import unittest
from executor import Executor
from planner.object_class import Plan, AVU
import core.irods_wrapper as irods_wrapper


class TestExecutorMethods(unittest.TestCase):
    '''Suite of tests on executor operations
    '''

    def setUp(self):
        
        irods_session = irods_wrapper.create_session()
        self.executor = Executor(irods_session, 1 )
        filepath = "/Sanger1/home/mercury/test"
        obj = self.executor.session.data_objects.get(filepath)
        for avu in obj.metadata.items():
            obj.metadata.remove(avu)
        obj.metadata.add('foo', 'bar')

        
    def tearDown(self):
       
        filepath = "/Sanger1/home/mercury/test"
        obj = self.executor.session.data_objects.get(filepath)
        for avu in obj.metadata.items():
            obj.metadata.remove(avu)
        obj.metadata.add('foo', 'bar')
    

    def test_no_overlap_case(self):
        filepath = "/Sanger1/home/mercury/test"
        existing_avus= self.executor.get_metadata(filepath).items()
        print(f"existing_avus: {existing_avus}")
        planned_avus=  [("Key1", "Value1"), ("Key2", "Value2", "Unit2"), ("Key3", "Value3")]
        planned_metadata = []
        for avu in planned_avus:
            planned_metadata.append(AVU(*avu))


        plan = Plan(filepath, planned_metadata)
        self.executor.execute_plan(plan)

        # expected_avus =  [("foo", "bar", None), ("Key1", "Value1"), ("Key2", "Value2", "Unit2"), ("Key3", "Value3")]

        changed_metadata = self.executor.get_metadata(filepath) # <iRODSMeta 13186 key2 value5 units2>
        print(f"Final_avus: {changed_metadata.items()}")
        self.assertEqual(changed_metadata['foo'].value, "bar")
        self.assertEqual(changed_metadata['foo'].units, None)
        self.assertEqual(changed_metadata['Key1'].value, "Value1")
        self.assertEqual(changed_metadata['Key2'].value, "Value2")
        self.assertEqual(changed_metadata['Key2'].units, "Unit2")
        self.assertEqual(changed_metadata['Key3'].value, "Value3")
       
    def test_single_overlap(self):
        filepath = "/Sanger1/home/mercury/test"
        existing_avus= self.executor.get_metadata(filepath).items()
        print(f"existing_avus: {existing_avus}")

        planned_avus=  [("Key1", "Value1"), ("Key2", "Value2", "Unit2"), ("foo", "changed_bar", "new_unit")]
        planned_metadata = []
        for avu in planned_avus:
            planned_metadata.append(AVU(*avu))


        plan = Plan(filepath, planned_metadata)
        self.executor.execute_plan(plan, True)
        
        # expected_avus =  [("Key1", "Value1"), ("Key2", "Value2", "Unit2"), ("foo", "changed_bar", "new_unit")]

        changed_metadata = self.executor.get_metadata(filepath) # <iRODSMeta 13186 key2 value5 units2>
        print(f"Final_avus: {changed_metadata.items()}")
        self.assertEqual(changed_metadata['foo'].value, "changed_bar")
        self.assertEqual(changed_metadata['foo'].units, "new_unit")
        self.assertEqual(changed_metadata['Key1'].value, "Value1")
        self.assertEqual(changed_metadata['Key2'].value, "Value2")
        self.assertEqual(changed_metadata['Key2'].units, "Unit2")
  
       
    def test_no_overwrite(self):

        filepath = "/Sanger1/home/mercury/test"
        # existing_avus=[("foo", "bar", None)]
        existing_avus= self.executor.get_metadata(filepath).items()
        print(f"existing_avus: {existing_avus}")
        planned_avus=  [("foo", "changed_bar", "new_unit")]
        planned_metadata = []
        for avu in planned_avus:
            planned_metadata.append(AVU(*avu))


        plan = Plan(filepath, planned_metadata)
        self.executor.execute_plan(plan)

        # expected_avus =  [("foo", "bar", None)]


        changed_metadata = self.executor.get_metadata(filepath) # <iRODSMeta 13186 key2 value5 units2>
        print(f"Final_avus: {changed_metadata.items()}")
        self.assertEqual(changed_metadata['foo'].value, "bar")
        self.assertEqual(changed_metadata['foo'].units, None)      

      # def test_two_value_overwrite(self):

    #     filepath = "/Sanger1/home/mercury/test"
    #     existing_avus=[("foo", "bar", None), ("foo", "bar", "foo_unit")]
    #     planned_avus=  [("foo", "changed_bar")]
    #     planned_metadata = []
    #     for avu in planned_avus:
    #         planned_metadata.append(AVU(*avu))


    #     plan = Plan(filepath, planned_metadata)
    #     self.executor.execute_plan(plan)

    #     # expected_avus =  [("foo", "changed_bar")]

    #     changed_metadata = self.executor.get_metadata(filepath) # <iRODSMeta 13186 key2 value5 units2>
    #     self.assertEqual(changed_metadata['foo'].value, "changed_bar")
    #     self.assertEqual(changed_metadata['foo'].units, None)
if __name__ == '__main__':
    unittest.main()