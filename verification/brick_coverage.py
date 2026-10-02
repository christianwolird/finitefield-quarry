#!/usr/bin/env python3
"""Check that brick result files cover every odd field below their bounds.

This complements ``brick_verify`` which checks the validity of the solutions.
"""

import argparse

from sympy import primerange

# Support invocation both as ``python -m`` and by direct file path.
try:
    from ._result_tools import (
        PROJECT_ROOT,
        extension_exponents,
        print_errors,
        read_extension_records,
        read_prime_records,
    )
except ImportError:
    from _result_tools import (
        PROJECT_ROOT,
        extension_exponents,
        print_errors,
        read_extension_records,
        read_prime_records,
    )


# The 3D and 4D searches were run with different bounds.
DEFAULT_ORDER_BOUNDS = {3: 1_000, 4: 700_000}
RESULTS_DIR = PROJECT_ROOT / "results" / "bricks"
DIMENSION_DIRS = {3: RESULTS_DIR / "three_dim", 4: RESULTS_DIR / "four_dim"}


def parse_args(argv=None):
    """Read which dimension and exclusive order bound should be audited."""
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


def check_dimension(dimension, order_bound):
    """Return coverage errors and field counts for one brick dimension."""
    results_dir = DIMENSION_DIRS[dimension]
    prime_records, prime_errors = read_prime_records(
        results_dir / "prime_field_solutions.txt"
    )
    extension_records, extension_errors = read_extension_records(
        results_dir / "extension_field_solutions.txt"
    )
    errors = prime_errors + extension_errors
    missing = []
    prime_count = 0
    extension_count = 0
    implicit_extension_count = 0

    if order_bound <= 3:
        errors.append(f"{dimension}D order bound must be greater than 3")
        return errors, prime_count, extension_count, implicit_extension_count

    # Finite fields have exactly the prime-power orders p^a. This outer loop
    # accounts for a=1; extension_exponents supplies every a>=2 still below
    # the bound, so no odd field order in the range is skipped or duplicated.
    for p in primerange(3, order_bound):
        p = int(p)
        prime_count += 1
        prime_record = prime_records.get(p)
        # A prime record may be a witness or ``None``; either one documents
        # that the search processed F_p.
        if prime_record is None:
            missing.append(str(p))

        for exponent in extension_exponents(p, order_bound):
            extension_count += 1
            # Any witness in F_p remains valid in all F_(p^a), so those fields
            # are covered without separate result lines. If F_p was unresolved,
            # every extension must have an explicit result-file entry.
            if prime_record is not None and prime_record.body != "None":
                implicit_extension_count += 1
            elif (p, exponent) not in extension_records:
                missing.append(f"{p}^{exponent}")

    if missing:
        errors.append(
            f"{dimension}D results are missing coverage for "
            + ", ".join(missing[:20])
            + (f" (and {len(missing) - 20} more)" if len(missing) > 20 else "")
        )

    return errors, prime_count, extension_count, implicit_extension_count


def main(argv=None):
    """Audit one or both dimensions and print a compact coverage summary."""
    args = parse_args(argv)
    dimensions_to_check = (args.dimension,) if args.dimension else (3, 4)
    errors = []
    summaries = []

    for dimension in dimensions_to_check:
        order_bound = args.order_bound or DEFAULT_ORDER_BOUNDS[dimension]
        dimension_errors, prime_count, extension_count, implicit_count = (
            check_dimension(dimension, order_bound)
        )
        errors.extend(dimension_errors)
        summaries.append(
            f"{dimension}D below {order_bound}: {prime_count} primes and "
            f"{extension_count} extensions "
            f"({implicit_count} by prime-field inclusion)"
        )

    if errors:
        print_errors(errors)
        return 1

    print("Brick result coverage is complete (" + "; ".join(summaries) + ").")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
