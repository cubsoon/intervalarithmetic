import unittest

from intervalarithmetic import *

class RoundingModeTestCase(unittest.TestCase):

    def test_function_init(self):
        for function in set_rounding, get_rounding:
            self.assertIsNotNone(function)
            self.assertTrue(callable(function))

    def test_constant_init(self):
        for constant in TO_ZERO, TO_NEAREST, TOWARD_PLUS_INF, TOWARD_MINUS_INF:
            self.assertIsNotNone(constant)

    def test_set_and_get_rounding(self):
        for mode in TO_ZERO, TO_NEAREST, TOWARD_PLUS_INF, TOWARD_MINUS_INF:
            self.assertTrue(set_rounding(mode))
            self.assertEqual(get_rounding(), mode, "first get_rounding call")
            self.assertEqual(get_rounding(), mode, "second get_rounding call")
        set_rounding(TO_NEAREST)

    def test_rounding_modes_1(self):
        a = 0.1
        b = 0.2
        set_rounding(TO_ZERO)
        tz = a * b
        set_rounding(TOWARD_PLUS_INF)
        pi = a * b
        set_rounding(TOWARD_MINUS_INF)
        mi = a * b
        set_rounding(TO_NEAREST)
        tn = a * b
        self.assertGreater(pi, mi)
        self.assertGreater(pi, tz)
        self.assertEqual(tz, mi)
        self.assertIn(tn, (tz, pi, mi))


class IntervalTestCase(unittest.TestCase):

    def test_repr_1(self):
        a = Interval(1000.1, strict=True)
        b = eval(a.__repr__())
        self.assertEqual(a.lv, b.lv)
        self.assertEqual(a.rv, b.rv)
        self.assertEqual(a.strict, b.strict)

if __name__ == '__main__':
    unittest.main(verbosity=2)
