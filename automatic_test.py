import unittest
from main import *


class RepairTestCase(unittest.TestCase):
    def setUp(self):
        self.dispatcher = Dispatcher(id=1, name='孙思')
        self.owner = Owner(id=1, name='李峰', address='4号702')

    # 测试默认执行顺序：按照方法名字典序排序，所以在方法名中stepX来约定测试执行顺序
    def test_step1_submit_repair(self):  # 步骤1：业主发起报修
        repair_id = self.owner.submit_repair(1, '厨房下水道堵塞', 1)
        self.assertIsNotNone(repair_id)
        repairs = session.query(Repair).filter_by(id=repair_id, type_id=1, status=1,
                                                  owner_id=self.owner.id, content='厨房下水道堵塞', channel=1).all()
        self.assertEqual(len(repairs), 1)

    def test_step2_input_repair(self):  # 步骤2：调度员录入已发起报修
        initiated_repairs = get_initiated_repairs()
        self.assertGreaterEqual(len(initiated_repairs), 1)
        repair = initiated_repairs[0]
        result = self.dispatcher.input_repair(repair.id)
        self.assertTrue(result)
        repairs = session.query(Repair).filter_by(id=repair.id, status=2, dispatcher_id=self.dispatcher.id).all()
        self.assertEqual(len(repairs), 1)

    def test_step3_dispatch_repair(self):  # 步骤3：调度员调度已录入报修
        inputted_repairs = self.dispatcher.get_self_inputted_repairs()
        self.assertGreaterEqual(len(inputted_repairs), 1)
        repair = inputted_repairs[0]
        worker_id = self.dispatcher.dispatch_repair(repair.id)
        self.assertNotEqual(worker_id, False)
        if worker_id == -1:  # 若无法分配任务
            idle_workers = session.query(Worker).filter_by(is_idle=True)  # 先验证确实没有空闲且能处理的工人
            for idle_worker in idle_workers:
                self.assertFalse(idle_worker.can_repair(repair.type_id))
            new_worker = Worker(name='于兵', repair_types=str(repair.type_id))  # 创建能处理故障的空闲工人
            session.add(new_worker)
            session.flush()
            session.commit()
            worker_id = self.dispatcher.dispatch_repair(repair.id)  # 再次分配报修
            self.assertEqual(worker_id, new_worker.id)
        # 验证分配是否有效
        self.assertGreaterEqual(worker_id, 1)
        repairs = session.query(Repair).filter_by(id=repair.id, status=3).all()  # 验证报修状态为3-已调度
        self.assertEqual(len(repairs), 1)
        workers = session.query(Worker).filter_by(id=worker_id).all()
        self.assertEqual(len(workers), 1)  # 验证分配到的工人存在
        worker = workers[0]
        self.assertTrue(worker.can_repair(repair.type_id))  # 验证分配给的工人是否能维修
        dispatches = session.query(RepairDispatch).filter_by(repair_id=repair.id, worker_id=worker_id, status=1).all()
        self.assertEqual(len(dispatches), 1)  # 验证是否新增维修调度


def repair_dispatch_suite():
    suite = unittest.TestSuite()
    # 运行前最好先把上一次运行的数据库修改还原
    suite.addTest(RepairTestCase('test_step1_submit_repair'))
    suite.addTest(RepairTestCase('test_step2_input_repair'))
    suite.addTest(RepairTestCase('test_step3_dispatch_repair'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(repair_dispatch_suite())
