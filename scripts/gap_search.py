"""Search finite fields for 3-by-3 generalized progressions of squares.

Each progression has a base value and two common differences, one for each
direction in the array. The search checks prime fields first, then considers
extension fields only for characteristics over an unresolved prime field.

The algorithms that construct and test progressions are in
``src/ffquarry/gap_tools.py``. This file handles the command line, chooses
which finite fields to examine, and writes the resulting examples to
``results/gaps``.
"""

import argparse
from pathlib import Path
from time import perf_counter

from sympy import primerange

from ffquarry.extension_field import ExtensionField
from ffquarry.gap_tools import smart_search
from ffquarry.prime_field import PrimeField

# Result file paths and the default upper bound for field order.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "gaps"
PRIME_RESULTS_PATH = RESULTS_DIR / "prime_field_solutions.txt"
EXTENSION_RESULTS_PATH = RESULTS_DIR / "extension_field_solutions.txt"
DEFAULT_ORDER_BOUND = 200_000


# This function defines the command-line choices: the largest field size to
# consider and whether to print progress during the search.
def parse_args(argv=None):
    """Read the exclusive field-order bound and optional progress display."""
    parser = argparse.ArgumentParser(
        description=(
            "Search for 3x3 generalized arithmetic progressions of distinct "
            "squares over odd finite fields below the order bound."
        )
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help=(
            "Print each unresolved characteristic and extension-field order "
            "as it is considered."
        ),
    )
    parser.add_argument(
        "order_bound",
        type=int,
        nargs="?",
        default=DEFAULT_ORDER_BOUND,
        help=(
            "Search finite fields with order below this bound "
            f"(default: {DEFAULT_ORDER_BOUND})."
        ),
    )
    return parser.parse_args(argv)


# Search first in fields with prime size p. If a progression is found there,
# it is automatically present in every extension field containing F_p, so
# only primes with no example are passed on to extension_search().
def prime_search(order_bound, verbose=False):
    """Search each odd prime field below the bound and save its result.

    A solution over the prime field remains a solution in every extension
    field of the same characteristic, since those fields contain the prime
    field. The returned list therefore contains only characteristics that
    require further searching.
    """
    no_solution_primes = []

    # Opening in write mode starts the result file from scratch without
    # stale records from an earlier run.
    with open(PRIME_RESULTS_PATH, "w", encoding="utf-8") as results_file:
        # Prime fields with a solution also settle all extension fields of
        # the same characteristic, so only failures move on to
        # extension_search().
        # `primerange` excludes the upper bound itself from the search.
        for p in primerange(order_bound):
            if p == 2:
                continue

            # smart_search returns either the certificate (A,x,y) or None
            # if the exhaustive fallback search found no solution.
            field = PrimeField(p)
            result = smart_search(field)

            if result is None:
                no_solution_primes.append(p)
                if verbose:
                    print(f"  Prime field of order {p} has no solution.", flush=True)

                results_file.write(f"{p}: None\n")
                continue

            # These three values determine all nine entries, so storing the
            # whole array would add nothing.
            A, x, y = result
            results_file.write(
                f"{p}: base={field.format(A)}, "
                f"steps=({field.format(x)}, {field.format(y)})\n"
            )

    return no_solution_primes


def extension_exponents(p, order_bound):
    """Yield exponents a>=2 for which the field with p^a elements is in range."""
    exponent = 2
    order = p * p

    # Start at p^2; the prime field p was already handled in prime_search().
    # Successive extension-field sizes are p^2, p^3, p^4, and so on.
    while order < order_bound:
        yield exponent
        exponent += 1
        order *= p


def extension_search(order_bound, no_solution_primes, verbose=False):
    """Search extensions for characteristics with no prime-field solution.

    When a solution is found in F_(p^a), it is inherited by F_(p^b) whenever
    a divides b: in that case F_(p^a) is a subfield of F_(p^b). The result file
    records this fact and avoids repeating the search in that larger field.
    """
    no_solution_extension_orders = []

    # Store each extension-field result separately from the prime-field
    # results, including a note when a smaller field already supplies it.
    with open(EXTENSION_RESULTS_PATH, "w", encoding="utf-8") as results_file:
        for p in no_solution_primes:
            if verbose:
                print(
                    f"Finding solutions over extension fields of characteristic {p}...",
                    flush=True,
                )

            # These are degrees with previously found solutions. Later degrees
            # divisible by one of them are settled by subfield inclusion.
            solved_exponents = []

            for exponent in extension_exponents(p, order_bound):
                q = p**exponent
                label = f"{p}^{exponent}"
                inherited_from = None

                # F_{p^a} embeds in F_{p^b} exactly when a divides b.
                for solved_exponent in solved_exponents:
                    if exponent % solved_exponent == 0:
                        inherited_from = solved_exponent
                        break

                if verbose:
                    print(
                        f"Finding a GAP solution over F_({label}) of order {q}...",
                        flush=True,
                    )

                if inherited_from is not None:
                    if verbose:
                        print(
                            f"  Inherited solution from {p}^{inherited_from}.",
                            flush=True,
                        )

                    results_file.write(
                        f"{label}: inherited from {p}^{inherited_from}\n"
                    )
                    results_file.flush()
                    continue

                field = ExtensionField(q)
                result = smart_search(field)
                # The polynomial records which representation of F_q we used.
                polynomial = field.gf.irreducible_poly

                if result is None:
                    if verbose:
                        print(f"  No solution.", flush=True)

                    no_solution_extension_orders.append(q)
                    results_file.write(f"{label}: None\n")
                else:
                    if verbose:
                        print(f"  Found solution.", flush=True)

                    solved_exponents.append(exponent)
                    A, x, y = result
                    results_file.write(
                        f"{label}: base={field.format(A)}, "
                        f"steps=({field.format(x)}, {field.format(y)}); "
                        f"polynomial={polynomial}\n"
                    )
                # Write each result immediately,
                # so any interrupted long run retains all completed fields.
                results_file.flush()

    return no_solution_extension_orders


def main():
    """Run both stages and report the unresolved fields and elapsed time."""
    args = parse_args()
    # Ensure the destination exists before the search functions open files in it.
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    start_time = perf_counter()

    print(
        f"Beginning search through odd prime order fields below {args.order_bound}...",
        flush=True,
    )
    prime_start_time = perf_counter()
    no_solution_primes = prime_search(args.order_bound, verbose=args.verbose)
    prime_elapsed = perf_counter() - prime_start_time

    print(f"Completed prime-field search in {prime_elapsed:.2f} seconds.")
    print(f"{len(no_solution_primes)} odd prime fields had no 3x3 GAP of squares:")
    print(f"  {no_solution_primes}", flush=True)

    if no_solution_primes:
        print(
            "Beginning search through odd extension fields "
            "for unresolved characteristics...",
            flush=True,
        )
        extension_start_time = perf_counter()
        no_solution_extension_orders = extension_search(
            args.order_bound,
            no_solution_primes,
            verbose=args.verbose,
        )
        extension_elapsed = perf_counter() - extension_start_time

        print(
            f"Completed extension-field search in {extension_elapsed:.2f} seconds."
        )
        print(
            f"{len(no_solution_extension_orders)} odd extension fields had no "
            "3x3 GAP of squares:"
        )
        print(f"  {no_solution_extension_orders}")
    else:
        print("No extension fields needed to be searched.")

    elapsed = perf_counter() - start_time
    print(f"Completed full search in {elapsed:.2f} seconds.")


# Importing this file exposes its functions to tests without starting a search.
# Running it as a program enters the command-line workflow above.
if __name__ == "__main__":
    main()
