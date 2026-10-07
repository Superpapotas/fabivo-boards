import unittest
from m10_step_schedules import turbo_sigmas

class TurboSchedules(unittest.TestCase):
    def test_existing_six_step_control(self):
        self.assertEqual(turbo_sigmas(6),[1.,.9375,.875,.75,.5,.25])
    def test_more_steps_preserve_low_noise_nodes(self):
        for n in (10,15):
            s=turbo_sigmas(n)
            self.assertEqual(len(s),n)
            self.assertEqual(s[-4:],[.875,.75,.5,.25])
            self.assertEqual(s[0],1.)
            self.assertTrue(all(a>b for a,b in zip(s,s[1:])))
            self.assertTrue(all(.875<x<=1. for x in s[:-4]))
    def test_invalid_counts(self):
        for n in (0,4,True,10.,'15'):
            with self.assertRaises(ValueError):turbo_sigmas(n)

if __name__=='__main__':unittest.main()
