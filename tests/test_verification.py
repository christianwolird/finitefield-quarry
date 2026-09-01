import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from verification import gap_coverage
from verification._result_tools import Record
from verification.brick_verify import verify_prime_record as verify_prime_brick
from verification.gap_verify import verify_prime_record as verify_prime_gap


class WitnessVerificationTests(unittest.TestCase):
    def record(self, body):
        return Record(Path("results.txt"), 1, "test", body)

    def test_valid_gap_is_accepted(self):
        valid, errors = verify_prime_gap(
            29,
            self.record("base=1, steps=(4, 24)"),
        )

        self.assertTrue(valid)
        self.assertEqual(errors, [])

    def test_gap_with_repeated_entries_is_rejected(self):
        valid, errors = verify_prime_gap(
            29,
            self.record("base=1, steps=(0, 24)"),
        )

        self.assertFalse(valid)
        self.assertTrue(any("not distinct" in error for error in errors))

    def test_valid_brick_is_accepted(self):
        valid, errors = verify_prime_brick(
            41,
            3,
            self.record("side_squares=(1, 4, 32)"),
        )

        self.assertTrue(valid)
        self.assertEqual(errors, [])

    def test_brick_with_repeated_subset_sums_is_rejected(self):
        valid, errors = verify_prime_brick(
            101,
            3,
            self.record("side_squares=(1, 1, 4)"),
        )

        self.assertFalse(valid)
        self.assertTrue(any("not distinct" in error for error in errors))


class CoverageTests(unittest.TestCase):
    def test_missing_prime_power_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            results_dir = Path(directory)
            (results_dir / "prime_field_solutions.txt").write_text(
                "3: None\n5: base=1, steps=(1, 2)\n7: None\n",
                encoding="utf-8",
            )
            # Keep the file nonempty while deliberately omitting 3^2, the only
            # extension field below 10 whose prime result does not cover it.
            (results_dir / "power_field_solutions.txt").write_text(
                "5^2: None\n",
                encoding="utf-8",
            )

            with patch.object(gap_coverage, "RESULTS_DIR", results_dir):
                errors, _, _, _ = gap_coverage.check_coverage(10)

        self.assertTrue(any("3^2" in error for error in errors))

    def test_prime_solution_covers_its_extensions(self):
        with tempfile.TemporaryDirectory() as directory:
            results_dir = Path(directory)
            (results_dir / "prime_field_solutions.txt").write_text(
                "3: base=1, steps=(1, 2)\n5: None\n7: None\n",
                encoding="utf-8",
            )
            (results_dir / "power_field_solutions.txt").write_text(
                "5^2: None\n",
                encoding="utf-8",
            )

            with patch.object(gap_coverage, "RESULTS_DIR", results_dir):
                errors, _, power_count, implicit_count = (
                    gap_coverage.check_coverage(10)
                )

        self.assertEqual(errors, [])
        self.assertEqual(power_count, 1)
        self.assertEqual(implicit_count, 1)


if __name__ == "__main__":
    unittest.main()
