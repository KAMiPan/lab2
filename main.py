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


class Manager(Base):
    __tablename__ = 'manager'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))

    def __repr__(self):
        return 'Manager[id='+str(self.id)+',name='+self.name+']'


class Owner(Base):
    __tablename__ = 'owner'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))
    address = Column(String(20))

    def __repr__(self):
        return 'Owner[id=' + str(self.id) + ',name=' + self.name + ',address='+self.address+']'


class Dispatcher(Base):
    __tablename__ = 'dispatcher'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))

    def __repr__(self):
        return 'Dispatcher[id='+str(self.id)+',name='+self.name+']'


class Worker(Base):
    __tablename__ = 'worker'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))
    is_idle = Column(Boolean, default=True)
    repair_types = Column(String(255))  # 能够维修的故障类型，形如1,5的字符串，与repair_type表的id对应

    def __repr__(self):
        return 'Worker[id=' + str(self.id) + ',name=' + self.name + \
               ',is_idle='+str(self.is_idle)+',repair_types'+self.repair_types+']'


class RepairType(Base):
    __tablename__ = 'repair_type'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))

    def __repr__(self):
        return 'RepairType[id='+str(self.id)+',name='+self.name+']'


class Repair(Base):
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
        return 'Repair[id='+str(self.id)+',dispatcher_id='+str(self.dispatcher_id)+',type_id='+str(self.type_id) + \
               ',status='+str(self.status)+',content='+self.content+',channel='+str(self.channel)+',ower_id=' + \
               str(self.owner_id)+',time='+self.time.strftime('%Y-%m-%d %H:%M:%S')+']'


class RepairDispatch(Base):
    __tablename__ = 'repair_dispatch'

    id = Column(Integer, primary_key=True, autoincrement=True)
    repair_id = Column(Integer, ForeignKey("repair.id"))
    worker_id = Column(Integer, ForeignKey("worker.id"))
    status = Column(Integer)  # 1-活动中，2-已关闭

    def __repr__(self):
        return 'RepairDispatch[id=' + str(self.id) + ',repair_id=' + str(self.repair_id) + \
               ',worker_id=' + str(self.worker_id) + ',status' + str(self.status) + ']'


class RepairRecord(Base):
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
               ',end_time='+self.end_time.strftime('%Y-%m-%d %H:%M:%S')+',procedure='+self.procedure+']'


class Feedback(Base):
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True, autoincrement=True)
    repair_id = Column(Integer, ForeignKey("repair.id"))
    response_speed = Column(Integer)
    service_attitude = Column(Integer)
    satisfaction_degree = Column(Integer)

    def __repr__(self):
        return 'Feedback[id=' + str(self.id) + ',repair_id=' + str(self.repair_id) + \
               ',response_speed=' + str(self.response_speed) + ',service_attitude=' + str(self.service_attitude) + \
               ',satisfaction_degree='+str(self.satisfaction_degree)+']'


class Complaint(Base):
    __tablename__ = 'complaint'

    id = Column(Integer, primary_key=True, autoincrement=True)
    repair_id = Column(Integer, ForeignKey("repair.id"))
    content = Column(String(255))
    status = Column(Integer)  # 0-已发起，1-沟通中，2-已关闭
    related_staff = Column(String(255))  # 形如d11,w5,w8的字符串，d表示dispatcher，w表示worker，数字是id
    result = Column(String(255))  # 与客户的沟通结果

    def __repr__(self):
        return 'Complaint[id=' + str(self.id) + ',repair_id=' + str(self.repair_id) + \
               ',content=' + self.content + ',status=' + str(self.status) + \
               ',related_staff='+self.related_staff+',result='+self.result + ']'


class Statement(Base):
    __tablename__ = 'statement'

    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(Integer, ForeignKey("complaint.id"))
    submitter = Column(String(20))  # 形如d11或w5的字符串，d表示dispatcher，w表示worker，数字对应id
    content = Column(String(255))

    def __repr__(self):
        return 'Statement[id=' + str(self.id) + ',complaint_id=' + str(self.complaint_id) + \
               ',submitter=' + self.submitter + ',content=' + self.content+']'


if __name__ == '__main__':
    Base.metadata.create_all(engine)  # 若未建表，在数据库中建表
    # 插入数据
    # repair = Repair(type_id=3, content='家里停电', channel=1, owner_id=1)
    # session.add(repair)
    # session.commit()

    # update数据
    # repair = session.query(Repair).filter_by(id=1).update({"status": 1})
    # session.commit()
