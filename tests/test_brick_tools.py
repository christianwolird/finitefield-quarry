"""Focused examples supporting the brick-search implementation.

The tests check the subset-sum construction, both required brick properties,
the quick-search seeds, normalization of exhaustive searches, extension-field
support, and rejection of dimensions outside the project's scope.
"""

import unittest

from ffquarry.brick_tools import (
    full_search_3d,
    full_search_4d,
    is_strong_perfect_brick,
    quick_search_3d,
    quick_search_4d,
    smart_search,
    subset_sums,
)
from ffquarry.extension_field import ExtensionField
from ffquarry.prime_field import PrimeField


class BrickToolsTests(unittest.TestCase):
    """Check representative mathematical invariants of the brick algorithms."""

    def test_subset_sums_include_every_choice(self):
        field = PrimeField(101)

        # The expected order reflects the iterative construction: subsets
        # without the newest side, followed by the same subsets with it.
        self.assertEqual(
            subset_sums(field, (1, 4, 16)),
            [0, 1, 4, 5, 16, 17, 20, 21],
        )

    def test_repeated_subset_sum_is_not_a_brick(self):
        # Equal side squares immediately repeat singleton subset sums, violating
        # strength even if every displayed value happened to be a square.
        self.assertFalse(is_strong_perfect_brick(PrimeField(101), (1, 1, 4)))

    def test_quick_search_3d_uses_pythagorean_seed(self):
        field = PrimeField(73)
        result = quick_search_3d(field)

        # 9 and 16 are 3^2 and 4^2; their sum 25 is also a square.
        self.assertEqual(result[:2], (9, 16))
        self.assertTrue(is_strong_perfect_brick(field, result))

    def test_full_search_3d_is_normalized(self):
        field = PrimeField(41)
        result = full_search_3d(field)

        # The exhaustive search removes scalar symmetry by fixing its first
        # nonzero side-square to 1.
        self.assertEqual(result[0], 1)
        self.assertTrue(is_strong_perfect_brick(field, result))

    def test_quick_search_4d_uses_euler_brick_seed(self):
        field = PrimeField(131)
        result = quick_search_4d(field)

        # A non-None return shows at least one reduced integer seed extended;
        # the second assertion independently checks the resulting witness.
        self.assertIsNotNone(result)
        self.assertTrue(is_strong_perfect_brick(field, result))

    def test_full_search_4d_is_normalized(self):
        field = PrimeField(101)
        result = full_search_4d(field)

        # Four dimensions use the same valid scalar normalization as 3D.
        self.assertEqual(result[0], 1)
        self.assertTrue(is_strong_perfect_brick(field, result))

    def test_smart_search_supports_extension_fields(self):
        # F_49 exercises the polynomial-field wrapper rather than integer
        # arithmetic modulo a prime.
        field = ExtensionField(49)
        result = smart_search(field, dimension=3)

        self.assertIsNotNone(result)
        self.assertTrue(is_strong_perfect_brick(field, result))

    def test_search_rejects_unsupported_dimensions(self):
        # The public dispatcher must fail explicitly instead of silently using
        # a 3D or 4D routine for an unimplemented dimension.
        with self.assertRaisesRegex(ValueError, "dimension must be 3 or 4"):
            smart_search(PrimeField(101), dimension=5)


# Allow direct execution in addition to unittest discovery.
if __name__ == "__main__":
    unittest.main()
