#!/usr/bin/env python3
"""Verify every explicit 3D and 4D perfect-brick witness."""

import re

try:
    from ._result_tools import (
        PROJECT_ROOT,
        extension_field,
        is_extension_square,
        is_prime_square,
        parse_extension_element,
        parse_prime_element,
        print_errors,
        read_extension_records,
        read_prime_records,
        validate_inherited_records,
    )
except ImportError:
    from _result_tools import (
        PROJECT_ROOT,
        extension_field,
        is_extension_square,
        is_prime_square,
        parse_extension_element,
        parse_prime_element,
        print_errors,
        read_extension_records,
        read_prime_records,
        validate_inherited_records,
    )


RESULTS_DIR = PROJECT_ROOT / "results" / "bricks"
DIMENSION_DIRS = {3: RESULTS_DIR / "three_dim", 4: RESULTS_DIR / "four_dim"}
PRIME_SOLUTION_PATTERN = re.compile(r"side_squares=\((.+)\)")
EXTENSION_SOLUTION_PATTERN = re.compile(
    r"side_squares=\((.+)\); polynomial=(.+)"
)


def _subset_sums(side_squares, zero):
    sums = [zero]
    for side_square in side_squares:
        sums.extend(total + side_square for total in tuple(sums))
    return sums


def _verify_brick(side_squares, dimensions, zero, key, is_square):
    if len(side_squares) != dimensions:
        return [f"expected {dimensions} side squares, found {len(side_squares)}"]

    sums = _subset_sums(side_squares, zero)
    errors = []
    if len({key(value) for value in sums}) != 2**dimensions:
        errors.append("the side/diagonal squares (subset sums) are not distinct")
    if not all(is_square(value) for value in sums):
        errors.append("one or more side/diagonal values are not squares")
    return errors


def _split_sides(text):
    return [part.strip() for part in text.split(",")]


def verify_prime_record(p, dimensions, record):
    if record.body == "None":
        return False, []

    match = PRIME_SOLUTION_PATTERN.fullmatch(record.body)
    if match is None:
        return False, [f"{record.location}: malformed brick solution"]

    try:
        sides = [parse_prime_element(text, p) for text in _split_sides(match.group(1))]
    except ValueError as error:
        return False, [f"{record.location}: {error}"]

    errors = _verify_brick(
        sides,
        dimensions,
        zero=0,
        key=lambda value: value % p,
        is_square=lambda value: is_prime_square(value, p),
    )
    return not errors, [f"{record.location}: {error}" for error in errors]


def verify_extension_record(p, exponent, dimensions, record):
    if record.body == "None" or record.body.startswith("inherited from "):
        return False, []

    match = EXTENSION_SOLUTION_PATTERN.fullmatch(record.body)
    if match is None:
        return False, [f"{record.location}: malformed brick solution"]

    side_text, polynomial_text = match.groups()
    try:
        field = extension_field(p, exponent, polynomial_text)
        sides = [
            parse_extension_element(text, field, p, exponent)
            for text in _split_sides(side_text)
        ]
    except ValueError as error:
        return False, [f"{record.location}: {error}"]

    errors = _verify_brick(
        sides,
        dimensions,
        zero=field(0),
        key=int,
        is_square=lambda value: is_extension_square(value, field),
    )
    return not errors, [f"{record.location}: {error}" for error in errors]


def verify_dimension(dimensions):
    results_dir = DIMENSION_DIRS[dimensions]
    prime_records, prime_errors = read_prime_records(
        results_dir / "prime_field_solutions.txt"
    )
    extension_records, extension_errors = read_extension_records(
        results_dir / "extension_field_solutions.txt"
    )
    errors = prime_errors + extension_errors
    verified_prime_solutions = 0
    verified_extension_solutions = set()

    for p, record in prime_records.items():
        valid, record_errors = verify_prime_record(p, dimensions, record)
        errors.extend(record_errors)
        verified_prime_solutions += int(valid)

    for (p, exponent), record in extension_records.items():
        valid, record_errors = verify_extension_record(
            p, exponent, dimensions, record
        )
        errors.extend(record_errors)
        if valid:
            verified_extension_solutions.add((p, exponent))

    errors.extend(
        validate_inherited_records(extension_records, verified_extension_solutions)
    )
    inherited_count = sum(
        record.body.startswith("inherited from ")
        for record in extension_records.values()
    )
    return (
        errors,
        verified_prime_solutions + len(verified_extension_solutions),
        inherited_count,
        len(prime_records) + len(extension_records),
    )


def main():
    errors = []
    summaries = []

    for dimensions in (3, 4):
        dimension_errors, solution_count, inherited_count, record_count = (
            verify_dimension(dimensions)
        )
        errors.extend(dimension_errors)
        summaries.append(
            f"{dimensions}D: {solution_count} explicit solutions, "
            f"{inherited_count} inherited entries, {record_count} total records"
        )

    if errors:
        print_errors(errors)
        return 1

    print("Verified all brick results (" + "; ".join(summaries) + ").")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
