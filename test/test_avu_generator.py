import unittest
from planner import planner

class TestAVUGenerator(unittest.TestCase):
    def test_static_avus(self):
        catalogue = {'objects': ['/test/a.txt', '/test/d.cram',
            '/test/e.cram', '/test2/abc.cram'],
            'collections': ['/test', '/test2']}

        output = [('/test/a.txt', ({'attribute': 'pi', 'value': 'ch12'},
                {'attribute': 'group', 'value': 'hgi'})),
            ('/test/d.cram', ({'attribute': 'pi', 'value': 'ch12'},
                {'attribute': 'group', 'value': 'hgi'}
                {'attribute': 'cost', 'value': 100000, 'unit': 'gdp'})),
            ('/test/e.cram', ({'attribute': 'pi', 'value': 'ch12'},
                {'attribute': 'group', 'value': 'hgi'}
                {'attribute': 'cost', 'value': 100000, 'unit': 'gdp'})),
            ('/test2/abc.cram', ({'attribute': 'pi', 'value': 'ch12'},
                {'attribute': 'group', 'value': 'hgi'}
                {'attribute': 'cost', 'value': 100000, 'unit': 'gdp'}))]

        self.assertEqual(
            list(planner.generateAVUs(catalogue, "test/test_config_1.yaml")),
            output)

        output_collections = output.extend(
            [('/test', ({'attribute': 'pi', 'value': 'ch12'},
                {'attribute': 'group', 'value': 'hgi'})),
            ('/test2', ({'attribute': 'pi', 'value': 'ch12'},
                {'attribute': 'group', 'value': 'hgi'}))])

        self.assertEqual(
            list(planner.generateAVUs(catalogue, "test/test_config_1.yaml",
                ignore_collections=False)), output_collections)


if __name__ == "__main__":
    unittest.main()
