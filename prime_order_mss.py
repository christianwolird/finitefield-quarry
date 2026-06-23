from time import perf_counter

from sympy import primerange

from search_tools import full_search, quick_search

PRIME_LIMIT = 400_000
RESULTS_PATH = "results.txt"


def find_mss(p):
    result = quick_search(p)
    if result is not None:
        return result

    return full_search(p)


def format_result(p, result):
    if result is None:
        return f"{p}: None"

    A, B, C, D, E, F, G, H, I = result
    return f"{p}: {A} {B} {C} | {D} {E} {F} | {G} {H} {I}"


def main():
    no_solution_primes = []
    search_times = []

    start_time = perf_counter()

    with open(RESULTS_PATH, "w", encoding="utf-8") as results_file:
        for p in primerange(PRIME_LIMIT):
            search_start = perf_counter()
            result = find_mss(p)
            search_times.append(perf_counter() - search_start)

            if result is None:
                no_solution_primes.append(p)

            results_file.write(format_result(p, result) + "\n")

    elapsed = perf_counter() - start_time
    average_ms = 1000 * sum(search_times) / len(search_times)

    print(f"Completed search in {elapsed:.2f} seconds.")
    print(f"Average search time: {average_ms:.3f} milliseconds.")
    print(
        f"{len(no_solution_primes)} finite fields had no MSS: "
        f"{no_solution_primes}"
    )


if __name__ == "__main__":
    main()
