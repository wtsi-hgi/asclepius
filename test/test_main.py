import main
import core.irods_wrapper as irods_wrapper

# main.py --config [path] --include_collections [root_collection]


class TestAsclepius(unittest.TestCase):
    '''Suite of tests on Asclepius
    '''

    def setUp(self):
       
        root_collection = "/humgen/asclepius_testing"
        self.session = irods_wrapper.create_session()

        filepath = "/humgen/asclepius_testing/foo"
         obj = self.executor.session.data_objects.get(filepath)
        for avu in obj.metadata.items():
            obj.metadata.remove(avu)
        obj.metadata.add('foo', 'bar')   


        filepath = "/humgen/asclepius_testing/test/bar"
         obj = self.executor.session.data_objects.get(filepath)
        for avu in obj.metadata.items():
            obj.metadata.remove(avu)
        obj.metadata.add('pi', 'ch12_previous') 

    def test_simple(self):
        root_collection = "/humgen/asclepius_testing"
        config = "config_valid.yaml"
        main.run(root_collection, config)


  
if __name__ == '__main__':
    unittest.main()



