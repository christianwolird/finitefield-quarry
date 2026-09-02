import io
import unittest
from contextlib import redirect_stderr

from scripts.brick_search import (
    EXTENSION_RESULTS_PATHS,
    PRIME_RESULTS_PATHS,
    parse_args,
)


class BrickSearchCliTests(unittest.TestCase):
    def test_dimension_is_required(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_args(["100"])

    def test_exactly_one_dimension_is_selected(self):
        args = parse_args(["100", "--dimension", "4"])

        self.assertEqual(args.dimension, 4)

    def test_each_dimension_has_prime_and_extension_result_paths(self):
        for dimensions, directory_name in ((3, "three_dim"), (4, "four_dim")):
            self.assertEqual(
                PRIME_RESULTS_PATHS[dimensions].parts[-2:],
                (directory_name, "prime_field_solutions.txt"),
            )
            self.assertEqual(
                EXTENSION_RESULTS_PATHS[dimensions].parts[-2:],
                (directory_name, "extension_field_solutions.txt"),
            )


if __name__ == "__main__":
    unittest.main()
