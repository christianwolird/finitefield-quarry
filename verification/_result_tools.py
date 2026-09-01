"""Shared parsing and finite-field helpers for the verification scripts."""

from dataclasses import dataclass
from functools import cache
from pathlib import Path
import re

import galois
from sympy import isprime


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Record:
    path: Path
    line_number: int
    label: str
    body: str

    @property
    def location(self):
        return f"{self.path}:{self.line_number}"


def _read_records(path):
    records = []
    errors = []

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return [], [f"{path}: could not read file: {error}"]

    if not lines:
        errors.append(f"{path}: result file is empty")

    for line_number, line in enumerate(lines, start=1):
        match = re.fullmatch(r"([^:]+): (.+)", line)
        if match is None:
            errors.append(f"{path}:{line_number}: malformed result line")
            continue

        records.append(
            Record(
                path=path,
                line_number=line_number,
                label=match.group(1),
                body=match.group(2),
            )
        )

    return records, errors


def read_prime_records(path):
    """Return prime-field records keyed by their (odd) prime order."""
    raw_records, errors = _read_records(path)
    records = {}

    for record in raw_records:
        if re.fullmatch(r"[1-9]\d*", record.label) is None:
            errors.append(
                f"{record.location}: invalid prime-field label {record.label!r}"
            )
            continue

        p = int(record.label)
        if p == 2 or not isprime(p):
            errors.append(f"{record.location}: {p} is not an odd prime")
            continue
        if p in records:
            errors.append(f"{record.location}: duplicate entry for {p}")
            continue

        records[p] = record

    return records, errors


def read_power_records(path):
    """Return extension-field records keyed by ``(prime, exponent)``."""
    raw_records, errors = _read_records(path)
    records = {}

    for record in raw_records:
        match = re.fullmatch(r"([1-9]\d*)\^([1-9]\d*)", record.label)
        if match is None:
            errors.append(
                f"{record.location}: invalid prime-power label {record.label!r}"
            )
            continue

        p, exponent = map(int, match.groups())
        if p == 2 or not isprime(p):
            errors.append(f"{record.location}: {p} is not an odd prime")
            continue
        if exponent < 2:
            errors.append(f"{record.location}: extension exponent must be at least 2")
            continue

        key = (p, exponent)
        if key in records:
            errors.append(f"{record.location}: duplicate entry for {record.label}")
            continue

        records[key] = record

    return records, errors


@cache
def extension_field(p, exponent, polynomial_text):
    """Construct the exact extension field named by a result record."""
    # Verification performs only a handful of operations in each of many
    # different fields. Pure-Python arithmetic avoids paying a separate Numba
    # compilation cost for every result-file polynomial.
    prime_field = galois.GF(p, compile="python-calculate")
    try:
        polynomial = galois.Poly.Str(polynomial_text, field=prime_field)
    except Exception as error:
        raise ValueError(f"invalid polynomial {polynomial_text!r}: {error}") from error

    if polynomial.degree != exponent:
        raise ValueError(
            f"polynomial degree {polynomial.degree} does not match exponent {exponent}"
        )
    if not polynomial.is_irreducible():
        raise ValueError(f"polynomial {polynomial_text!r} is not irreducible")
    if not polynomial.is_primitive():
        raise ValueError(f"polynomial {polynomial_text!r} is not primitive")

    try:
        return galois.GF(
            p**exponent,
            irreducible_poly=polynomial,
            compile="python-calculate",
        )
    except Exception as error:
        raise ValueError(f"could not construct field: {error}") from error


def parse_prime_element(text, p):
    """Parse the canonical integer representation of an element of F_p."""
    if re.fullmatch(r"0|[1-9]\d*", text) is None:
        raise ValueError(f"invalid prime-field element {text!r}")

    value = int(text)
    if value >= p:
        raise ValueError(f"element {value} is not in the canonical range 0,...,{p - 1}")
    return value


def parse_power_element(text, field, p, exponent):
    """Parse galois's polynomial representation in the primitive element α."""
    if not text:
        raise ValueError("empty field element")

    value = field(0)
    seen_degrees = set()

    for term in re.split(r"\s*\+\s*", text):
        constant_match = re.fullmatch(r"0|[1-9]\d*", term)
        alpha_match = re.fullmatch(r"(?:(\d+))?α(?:\^(\d+))?", term)

        if constant_match is not None:
            coefficient = int(term)
            degree = 0
        elif alpha_match is not None:
            coefficient = int(alpha_match.group(1) or 1)
            degree = int(alpha_match.group(2) or 1)
        else:
            raise ValueError(f"invalid extension-field term {term!r}")

        if coefficient >= p:
            raise ValueError(f"coefficient {coefficient} is outside 0,...,{p - 1}")
        if degree >= exponent:
            raise ValueError(
                f"power α^{degree} is not reduced below field degree {exponent}"
            )
        if degree in seen_degrees:
            raise ValueError(f"degree {degree} occurs more than once")
        seen_degrees.add(degree)

        value += field(coefficient) * field.primitive_element**degree

    return value


def is_prime_square(value, p):
    value %= p
    return value == 0 or pow(value, (p - 1) // 2, p) == 1


def is_power_square(value, field):
    return value == field(0) or value ** ((field.order - 1) // 2) == field(1)


def prime_power_exponents(p, order_bound):
    exponent = 2
    order = p * p
    while order < order_bound:
        yield exponent
        exponent += 1
        order *= p


def validate_inherited_records(power_records, direct_solutions):
    """Check that inherited entries point to a valid embedded solution."""
    errors = []
    inheritance_pattern = re.compile(r"inherited from ([1-9]\d*)\^([1-9]\d*)")

    for (p, exponent), record in power_records.items():
        if not record.body.startswith("inherited from "):
            continue

        match = inheritance_pattern.fullmatch(record.body)
        if match is None:
            errors.append(f"{record.location}: malformed inheritance entry")
            continue

        source_p, source_exponent = map(int, match.groups())
        source = (source_p, source_exponent)
        if source_p != p:
            errors.append(
                f"{record.location}: inherited solution has a different characteristic"
            )
        elif source_exponent >= exponent or exponent % source_exponent != 0:
            errors.append(
                f"{record.location}: F_({p}^{source_exponent}) does not embed in "
                f"F_({p}^{exponent})"
            )
        elif source not in power_records:
            errors.append(f"{record.location}: inherited source has no result entry")
        elif source not in direct_solutions:
            errors.append(
                f"{record.location}: inherited source is not a verified explicit "
                "solution"
            )

    return errors


def print_errors(errors):
    for error in errors:
        print(f"ERROR: {error}")
