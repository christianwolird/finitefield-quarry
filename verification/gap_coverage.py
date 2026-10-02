#!/usr/bin/env python3
"""Check that GAP result files cover every odd field below a chosen bound.

This complements ``gap_verify`` which checks the validity of the solutions.
"""

import argparse

from sympy import primerange

# Support invocation either as a package module or by the README's file path.
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


# Match the bound used to produce the current GAP result files.
DEFAULT_ORDER_BOUND = 200_000
RESULTS_DIR = PROJECT_ROOT / "results" / "gaps"


def parse_args(argv=None):
    """Read the exclusive field-order bound used for the coverage claim."""
    parser = argparse.ArgumentParser(
        description="Check coverage of the GAP result files."
    )
    parser.add_argument(
        "order_bound",
        type=int,
        nargs="?",
        default=DEFAULT_ORDER_BOUND,
        help=f"exclusive field-order bound (default: {DEFAULT_ORDER_BOUND})",
    )
    return parser.parse_args(argv)


def check_coverage(order_bound):
    """Return errors and counts for every odd field of order below the bound."""
    prime_records, prime_errors = read_prime_records(
        RESULTS_DIR / "prime_field_solutions.txt"
    )
    extension_records, extension_errors = read_extension_records(
        RESULTS_DIR / "extension_field_solutions.txt"
    )
    errors = prime_errors + extension_errors
    missing = []
    prime_count = 0
    extension_count = 0
    implicit_extension_count = 0

    if order_bound <= 3:
        errors.append("order bound must be greater than 3")
        return errors, prime_count, extension_count, implicit_extension_count

    # Every finite field has prime-power order p^a. Iterating over primes p
    # and then all exponents a therefore enumerates the entire claimed range
    # exactly once. Exponent one is the prime field handled before the loop.
    for p in primerange(3, order_bound):
        p = int(p)
        prime_count += 1
        prime_record = prime_records.get(p)
        # Whether it says ``None`` or gives a witness, the prime-field record
        # proves that this field was processed. Absence is a coverage failure.
        if prime_record is None:
            missing.append(str(p))

        for exponent in extension_exponents(p, order_bound):
            extension_count += 1
            # A solution in F_p embeds in every extension F_(p^a), which is
            # why the search deliberately emits no separate extension records.
            if prime_record is not None and prime_record.body != "None":
                implicit_extension_count += 1
            # If the prime field had no solution, each extension needs its own
            # direct, inherited, or ``None`` record from the extension search.
            elif (p, exponent) not in extension_records:
                missing.append(f"{p}^{exponent}")

    if missing:
        errors.append(
            "missing result coverage for "
            + ", ".join(missing[:20])
            + (f" (and {len(missing) - 20} more)" if len(missing) > 20 else "")
        )

    return errors, prime_count, extension_count, implicit_extension_count


def main(argv=None):
    """Check coverage and return a process status suitable for automation."""
    args = parse_args(argv)
    errors, prime_count, extension_count, implicit_extension_count = check_coverage(
        args.order_bound
    )
    if errors:
        print_errors(errors)
        return 1

    print(
        f"GAP results cover all {prime_count} odd prime fields and "
        f"{extension_count} odd extension fields below {args.order_bound} "
        f"({implicit_extension_count} extensions covered by prime-field inclusion)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
