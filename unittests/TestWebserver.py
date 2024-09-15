""" Unittest file for correct computations """

import unittest
from deepdiff import DeepDiff
from demo_ingestor import DemoIngestor

class TestWebserver(unittest.TestCase):
    """ Class that includes all tests """
    def setUp(self):
        """ Make sure we read csv """
        self.ingestor = DemoIngestor("./my_csv.csv")

    def test_unittest_global_mean(self):
        """ Test global mean - expect to pass """
        res = self.ingestor.get_global_mean(
            "Percent of adults who engage in no leisure-time physical activity")
        self.assertEqual(res, 6.7)

    def test_unittest_state_mean(self):
        """ Test state mean - expect to pass """
        res = self.ingestor.get_state_mean(
            "Percent of adults who engage in no leisure-time physical activity", "Wisconsin")
        self.assertEqual(res, 6.5)

    def test_unittest_states_mean(self):
        """ Test states mean - expect to pass """
        res = self.ingestor.get_states_mean(
            "Percent of adults who engage in no leisure-time physical activity")
        d = DeepDiff(res, {'Hawaii': 5.5, 'Idaho': 6.0, 'Wisconsin': 6.5,
                        'Alaska': 7.0, 'Nebraska': 8.0, 'Virgin Islands': 9.0}, math_epsilon=0.01)
        self.assertTrue(not d, str(d))

    def test_unittest_get_best5(self):
        """ Test best5 - expect to pass """
        res = self.ingestor.get_best5(
            "Percent of adults who engage in no leisure-time physical activity")
        d = DeepDiff(res, {'Hawaii': 5.5, 'Idaho': 6.0, 'Wisconsin': 6.5,
                           'Alaska': 7.0, 'Nebraska': 8.0}, math_epsilon=0.01)
        self.assertTrue(not d, str(d))

    def test_unittest_get_worst5(self):
        """ Test worst5 - expect to pass """
        res = self.ingestor.get_worst5(
            "Percent of adults who engage in no leisure-time physical activity")
        d = DeepDiff(res, {'Idaho': 6.0, 'Wisconsin': 6.5, 'Alaska': 7.0,
                           'Nebraska': 8.0, 'Virgin Islands': 9.0}, math_epsilon=0.01)
        self.assertTrue(not d, str(d))

    def test_unittest_get_diff_from_mean(self):
        """ Test diff from mean - expect to pass """
        res = self.ingestor.get_diff_from_mean(
            "Percent of adults who engage in no leisure-time physical activity")
        d = DeepDiff(res, {'Wisconsin': 0.2, 'Alaska': -0.3, 'Nebraska': -1.3,
                           'Idaho': 0.7, 'Virgin Islands': -2.3, 'Hawaii': 1.2}, math_epsilon=0.01)
        self.assertTrue(not d, str(d))

    def test_unittest_probably_fail(self):
        """ Test diff from mean without epsilon - expect to fail """
        res = self.ingestor.get_diff_from_mean(
            "Percent of adults who engage in no leisure-time physical activity")
        d = DeepDiff(res, {'Wisconsin': 0.2, 'Alaska': -0.3,
                           'Nebraska': -1.3, 'Idaho': 0.7, 'Virgin Islands': -2.3, 'Hawaii': 1.2})
        self.assertTrue(not d, str(d))

    def test_unittest_get_state_diff_from_mean(self):
        """ Test state diff from mean - expect to pass """
        res = self.ingestor.get_state_diff_from_mean(
            "Percent of adults who engage in no leisure-time physical activity", "Hawaii")
        d = DeepDiff(res, {'Hawaii': 1.2}, math_epsilon=0.01)
        self.assertTrue(not d, str(d))

    def test_unittest_get_mean_by_category(self):
        """ Test mean by category - expect to pass """
        res = self.ingestor.get_mean_by_category(
            "Percent of adults who engage in no leisure-time physical activity")
        ref = {"('Wisconsin', 'Age (years)', '55 - 64')": 5.0,
               "('Wisconsin', 'Age (years)', '18 - 24')": 8.0,
               "('Alaska', 'Age (years)', '55 - 64')": 7.0,
               "('Nebraska', 'Age (years)', '55 - 64')": 8.0,
               "('Idaho', 'Age (years)', '55 - 64')": 6.0,
               "('Virgin Islands', 'Age (years)', '55 - 64')": 9.0,
               "('Hawaii', 'Age (years)', '55 - 64')": 5.5}
        d = DeepDiff(res, ref, math_epsilon=0.01)
        self.assertTrue(not d, str(d))

    def test_unittest_get_state_mean_by_category(self):
        """ Test state mean by category - expect to pass """
        res = self.ingestor.get_state_mean_by_category(
            "Percent of adults who engage in no leisure-time physical activity", "Wisconsin")
        d = DeepDiff(res, {'Wisconsin': {"('Age (years)', '55 - 64')": 5.0,
                                         "('Age (years)', '18 - 24')": 8.0}}, math_epsilon=0.01)
        self.assertTrue(not d, str(d))
