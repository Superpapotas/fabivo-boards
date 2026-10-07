"""Synthetic smoke checks. These labels are not research dataset examples."""
import unittest
import metrics
from consensus import pick

LABEL = 'box 1000 1000\nv 0 0 20 1000\nh 0 0 1000 20\n'

class MetricsSmoke(unittest.TestCase):
    def test_identical(self):
        self.assertEqual(metrics.score(LABEL, LABEL)['f1'], 1.0)
        self.assertEqual(metrics.struct_score(LABEL, LABEL)['f1'], 1.0)
    def test_empty(self):
        self.assertFalse(metrics.score('', LABEL)['valid'])
        self.assertEqual(metrics.struct_score('', LABEL)['f1'], 0.0)
    def test_medoid_tie_and_invalid(self):
        self.assertEqual(pick(['', LABEL, LABEL]), 1)
        self.assertIsNone(pick(['', '']))

if __name__ == '__main__':
    unittest.main()
