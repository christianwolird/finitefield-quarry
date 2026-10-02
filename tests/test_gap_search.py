"""Checks for the GAP search program's command-line interpretation.

These tests do not run the expensive finite-field search. They establish that
the documented default bound and an explicit replacement reach the search
functions as the intended integers.
"""

import unittest

from scripts.gap_search import DEFAULT_ORDER_BOUND, parse_args


class GapSearchCliTests(unittest.TestCase):
    """Check the two supported ways to choose the exclusive order bound."""

    def test_default_order_bound_is_200_000(self):
        # An empty argument list models invoking the script with no options.
        args = parse_args([])

        self.assertEqual(DEFAULT_ORDER_BOUND, 200_000)
        self.assertEqual(args.order_bound, 200_000)

    def test_order_bound_can_be_overridden(self):
        # Command-line arguments arrive as text; argparse must convert the
        # supplied bound to the integer used in comparisons and prime ranges.
        args = parse_args(["400000"])

        self.assertEqual(args.order_bound, 400_000)


# Allow this file to run directly as well as through unittest discovery.
if __name__ == "__main__":
    unittest.main()
