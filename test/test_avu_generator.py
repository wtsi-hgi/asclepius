import unittest
from planner import planner
from planner.object_class import Plan, AVU

class TestAVUGenerator(unittest.TestCase):
    def test_static_avus(self):
        catalogue = {'objects': ['/test/a.txt', '/test/d.cram',
            '/test/e.cram', '/test2/abc.cram'],
            'collections': ['/test', '/test2']}

        output = [
            Plan('/test/a.txt',
                [AVU('pi', 'ch12', None), AVU('group', 'hgi', None)]),
            Plan('/test/d.cram',
                [AVU('pi', 'ch12', None), AVU('group', 'hgi', None),
                AVU('cost', 100000, 'gbp')]),
            Plan('/test/e.cram',
                [AVU('pi', 'ch12', None), AVU('group', 'hgi', None),
                AVU('cost', 100000, 'gbp')]),
            Plan('/test2/abc.cram',
                [AVU('pi', 'ch12', None), AVU('group', 'hgi', None),
                AVU('cost', 100000, 'gbp')])
        ]

        self.assertEqual(
            list(planner.generate_avus(catalogue, "test/test_config_1.yaml")),
            output)

        output_collections = output + [Plan('/test',
                [AVU('pi', 'ch12', None), AVU('group', 'hgi', None)]),
            Plan('/test2',
                [AVU('pi', 'ch12', None), AVU('group', 'hgi', None)])]

        self.assertEqual(
            list(planner.generate_avus(catalogue, "test/test_config_1.yaml",
                ignore_collections=False)), output_collections)


if __name__ == "__main__":
    unittest.main()
