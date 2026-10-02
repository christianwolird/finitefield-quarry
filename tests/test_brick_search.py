"""Checks for brick-search command-line choices and output destinations."""

import io
import unittest
from contextlib import redirect_stderr

from scripts.brick_search import (
    EXTENSION_RESULTS_PATHS,
    PRIME_RESULTS_PATHS,
    parse_args,
)


class BrickSearchCliTests(unittest.TestCase):
    """Ensure each run selects one dimension and its matching result files."""

    def test_dimension_is_required(self):
        # argparse reports invalid input on standard error and exits. Redirect
        # that expected message so it does not clutter the test output.
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_args(["100"])

    def test_exactly_one_dimension_is_selected(self):
        # A successful parse must expose the selected dimension as an integer.
        args = parse_args(["100", "--dimension", "4"])

        self.assertEqual(args.dimension, 4)

    def test_each_dimension_has_prime_and_extension_result_paths(self):
        # Separating dimensions prevents a 3D run from overwriting the much
        # larger 4D computation, while keeping prime and extension data apart.
        for dimension, directory_name in ((3, "three_dim"), (4, "four_dim")):
            self.assertEqual(
                PRIME_RESULTS_PATHS[dimension].parts[-2:],
                (directory_name, "prime_field_solutions.txt"),
            )
            self.assertEqual(
                EXTENSION_RESULTS_PATHS[dimension].parts[-2:],
                (directory_name, "extension_field_solutions.txt"),
            )


# Allow direct execution in addition to automatic test discovery.
if __name__ == "__main__":
    unittest.main()
