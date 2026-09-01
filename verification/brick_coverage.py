#!/usr/bin/env python3
"""Check that the brick results cover every odd field below their bounds."""

import argparse

from sympy import primerange

try:
    from ._result_tools import (
        PROJECT_ROOT,
        prime_power_exponents,
        print_errors,
        read_power_records,
        read_prime_records,
    )
except ImportError:
    from _result_tools import (
        PROJECT_ROOT,
        prime_power_exponents,
        print_errors,
        read_power_records,
        read_prime_records,
    )


DEFAULT_ORDER_BOUNDS = {3: 1_000, 4: 700_000}
RESULTS_DIR = PROJECT_ROOT / "results" / "bricks"
DIMENSION_DIRS = {3: RESULTS_DIR / "three_dim", 4: RESULTS_DIR / "four_dim"}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Check coverage of the 3D and 4D brick result files."
    )
    parser.add_argument(
        "--dimension",
        type=int,
        choices=(3, 4),
        help="check one dimension instead of both",
    )
    parser.add_argument(
        "--order-bound",
        type=int,
        help="override the bound (requires --dimension)",
    )
    args = parser.parse_args(argv)
    if args.order_bound is not None and args.dimension is None:
        parser.error("--order-bound requires --dimension")
    return args


def check_dimension(dimensions, order_bound):
    results_dir = DIMENSION_DIRS[dimensions]
    prime_records, prime_errors = read_prime_records(
        results_dir / "prime_field_solutions.txt"
    )
    power_records, power_errors = read_power_records(
        results_dir / "power_field_solutions.txt"
    )
    errors = prime_errors + power_errors
    missing = []
    prime_count = 0
    power_count = 0
    implicit_power_count = 0

    if order_bound <= 3:
        errors.append(f"{dimensions}D order bound must be greater than 3")
        return errors, prime_count, power_count, implicit_power_count

    for p in primerange(3, order_bound):
        p = int(p)
        prime_count += 1
        prime_record = prime_records.get(p)
        if prime_record is None:
            missing.append(str(p))

        for exponent in prime_power_exponents(p, order_bound):
            power_count += 1
            if prime_record is not None and prime_record.body != "None":
                implicit_power_count += 1
            elif (p, exponent) not in power_records:
                missing.append(f"{p}^{exponent}")

    if missing:
        errors.append(
            f"{dimensions}D results are missing coverage for "
            + ", ".join(missing[:20])
            + (f" (and {len(missing) - 20} more)" if len(missing) > 20 else "")
        )

    return errors, prime_count, power_count, implicit_power_count


def main(argv=None):
    args = parse_args(argv)
    dimensions_to_check = (args.dimension,) if args.dimension else (3, 4)
    errors = []
    summaries = []

    for dimensions in dimensions_to_check:
        order_bound = args.order_bound or DEFAULT_ORDER_BOUNDS[dimensions]
        dimension_errors, prime_count, power_count, implicit_count = check_dimension(
            dimensions, order_bound
        )
        errors.extend(dimension_errors)
        summaries.append(
            f"{dimensions}D below {order_bound}: {prime_count} primes and "
            f"{power_count} extensions ({implicit_count} by prime-field inclusion)"
        )

    if errors:
        print_errors(errors)
        return 1

    print("Brick result coverage is complete (" + "; ".join(summaries) + ").")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
