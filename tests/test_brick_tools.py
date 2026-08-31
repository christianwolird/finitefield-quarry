import unittest

from ffquarry.brick_tools import (
    four_dimensional_full_search,
    four_dimensional_quick_search,
    is_perfect_brick,
    smart_search,
    subset_sums,
    three_dimensional_full_search,
    three_dimensional_quick_search,
)
from ffquarry.power_field import PowerField
from ffquarry.prime_field import PrimeField


class BrickToolsTests(unittest.TestCase):
    def test_subset_sums_include_every_choice(self):
        field = PrimeField(101)

        self.assertEqual(
            subset_sums(field, (1, 4, 16)),
            [0, 1, 4, 5, 16, 17, 20, 21],
        )

    def test_repeated_subset_sum_is_not_a_brick(self):
        self.assertFalse(is_perfect_brick(PrimeField(101), (1, 1, 4)))

    def test_three_dimensional_quick_search_uses_pythagorean_seed(self):
        field = PrimeField(73)
        result = three_dimensional_quick_search(field)

        self.assertEqual(result[:2], (9, 16))
        self.assertTrue(is_perfect_brick(field, result))

    def test_three_dimensional_full_search_is_normalized(self):
        field = PrimeField(41)
        result = three_dimensional_full_search(field)

        self.assertEqual(result[0], 1)
        self.assertTrue(is_perfect_brick(field, result))

    def test_four_dimensional_quick_search_uses_euler_brick_seed(self):
        field = PrimeField(131)
        result = four_dimensional_quick_search(field)

        self.assertIsNotNone(result)
        self.assertTrue(is_perfect_brick(field, result))

    def test_four_dimensional_full_search_is_normalized(self):
        field = PrimeField(101)
        result = four_dimensional_full_search(field)

        self.assertEqual(result[0], 1)
        self.assertTrue(is_perfect_brick(field, result))

    def test_smart_search_supports_power_fields(self):
        field = PowerField(49)
        result = smart_search(field, dimensions=3)

        self.assertIsNotNone(result)
        self.assertTrue(is_perfect_brick(field, result))

    def test_search_rejects_unsupported_dimensions(self):
        with self.assertRaisesRegex(ValueError, "dimensions must be 3 or 4"):
            smart_search(PrimeField(101), dimensions=5)


if __name__ == "__main__":
    unittest.main()
