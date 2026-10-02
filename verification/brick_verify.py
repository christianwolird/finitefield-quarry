#!/usr/bin/env python3
"""Verify every explicit 3D and 4D strong perfect brick witness.

A recorded brick lists squared side lengths s_1,...,s_d. Each subset sum is
the square of a face diagonal of the corresponding axis-aligned box, including
0 for the empty subset and the full space diagonal for the complete subset.
This script checks that all 2^d sums are squares (perfection) and are pairwise
distinct (strength), then validates all recorded subfield inheritance claims.
"""

import re

# Permit the verifier to be run either as a package module or as the file path
# shown in the README. Both forms use the same shared verification helpers.
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


# Each dimension has separate result files but follows the same line grammar.
RESULTS_DIR = PROJECT_ROOT / "results" / "bricks"
DIMENSION_DIRS = {3: RESULTS_DIR / "three_dim", 4: RESULTS_DIR / "four_dim"}
PRIME_SOLUTION_PATTERN = re.compile(r"side_squares=\((.+)\)")
EXTENSION_SOLUTION_PATTERN = re.compile(
    r"side_squares=\((.+)\); polynomial=(.+)"
)


def _subset_sums(side_squares, zero):
    """Construct one sum for every subset of the supplied side squares."""
    sums = [zero]
    for side_square in side_squares:
        # Existing sums omit the new side; adding the side to a frozen copy of
        # that list produces exactly the subsets that contain it.
        sums.extend(total + side_square for total in tuple(sums))
    return sums


def _verify_brick(side_squares, dimension, zero, key, is_square):
    """Return every dimension, strength, or perfection error in a witness."""
    if len(side_squares) != dimension:
        return [f"expected {dimension} side squares, found {len(side_squares)}"]

    sums = _subset_sums(side_squares, zero)
    errors = []
    # Exactly 2^d distinct keys proves that no two different subsets give the
    # same diagonal square. This is the project's strong condition.
    if len({key(value) for value in sums}) != 2**dimension:
        errors.append("the side/diagonal squares (subset sums) are not distinct")
    if not all(is_square(value) for value in sums):
        errors.append("one or more side/diagonal values are not squares")
    return errors


def _split_sides(text):
    """Separate the comma-delimited side coordinates printed by the search."""
    return [part.strip() for part in text.split(",")]


def verify_prime_record(p, dimension, record):
    """Verify one prime-field brick line; return ``(is_solution, errors)``."""
    # A ``None`` line has no positive certificate. It is accepted as a
    # well-formed search result but does not increase the solution count.
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
        dimension,
        zero=0,
        key=lambda value: value % p,
        is_square=lambda value: is_prime_square(value, p),
    )
    return not errors, [f"{record.location}: {error}" for error in errors]


def verify_extension_record(p, exponent, dimension, record):
    """Verify one explicit extension-field brick in its recorded field model."""
    # Inheritance is checked after all possible source witnesses, so that only
    # an independently verified direct solution can justify an inherited one.
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
        dimension,
        zero=field(0),
        key=int,
        is_square=lambda value: is_extension_square(value, field),
    )
    return not errors, [f"{record.location}: {error}" for error in errors]


def verify_dimension(dimension):
    """Verify the prime and extension files for one brick dimension."""
    results_dir = DIMENSION_DIRS[dimension]
    prime_records, prime_errors = read_prime_records(
        results_dir / "prime_field_solutions.txt"
    )
    extension_records, extension_errors = read_extension_records(
        results_dir / "extension_field_solutions.txt"
    )
    errors = prime_errors + extension_errors
    verified_prime_solutions = 0
    verified_extension_solutions = set()

    # Count only explicit witnesses that pass every check. Keep extension
    # solutions as (p,a) pairs for the later subfield-inheritance audit.
    for p, record in prime_records.items():
        valid, record_errors = verify_prime_record(p, dimension, record)
        errors.extend(record_errors)
        verified_prime_solutions += int(valid)

    for (p, exponent), record in extension_records.items():
        valid, record_errors = verify_extension_record(
            p, exponent, dimension, record
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
    """Verify both supported dimensions and combine their reports."""
    errors = []
    summaries = []

    for dimension in (3, 4):
        dimension_errors, solution_count, inherited_count, record_count = (
            verify_dimension(dimension)
        )
        errors.extend(dimension_errors)
        summaries.append(
            f"{dimension}D: {solution_count} explicit solutions, "
            f"{inherited_count} inherited entries, {record_count} total records"
        )

    if errors:
        print_errors(errors)
        return 1

    print("Verified all brick results (" + "; ".join(summaries) + ").")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
