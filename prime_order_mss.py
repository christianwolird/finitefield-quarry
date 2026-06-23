from sympy import primerange

from search_tools import quick_search, full_search

PRIME_LIMIT = 400_000


def main():
    for p in primerange(PRIME_LIMIT):
        result = quick_search(p)
        if result is None:
            result = full_search(p)
        if result is None:
            print(p)


if __name__ == "__main__":
    main()
