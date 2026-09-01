#!/usr/bin/env python3
"""Check that the GAP results cover every odd field below the search bound."""

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


DEFAULT_ORDER_BOUND = 350_000
RESULTS_DIR = PROJECT_ROOT / "results" / "gaps"


def parse_args(argv=None):
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
    prime_records, prime_errors = read_prime_records(
        RESULTS_DIR / "prime_field_solutions.txt"
    )
    power_records, power_errors = read_power_records(
        RESULTS_DIR / "power_field_solutions.txt"
    )
    errors = prime_errors + power_errors
    missing = []
    prime_count = 0
    power_count = 0
    implicit_power_count = 0

    if order_bound <= 3:
        errors.append("order bound must be greater than 3")
        return errors, prime_count, power_count, implicit_power_count

    for p in primerange(3, order_bound):
        p = int(p)
        prime_count += 1
        prime_record = prime_records.get(p)
        if prime_record is None:
            missing.append(str(p))

        for exponent in prime_power_exponents(p, order_bound):
            power_count += 1
            # A solution in F_p embeds in every extension F_(p^a), which is
            # why the search deliberately emits no separate power records.
            if prime_record is not None and prime_record.body != "None":
                implicit_power_count += 1
            elif (p, exponent) not in power_records:
                missing.append(f"{p}^{exponent}")

    if missing:
        errors.append(
            "missing result coverage for "
            + ", ".join(missing[:20])
            + (f" (and {len(missing) - 20} more)" if len(missing) > 20 else "")
        )

    return errors, prime_count, power_count, implicit_power_count


def main(argv=None):
    args = parse_args(argv)
    errors, prime_count, power_count, implicit_power_count = check_coverage(
        args.order_bound
    )
    if errors:
        print_errors(errors)
        return 1

    print(
        f"GAP results cover all {prime_count} odd prime fields and "
        f"{power_count} odd extension fields below {args.order_bound} "
        f"({implicit_power_count} extensions covered by prime-field inclusion)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

