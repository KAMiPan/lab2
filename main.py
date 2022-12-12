from sqlalchemy import create_engine, Column, Integer, Boolean, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine('sqlite:///lab2.db', encoding='utf8', echo=True)
# 创建缓存对象
Session = sessionmaker(bind=engine)
session = Session()
# 声明基类
Base = declarative_base()


class Manager(Base):  # 物业经理
    __tablename__ = 'manager'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))

    def __repr__(self):
        return 'Manager[id=' + str(self.id) + ',name=' + self.name + ']'


class Owner(Base):  # 业主
    __tablename__ = 'owner'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))
    address = Column(String(20))

    def __repr__(self):
        return 'Owner[id=' + str(self.id) + ',name=' + self.name + ',address=' + self.address + ']'

    def submit_repair(self, type_id, content, channel):  # 业主提交报修
        repair = Repair(type_id=type_id, content=content, channel=channel, owner_id=self.id)
        session.add(repair)
        session.flush()
        session.commit()
        return repair.id  # 返回新增repair的主键


def get_initiated_repairs():  # 查看所有状态为1-已发起待录入的repair
    repairs = session.query(Repair).filter_by(status=1).all()
    return repairs


class Dispatcher(Base):  # 调度员
    __tablename__ = 'dispatcher'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))

    def __repr__(self):
        return 'Dispatcher[id=' + str(self.id) + ',name=' + self.name + ']'

    def input_repair(self, repair_id):  # 调度员录入报修
        repairs = session.query(Repair).filter_by(id=repair_id).all()
        if len(repairs) != 1:  # 如果对应报修不存在时
            return False
        repair = repairs[0]
        if repair.status != 1:  # 只能录入状态为1-已发起的报修
            return False
        repair.status = 2  # 报修状态修改为2-已录入
        repair.dispatcher_id = self.id
        session.commit()
        return True  # 返回是否成功录入

    def dispatch_repair(self, repair_id):  # 调度员调度报修
        repairs = session.query(Repair).filter_by(id=repair_id).all()
        if len(repairs) != 1:  # 如果对应报修不存在时
            return False
        repair = repairs[0]
        if repair.status != 2:  # 只能调度状态为2-已录入的报修
            return False
        if repair.dispatcher_id != self.id:  # 只能调度自己录入的报修
            return False
        idle_workers = session.query(Worker).filter_by(is_idle=True)  # www找到所有空闲工人
        for worker in idle_workers:  # 遍历找到能处理该故障类型的工人
            if worker.can_repair(repair.type_id):
                dispatch = RepairDispatch(repair_id=repair_id, worker_id=worker.id)  # 创建维修调度
                session.add(dispatch)
                session.flush()
                worker.is_idle = False  # 工人是否空闲改为否
                repair.status = 3  # 报修状态修改为3-已调度
                session.commit()
                return dispatch.id
        return False  # 没有合适的空闲工人的情况

    def get_self_inputted_repairs(self):  # 调度员查看所有自己录入的、状态为2-已录入待调度的repair
        repairs = session.query(Repair).filter_by(status=2, dispatcher_id=self.id)
        return repairs


class Worker(Base):  # 维修工人
    __tablename__ = 'worker'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))
    is_idle = Column(Boolean, default=True)
    repair_types = Column(String(255))  # 能够维修的故障类型，形如1,5的字符串，与repair_type表的id对应

    def __repr__(self):
        return 'Worker[id=' + str(self.id) + ',name=' + self.name + \
               ',is_idle=' + str(self.is_idle) + ',repair_types' + self.repair_types + ']'

    def can_repair(self, type_id):
        types = self.repair_types.split(',')
        return type_id in types


class RepairType(Base):  # 故障类型
    __tablename__ = 'repair_type'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))

    def __repr__(self):
        return 'RepairType[id=' + str(self.id) + ',name=' + self.name + ']'


class Repair(Base):  # 报修，对应多个维修调度
    __tablename__ = 'repair'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dispatcher_id = Column(Integer, ForeignKey("dispatcher.id"), nullable=True)  # 状态为已发起时，此外键可以为空
    type_id = Column(Integer, ForeignKey("repair_type.id"))
    status = Column(Integer, default=1)  # 1-已发起，2-已录入，3-已调度，4-已维修，5-已评价
    content = Column(String(255))
    channel = Column(Integer)  # 1-电话报修 2-微信报修
    owner_id = Column(Integer, ForeignKey("owner.id"))
    time = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return 'Repair[id=' + str(self.id) + ',dispatcher_id=' + str(self.dispatcher_id) + ',type_id=' + str(
            self.type_id) + ',status=' + str(self.status) + ',content=' + self.content + ',channel=' + str(
            self.channel) + ',owner_id=' + str(self.owner_id) + ',time=' + self.time.strftime('%Y-%m-%d %H:%M:%S') + ']'

    def get_active_dispatch(self):
        active_dispatches = session.query(RepairDispatch).filter_by(repair_id=self.id, status=1).all()
        if len(active_dispatches) != 1:  # 不存在活动中的调度
            return False
        return active_dispatches[0].id

    def get_related_staff(self):  # 获取报修相关人员
        related_staff = []
        if self.dispatcher_id is not None:  # 添加负责该报修的调度员
            related_staff.append('d' + str(self.dispatcher_id))
        dispatches = session.query(RepairDispatch).filter_by(repair_id=self.id).all()
        for dispatch in dispatches:  # 添加报修所有维修调度的工人
            related_staff.append('w' + str(dispatch.worker_id))
        return related_staff


class RepairDispatch(Base):  # 维修调度，对应多个维修记录
    __tablename__ = 'repair_dispatch'

    id = Column(Integer, primary_key=True, autoincrement=True)
    repair_id = Column(Integer, ForeignKey("repair.id"))
    worker_id = Column(Integer, ForeignKey("worker.id"))
    status = Column(Integer, default=1)  # 1-活动中，2-已关闭

    def __repr__(self):
        return 'RepairDispatch[id=' + str(self.id) + ',repair_id=' + str(self.repair_id) + \
               ',worker_id=' + str(self.worker_id) + ',status' + str(self.status) + ']'


class RepairRecord(Base):  # 维修记录
    __tablename__ = 'repair_record'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dispatch_id = Column(Integer, ForeignKey("repair_dispatch.id"))
    type = Column(Integer)  # 1-无法维修，2-待后续维修，3-完成维修
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    procedure = Column(String(255))

    def __repr__(self):
        return 'RepairRecord[id=' + str(self.id) + ',dispatch_id=' + str(self.dispatch_id) + \
               ',type=' + str(self.type) + ',start_time=' + self.start_time.strftime('%Y-%m-%d %H:%M:%S') + \
               ',end_time=' + self.end_time.strftime('%Y-%m-%d %H:%M:%S') + ',procedure=' + self.procedure + ']'


class Feedback(Base):  # 用户对报修的评价
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True, autoincrement=True)
    repair_id = Column(Integer, ForeignKey("repair.id"))
    response_speed = Column(Integer)
    service_attitude = Column(Integer)
    satisfaction_degree = Column(Integer)

    def __repr__(self):
        return 'Feedback[id=' + str(self.id) + ',repair_id=' + str(self.repair_id) + \
               ',response_speed=' + str(self.response_speed) + ',service_attitude=' + str(self.service_attitude) + \
               ',satisfaction_degree=' + str(self.satisfaction_degree) + ']'


class Complaint(Base):  # 用户对报修的投诉
    __tablename__ = 'complaint'

    id = Column(Integer, primary_key=True, autoincrement=True)
    repair_id = Column(Integer, ForeignKey("repair.id"))
    content = Column(String(255))
    status = Column(Integer, default=1)  # 1-已发起，2-沟通中，3-已关闭
    related_staff = Column(String(255))  # 形如d11,w5,w8的字符串，d表示dispatcher，w表示worker，数字是id
    result = Column(String(255))  # 与客户的沟通结果

    def __repr__(self):
        return 'Complaint[id=' + str(self.id) + ',repair_id=' + str(self.repair_id) + \
               ',content=' + self.content + ',status=' + str(self.status) + \
               ',related_staff=' + self.related_staff + ',result=' + self.result + ']'


class Statement(Base):  # 投诉相关人员提交的情况说明
    __tablename__ = 'statement'

    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(Integer, ForeignKey("complaint.id"))
    submitter = Column(String(20))  # 形如d11或w5的字符串，d表示dispatcher，w表示worker，数字对应id
    content = Column(String(255))

    def __repr__(self):
        return 'Statement[id=' + str(self.id) + ',complaint_id=' + str(self.complaint_id) + \
               ',submitter=' + self.submitter + ',content=' + self.content + ']'


if __name__ == '__main__':
    Base.metadata.create_all(engine)  # 若未建表，在数据库中建表
    # 插入数据
    # repair = Repair(type_id=3, content='家里停电', channel=1, owner_id=1)
    # session.add(repair)
    # session.commit()

    # 更新数据
    # repair = session.query(Repair).filter_by(id=1).update({"status": 1})
    # session.commit()
