import unittest
import main
import core.irods_wrapper as irods_wrapper

# main.py --config [path] --include_collections [root_collection]


class TestAsclepius(unittest.TestCase):
    '''Suite of tests on Asclepius
    '''


    def setUpFile(self, filepath, metadata):
        obj = self.session.data_objects.get(filepath)
        for avu in obj.metadata.items():
            obj.metadata.remove(avu)
        obj.metadata.add(*metadata)  

    def setUp(self):
       
        self.session = irods_wrapper.create_session()
        filepath = "/humgen/asclepius_testing/foo"
        metadata = ('foo', 'bar')  
        self.setUpFile(filepath, metadata)

        filepath = "/humgen/asclepius_testing/test/bar"
        metadata = ('pi', 'ch12_previous') 
        self.setUpFile(filepath, metadata)

    def tearDown(self):
       
        self.session = irods_wrapper.create_session()
        filepath = "/humgen/asclepius_testing/foo"
        metadata = ('foo', 'bar')  
        self.setUpFile(filepath, metadata)

        filepath = "/humgen/asclepius_testing/test/bar"
        metadata = ('pi', 'ch12_previous') 
        self.setUpFile(filepath, metadata)


    def test_simple(self):
        root_collection = "/humgen/asclepius_testing"
        config = "/lustre/scratch115/teams/hgi/lustre-usage/tools/pyrodstest/asclepius/test/test_config_1.yaml"
        main.run(root_collection, config)

        filepath = "/humgen/asclepius_testing/foo"
        # expected_metadata = [(pi, ch12, None), (group, hgi, None), (foo, bar, None)]
        changed_metadata = irods_wrapper.get_metadata(self.session, filepath) # <iRODSMeta 13186 key2 value5 units2>
        print(f"Final_avus: {changed_metadata.items()}")
        self.assertEqual(changed_metadata['foo'].value, "bar")
        self.assertEqual(changed_metadata['foo'].units, None)
        self.assertEqual(changed_metadata['pi'].value, "ch12")
        self.assertEqual(changed_metadata['group'].value, "hgi")

        filepath = "/humgen/asclepius_testing/test/bar"
        # expected_metadata = [(pi, ch12_previous, None), (group, hgi, None), (foo, bar, None)]
        changed_metadata = irods_wrapper.get_metadata(self.session, filepath) # <iRODSMeta 13186 key2 value5 units2>
        print(f"Final_avus: {changed_metadata.items()}")
        self.assertEqual(changed_metadata['pi'].value, "ch12_previous")
        self.assertEqual(changed_metadata['group'].value, "hgi")

    def test_simple_overwrite(self):
        root_collection = "/humgen/asclepius_testing"
        config = "/lustre/scratch115/teams/hgi/lustre-usage/tools/pyrodstest/asclepius/test/test_config_1.yaml"
        main.run(root_collection, config, overwrite = True)

    
        filepath = "/humgen/asclepius_testing/test/bar"
        # expected_metadata = [(pi, ch12, None), (group, hgi, None), (foo, bar, None)]
        changed_metadata = irods_wrapper.get_metadata(self.session, filepath) # <iRODSMeta 13186 key2 value5 units2>
        print(f"Final_avus: {changed_metadata.items()}")
        self.assertEqual(changed_metadata['pi'].value, "ch12")
        self.assertEqual(changed_metadata['group'].value, "hgi")




  
if __name__ == '__main__':
    unittest.main()



