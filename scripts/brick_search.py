"""Search finite fields for strong perfect 3D or 4D Euler bricks.

The search first checks prime fields, then checks extension fields for each
prime characteristic where no brick was found. A brick is represented by the
squares of its side lengths. Perfect means every subset sum is a square;
strong means those sums are all distinct. This search requires both
properties, so every subset sum must be a distinct square in the field.

The search algorithms themselves are in ``src/ffquarry/brick_tools.py``.
This file connects those algorithms to the command line: it reads the chosen
dimension and order bound, selects prime or extension fields, and writes the
results to the files under ``results/bricks``.
"""

import argparse
from pathlib import Path
from time import perf_counter

from sympy import primerange

from ffquarry.brick_tools import smart_search
from ffquarry.extension_field import ExtensionField
from ffquarry.prime_field import PrimeField

# Path to results directory. Results are kept in separate sub-directories
# for prime fields and extension fields.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "bricks"

# Keep records for different dimensions in different files.
# Their search methods and order bounds differ.
# Both dimensions still use the same result format.
DIMENSION_RESULTS_DIRS = {
    3: RESULTS_DIR / "three_dim",
    4: RESULTS_DIR / "four_dim",
}

PRIME_RESULTS_PATHS = {
    dimension: results_dir / "prime_field_solutions.txt"
    for dimension, results_dir in DIMENSION_RESULTS_DIRS.items()
}

EXTENSION_RESULTS_PATHS = {
    dimension: results_dir / "extension_field_solutions.txt"
    for dimension, results_dir in DIMENSION_RESULTS_DIRS.items()
}


# This function defines the choices a person can give when starting the
# program: which dimension to search, how large fields may be, and whether to
# print progress as each field is checked.
def parse_args(argv=None):
    """Read the dimension, exclusive order bound, and progress option."""
    parser = argparse.ArgumentParser(
        description=(
            "Search for 3D and 4D strong perfect Euler bricks "
            "over odd finite fields below the order bound."
        )
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print progress for every finite field considered.",
    )
    parser.add_argument(
        "--dimension",
        type=int,
        choices=(3, 4),
        required=True,
        help="Choose the single brick dimension to search.",
    )
    parser.add_argument(
        "order_bound",
        type=int,
        help="Search finite fields with order below this bound.",
    )
    return parser.parse_args(argv)


def extension_exponents(p, order_bound):
    """Yield `a` for which the extension field F_(p^a) is below the bound."""
    exponent = 2
    order = p * p

    while order < order_bound:
        yield exponent
        exponent += 1
        order *= p


def _format_sides(field, sides):
    """Write the side-square values in the notation used by result files."""
    return ", ".join(field.format(side) for side in sides)


# First check fields whose size is a prime p. Only the primes with no example
# need further attention: an example over F_p also exists in every larger
# field containing F_p.
def prime_search(order_bound, dimension, verbose=False):
    """Search odd prime fields and record whether each contains a brick.

    The returned primes are precisely the characteristics that still need an
    extension-field search. Characteristic 2 is omitted from the search.
    """
    DIMENSION_RESULTS_DIRS[dimension].mkdir(parents=True, exist_ok=True)
    no_solution_primes = []

    # Write mode ensures that the file contains exactly the records from this
    # run, with no leftover fields from an earlier bound.
    with open(PRIME_RESULTS_PATHS[dimension], "w", encoding="utf-8") as results_file:
        # The upper bound itself is excluded.
        for p in primerange(order_bound):
            if p == 2:
                continue

            if verbose:
                print(
                    f"Finding a {dimension}D brick solution over F_{p}...",
                    flush=True,
                )

            # A returned tuple is a witness solution. None means
            # the quick search and exhaustive fallback both failed.
            field = PrimeField(p)
            result = smart_search(field, dimension)

            if result is None:
                no_solution_primes.append(p)
                results_file.write(f"{p}: None\n")
            else:
                results_file.write(
                    f"{p}: side_squares=({_format_sides(field, result)})\n"
                )
            # Save each completed field immediately during a potentially long
            # computation.
            results_file.flush()

    return no_solution_primes


def extension_search(order_bound, dimension, no_solution_primes, verbose=False):
    """Search extensions of prime fields where the prime search found none.

    If a brick is found in F_(p^a), it also exists in F_(p^b) whenever a
    divides b, because the smaller field is contained in the larger one. Such
    larger fields are recorded as inherited instead of searched again.
    """
    DIMENSION_RESULTS_DIRS[dimension].mkdir(parents=True, exist_ok=True)
    no_solution_extension_orders = []

    # For each unresolved prime p, check fields F_(p^a) in increasing order.
    # If a previously found exponent divides a, that smaller field sits
    # inside F_(p^a), so it already has a solution and we can skip it.
    with open(
        EXTENSION_RESULTS_PATHS[dimension], "w", encoding="utf-8"
    ) as results_file:
        for p in no_solution_primes:
            # Record degrees with explicit solutions. A later extension degree
            # divisible by one of these inherits the same brick.
            solved_exponents = []

            for exponent in extension_exponents(p, order_bound):
                q = p**exponent
                label = f"{p}^{exponent}"
                # The first dividing degree is enough to certify inheritance;
                # no preference among several valid source fields is needed.
                inherited_from = next(
                    (
                        solved
                        for solved in solved_exponents
                        if exponent % solved == 0
                    ),
                    None,
                )

                if verbose:
                    print(
                        f"Finding a {dimension}D brick solution over "
                        f"F_({label}) of order {q}...",
                        flush=True,
                    )

                # Record the inherited solution, if it exists.
                if inherited_from is not None:
                    results_file.write(
                        f"{label}: inherited from {p}^{inherited_from}\n"
                    )
                    results_file.flush()
                    continue

                field = ExtensionField(q)
                # The search returns the squares of the side lengths.
                result = smart_search(field, dimension)

                if result is None:
                    no_solution_extension_orders.append(q)
                    results_file.write(f"{label}: None\n")
                else:
                    solved_exponents.append(exponent)
                    # Write the square side lengths and the polynomial used
                    # to construct the current finite field extension.
                    results_file.write(
                        f"{label}: "
                        f"side_squares=({_format_sides(field, result)}); "
                        f"polynomial={field.gf.irreducible_poly}\n"
                    )
                results_file.flush()

    return no_solution_extension_orders


def main(argv=None):
    """Run the prime-field search followed by any needed extension searches."""
    args = parse_args(argv)
    dimension = args.dimension
    # Create the output folder before starting either search; the detailed
    # records are written by prime_search() and extension_search().
    DIMENSION_RESULTS_DIRS[dimension].mkdir(parents=True, exist_ok=True)
    start_time = perf_counter()

    print(
        f"Beginning {dimension}D strong perfect brick search below "
        f"order {args.order_bound}...",
        flush=True,
    )
    no_solution_primes = prime_search(
        args.order_bound,
        dimension,
        verbose=args.verbose,
    )
    no_solution_extension_orders = extension_search(
        args.order_bound,
        dimension,
        no_solution_primes,
        verbose=args.verbose,
    )
    elapsed = perf_counter() - start_time

    print(f"Completed {dimension}D search in {elapsed:.2f} seconds.")
    print(f"  Prime fields without a solution: {no_solution_primes}")
    print(
        "  Extension fields without a solution: "
        f"{no_solution_extension_orders}",
        flush=True,
    )


# Keep imports side-effect free for tests and other Python callers.
if __name__ == "__main__":
    main()
