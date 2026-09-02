import unittest

from scripts.gap_search import DEFAULT_ORDER_BOUND, parse_args


class GapSearchCliTests(unittest.TestCase):
    def test_default_order_bound_is_200_000(self):
        args = parse_args([])

        self.assertEqual(DEFAULT_ORDER_BOUND, 200_000)
        self.assertEqual(args.order_bound, 200_000)

    def test_order_bound_can_be_overridden(self):
        args = parse_args(["400000"])

        self.assertEqual(args.order_bound, 400_000)


if __name__ == "__main__":
    unittest.main()
