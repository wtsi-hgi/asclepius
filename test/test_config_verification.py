import unittest
from planner import planner

class TestConfigVerification(unittest.TestCase):
    def test_valid_configuration(self):
        self.assertTrue(planner.verify_config("test/config_valid.yaml"))

    def test_invalid_regex(self):
        self.assertEqual(planner.verify_config("test/config_invalid_regex.yaml"),
            "Invalid pattern (regex): /[*.cram/")

    def test_invalid_avus(self):
        self.assertEqual(planner.verify_config("test/" \
                "config_missing_attribute.yaml"),
            "Invalid AVU (no attribute): *.cram")

        self.assertEqual(planner.verify_config("test/" \
                "config_missing_value.yaml"),
            "Invalid AVU (no value): *.cram")

    def test_invalid_infer(self):
        self.assertEqual(planner.verify_config("test/" \
                "config_missing_mapping.yaml"),
            "Invalid dynamic AVU (no mapping): *.cram")

        # TODO: Test for invalid infer methods once they are implemented

if __name__ == "__main__":
    unittest.main()
