#!/usr/bin/env python3
"""Verify every 3x3 GAP in the solution files.

For each printed tuple (A, x, y), this script reconstructs all values
A+i*x+j*y, checks that the nine values are distinct squares, and independently
checks the claimed row and column differences. It also validates every claim
that a solution is inherited through a finite-field inclusion.
"""

import re

# These imports support both ``python -m verification.gap_verify`` (package
# form) and ``python verification/gap_verify.py`` (direct script form). Both
# branches import the same functions; the arithmetic checks are unchanged.
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


# Expected locations and exact grammars for the two kinds of witness line.
RESULTS_DIR = PROJECT_ROOT / "results" / "gaps"
PRIME_RESULTS_PATH = RESULTS_DIR / "prime_field_solutions.txt"
EXTENSION_RESULTS_PATH = RESULTS_DIR / "extension_field_solutions.txt"
PRIME_SOLUTION_PATTERN = re.compile(
    r"base=([^,;]+), steps=\(([^,;]+), ([^,;]+)\)"
)
EXTENSION_SOLUTION_PATTERN = re.compile(
    r"base=([^,;]+), steps=\(([^,;]+), ([^,;]+)\); polynomial=(.+)"
)


def _gap_values(base, row_step, column_step, reduce_value):
    """Construct the nine entries A+i*x+j*y in row-major order.

    ``reduce_value`` performs arithmetic in the relevant field: reduction
    modulo p for prime fields, or construction as an F_(p^a) element for
    extension fields.
    """
    return [
        reduce_value(base + row * row_step + column * column_step)
        for row in range(3)
        for column in range(3)
    ]


def _verify_gap(values, row_step, column_step, key, is_square):
    """Return every mathematical defect found in one reconstructed GAP."""
    errors = []

    # Nine unique keys mean nine distinct field elements, even when the
    # library's extension-field objects themselves are not hashable.
    if len({key(value) for value in values}) != 9:
        errors.append("the nine GAP entries are not distinct")
    if not all(is_square(value) for value in values):
        errors.append("one or more GAP entries are not squares")

    # Row-major storage places each row in three consecutive positions.
    # Check both adjacent differences, rather than trusting construction, so
    # this verifier remains useful if its constructor later changes.
    for row in range(3):
        offset = 3 * row
        if key(values[offset + 1] - values[offset]) != key(column_step):
            errors.append("a row does not have the recorded column step")
            break
        if key(values[offset + 2] - values[offset + 1]) != key(column_step):
            errors.append("a row does not have the recorded column step")
            break

    # Moving one row down advances three positions in the flat list.
    for column in range(3):
        if key(values[3 + column] - values[column]) != key(row_step):
            errors.append("a column does not have the recorded row step")
            break
        if key(values[6 + column] - values[3 + column]) != key(row_step):
            errors.append("a column does not have the recorded row step")
            break

    return errors


def verify_prime_record(p, record):
    """Verify one prime-field line; return ``(is_solution, errors)``."""
    # ``None`` is a search claim rather than a witness. Exhaustiveness is
    # established by the search algorithm; there is no short object to check.
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

    # Keep all derived integers in their canonical residue classes.
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


def verify_extension_record(p, exponent, record):
    """Verify one explicit extension-field line in its recorded coordinates."""
    # Inherited entries are checked globally after their source witnesses have
    # been verified; ``None`` again contains no positive witness to inspect.
    if record.body == "None" or record.body.startswith("inherited from "):
        return False, []

    match = EXTENSION_SOLUTION_PATTERN.fullmatch(record.body)
    if match is None:
        return False, [f"{record.location}: malformed GAP solution"]

    base_text, row_step_text, column_step_text, polynomial_text = match.groups()
    try:
        field = extension_field(p, exponent, polynomial_text)
        base, row_step, column_step = (
            parse_extension_element(text, field, p, exponent)
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
        is_square=lambda value: is_extension_square(value, field),
    )
    return not errors, [f"{record.location}: {error}" for error in errors]


def main():
    """Verify both result files and print one summary or all discovered errors."""
    prime_records, prime_errors = read_prime_records(PRIME_RESULTS_PATH)
    extension_records, extension_errors = read_extension_records(
        EXTENSION_RESULTS_PATH
    )
    errors = prime_errors + extension_errors
    verified_prime_solutions = 0
    verified_extension_solutions = set()

    # A record counts as an explicit solution only after all mathematical
    # checks pass. This set is later the trusted source for inheritance claims.
    for p, record in prime_records.items():
        valid, record_errors = verify_prime_record(p, record)
        errors.extend(record_errors)
        verified_prime_solutions += int(valid)

    for (p, exponent), record in extension_records.items():
        valid, record_errors = verify_extension_record(p, exponent, record)
        errors.extend(record_errors)
        if valid:
            verified_extension_solutions.add((p, exponent))

    errors.extend(
        validate_inherited_records(extension_records, verified_extension_solutions)
    )

    if errors:
        print_errors(errors)
        return 1

    # Inherited records are reported separately because they contain no new
    # printed witness; their validity follows from the subfield theorem.
    inherited_count = sum(
        record.body.startswith("inherited from ")
        for record in extension_records.values()
    )
    print(
        "Verified "
        f"{verified_prime_solutions + len(verified_extension_solutions)} explicit GAP "
        f"solutions and {inherited_count} inherited entries "
        f"across {len(prime_records) + len(extension_records)} records."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
