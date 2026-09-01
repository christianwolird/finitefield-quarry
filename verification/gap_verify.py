#!/usr/bin/env python3
"""Verify every explicit 3x3 GAP witness in the checked-in results."""

import re

try:
    from ._result_tools import (
        PROJECT_ROOT,
        extension_field,
        is_power_square,
        is_prime_square,
        parse_power_element,
        parse_prime_element,
        print_errors,
        read_power_records,
        read_prime_records,
        validate_inherited_records,
    )
except ImportError:
    from _result_tools import (
        PROJECT_ROOT,
        extension_field,
        is_power_square,
        is_prime_square,
        parse_power_element,
        parse_prime_element,
        print_errors,
        read_power_records,
        read_prime_records,
        validate_inherited_records,
    )


RESULTS_DIR = PROJECT_ROOT / "results" / "gaps"
PRIME_RESULTS_PATH = RESULTS_DIR / "prime_field_solutions.txt"
POWER_RESULTS_PATH = RESULTS_DIR / "power_field_solutions.txt"
PRIME_SOLUTION_PATTERN = re.compile(
    r"base=([^,;]+), steps=\(([^,;]+), ([^,;]+)\)"
)
POWER_SOLUTION_PATTERN = re.compile(
    r"base=([^,;]+), steps=\(([^,;]+), ([^,;]+)\); polynomial=(.+)"
)


def _gap_values(base, row_step, column_step, reduce_value):
    return [
        reduce_value(base + row * row_step + column * column_step)
        for row in range(3)
        for column in range(3)
    ]


def _verify_gap(values, row_step, column_step, key, is_square):
    errors = []

    if len({key(value) for value in values}) != 9:
        errors.append("the nine GAP entries are not distinct")
    if not all(is_square(value) for value in values):
        errors.append("one or more GAP entries are not squares")

    for row in range(3):
        offset = 3 * row
        if key(values[offset + 1] - values[offset]) != key(column_step):
            errors.append("a row does not have the recorded column step")
            break
        if key(values[offset + 2] - values[offset + 1]) != key(column_step):
            errors.append("a row does not have the recorded column step")
            break

    for column in range(3):
        if key(values[3 + column] - values[column]) != key(row_step):
            errors.append("a column does not have the recorded row step")
            break
        if key(values[6 + column] - values[3 + column]) != key(row_step):
            errors.append("a column does not have the recorded row step")
            break

    return errors


def verify_prime_record(p, record):
    if record.body == "None":
        return False, []

    match = PRIME_SOLUTION_PATTERN.fullmatch(record.body)
    if match is None:
        return False, [f"{record.location}: malformed GAP solution"]

    try:
        base, row_step, column_step = (
            parse_prime_element(text, p) for text in match.groups()
        )
    except ValueError as error:
        return False, [f"{record.location}: {error}"]

    reduce_value = lambda value: value % p
    values = _gap_values(base, row_step, column_step, reduce_value)
    errors = _verify_gap(
        values,
        row_step,
        column_step,
        key=reduce_value,
        is_square=lambda value: is_prime_square(value, p),
    )
    return not errors, [f"{record.location}: {error}" for error in errors]


def verify_power_record(p, exponent, record):
    if record.body == "None" or record.body.startswith("inherited from "):
        return False, []

    match = POWER_SOLUTION_PATTERN.fullmatch(record.body)
    if match is None:
        return False, [f"{record.location}: malformed GAP solution"]

    base_text, row_step_text, column_step_text, polynomial_text = match.groups()
    try:
        field = extension_field(p, exponent, polynomial_text)
        base, row_step, column_step = (
            parse_power_element(text, field, p, exponent)
            for text in (base_text, row_step_text, column_step_text)
        )
    except ValueError as error:
        return False, [f"{record.location}: {error}"]

    values = _gap_values(base, row_step, column_step, field)
    errors = _verify_gap(
        values,
        row_step,
        column_step,
        key=int,
        is_square=lambda value: is_power_square(value, field),
    )
    return not errors, [f"{record.location}: {error}" for error in errors]


def main():
    prime_records, prime_errors = read_prime_records(PRIME_RESULTS_PATH)
    power_records, power_errors = read_power_records(POWER_RESULTS_PATH)
    errors = prime_errors + power_errors
    verified_prime_solutions = 0
    verified_power_solutions = set()

    for p, record in prime_records.items():
        valid, record_errors = verify_prime_record(p, record)
        errors.extend(record_errors)
        verified_prime_solutions += int(valid)

    for (p, exponent), record in power_records.items():
        valid, record_errors = verify_power_record(p, exponent, record)
        errors.extend(record_errors)
        if valid:
            verified_power_solutions.add((p, exponent))

    errors.extend(validate_inherited_records(power_records, verified_power_solutions))

    if errors:
        print_errors(errors)
        return 1

    inherited_count = sum(
        record.body.startswith("inherited from ") for record in power_records.values()
    )
    print(
        "Verified "
        f"{verified_prime_solutions + len(verified_power_solutions)} explicit GAP "
        f"solutions and {inherited_count} inherited entries "
        f"across {len(prime_records) + len(power_records)} records."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
