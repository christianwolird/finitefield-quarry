import argparse
from pathlib import Path
from time import perf_counter

from sympy import primerange

from ffquarry.brick_tools import smart_search
from ffquarry.extension_field import ExtensionField
from ffquarry.prime_field import PrimeField

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "bricks"
DIMENSION_RESULTS_DIRS = {
    3: RESULTS_DIR / "three_dim",
    4: RESULTS_DIR / "four_dim",
}
PRIME_RESULTS_PATHS = {
    dimensions: results_dir / "prime_field_solutions.txt"
    for dimensions, results_dir in DIMENSION_RESULTS_DIRS.items()
}
EXTENSION_RESULTS_PATHS = {
    dimensions: results_dir / "extension_field_solutions.txt"
    for dimensions, results_dir in DIMENSION_RESULTS_DIRS.items()
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Search for 3D and 4D perfect Euler bricks of distinct squares "
            "over odd finite fields below the order bound."
        )
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print every finite field as it is searched.",
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
    exponent = 2
    order = p * p

    while order < order_bound:
        yield exponent
        exponent += 1
        order *= p


def _format_sides(field, sides):
    return ", ".join(field.format(side) for side in sides)


def prime_search(order_bound, dimensions, verbose=False):
    """Search odd prime fields and write the selected dimension's results."""
    DIMENSION_RESULTS_DIRS[dimensions].mkdir(parents=True, exist_ok=True)
    no_solution_primes = []

    with open(PRIME_RESULTS_PATHS[dimensions], "w", encoding="utf-8") as results_file:
        for p in primerange(order_bound):
            if p == 2:
                continue

            if verbose:
                print(f"Checking {dimensions}D bricks over F_{p}...", flush=True)

            field = PrimeField(p)
            result = smart_search(field, dimensions)

            if result is None:
                no_solution_primes.append(p)
                results_file.write(f"{p}: None\n")
            else:
                results_file.write(
                    f"{p}: side_squares=({_format_sides(field, result)})\n"
                )
            results_file.flush()

    return no_solution_primes


def extension_search(order_bound, dimensions, no_solution_primes, verbose=False):
    """Search extension fields for characteristics unresolved over F_p."""
    DIMENSION_RESULTS_DIRS[dimensions].mkdir(parents=True, exist_ok=True)
    no_solution_extension_orders = []

    with open(
        EXTENSION_RESULTS_PATHS[dimensions], "w", encoding="utf-8"
    ) as results_file:
        for p in no_solution_primes:
            solved_exponents = []

            for exponent in extension_exponents(p, order_bound):
                q = p**exponent
                label = f"{p}^{exponent}"
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
                        f"Checking {dimensions}D bricks over "
                        f"F_({label}) of order {q}...",
                        flush=True,
                    )

                if inherited_from is not None:
                    results_file.write(
                        f"{label}: inherited from {p}^{inherited_from}\n"
                    )
                    results_file.flush()
                    continue

                field = ExtensionField(q)
                result = smart_search(field, dimensions)

                if result is None:
                    no_solution_extension_orders.append(q)
                    results_file.write(f"{label}: None\n")
                else:
                    solved_exponents.append(exponent)
                    results_file.write(
                        f"{label}: "
                        f"side_squares=({_format_sides(field, result)}); "
                        f"polynomial={field.gf.irreducible_poly}\n"
                    )
                results_file.flush()

    return no_solution_extension_orders


def main(argv=None):
    args = parse_args(argv)
    dimensions = args.dimension
    DIMENSION_RESULTS_DIRS[dimensions].mkdir(parents=True, exist_ok=True)
    start_time = perf_counter()

    print(
        f"Beginning {dimensions}D perfect-brick search below "
        f"order {args.order_bound}...",
        flush=True,
    )
    no_solution_primes = prime_search(
        args.order_bound,
        dimensions,
        verbose=args.verbose,
    )
    no_solution_extension_orders = extension_search(
        args.order_bound,
        dimensions,
        no_solution_primes,
        verbose=args.verbose,
    )
    elapsed = perf_counter() - start_time

    print(f"Completed {dimensions}D search in {elapsed:.2f} seconds.")
    print(f"  Prime fields without a solution: {no_solution_primes}")
    print(
        "  Extension fields without a solution: "
        f"{no_solution_extension_orders}",
        flush=True,
    )


if __name__ == "__main__":
    main()
