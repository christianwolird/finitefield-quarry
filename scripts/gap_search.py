import argparse
from pathlib import Path
from time import perf_counter

from sympy import primerange

from ffquarry.gap_tools import smart_search
from ffquarry.power_field import PowerField
from ffquarry.prime_field import PrimeField

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "gaps"
PRIME_RESULTS_PATH = RESULTS_DIR / "prime_field_solutions.txt"
POWER_RESULTS_PATH = RESULTS_DIR / "power_field_solutions.txt"


def parse_args():
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
            "Print each unresolved characteristic and prime-power field order "
            "as it is searched."
        ),
    )
    parser.add_argument(
        "order_bound",
        type=int,
        help="Search finite fields with order below this bound.",
    )
    return parser.parse_args()


def prime_search(order_bound, verbose=False):
    no_solution_primes = []

    with open(PRIME_RESULTS_PATH, "w", encoding="utf-8") as results_file:
        # Prime fields with a solution also settle all extension fields of
        # the same characteristic, so only failures move on to power_search().
        for p in primerange(order_bound):
            if p == 2:
                continue

            field = PrimeField(p)
            result = smart_search(field)

            if result is None:
                no_solution_primes.append(p)
                if verbose:
                    print(f"  Prime field of order {p} has no solution.", flush=True)

                results_file.write(f"{p}: None\n")
                continue

            A, x, y = result
            results_file.write(
                f"{p}: base={field.format(A)}, "
                f"steps=({field.format(x)}, {field.format(y)})\n"
            )

    return no_solution_primes


def prime_power_exponents(p, order_bound):
    exponent = 2
    order = p * p

    # Start at p^2; the prime field p was already handled in prime_search().
    while order < order_bound:
        yield exponent
        exponent += 1
        order *= p


def power_search(order_bound, no_solution_primes, verbose=False):
    no_solution_power_orders = []

    with open(POWER_RESULTS_PATH, "w", encoding="utf-8") as results_file:
        for p in no_solution_primes:
            if verbose:
                print(
                    f"Searching prime-power fields of characteristic {p}...",
                    flush=True,
                )

            solved_exponents = []

            for exponent in prime_power_exponents(p, order_bound):
                q = p**exponent
                label = f"{p}^{exponent}"
                inherited_from = None

                # F_{p^a} embeds in F_{p^b} exactly when a divides b.
                for solved_exponent in solved_exponents:
                    if exponent % solved_exponent == 0:
                        inherited_from = solved_exponent
                        break

                if verbose:
                    print(f"Checking field of order {label}={q}...", flush=True)

                if inherited_from is not None:
                    if verbose:
                        print(f"  Inherited solution from {p}^{inherited_from}.", flush=True)

                    results_file.write(f"{label}: inherited from {p}^{inherited_from}\n")
                    results_file.flush()
                    continue

                field = PowerField(q)
                result = smart_search(field)
                polynomial = field.gf.irreducible_poly

                if result is None:
                    if verbose:
                        print(f"  No solution.", flush=True)

                    no_solution_power_orders.append(q)
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
                results_file.flush()

    return no_solution_power_orders


def main():
    args = parse_args()
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
            "Beginning search through odd prime-power order fields "
            "for unresolved characteristics...",
            flush=True,
        )
        power_start_time = perf_counter()
        no_solution_power_orders = power_search(
            args.order_bound,
            no_solution_primes,
            verbose=args.verbose,
        )
        power_elapsed = perf_counter() - power_start_time

        print(f"Completed power-field search in {power_elapsed:.2f} seconds.")
        print(
            f"{len(no_solution_power_orders)} odd prime-power fields had no "
            "3x3 GAP of squares:"
        )
        print(f"  {no_solution_power_orders}")
    else:
        print("No prime-power fields needed to be searched.")

    elapsed = perf_counter() - start_time
    print(f"Completed full search in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    main()
