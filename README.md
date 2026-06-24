# finitefield-quarry

Search code for 3x3 magic squares of distinct squares over finite fields.

The current code focuses on prime fields `F_p`. For each prime `p` below a configured limit, it searches for a 3x3 magic square whose nine entries are distinct square elements of `F_p`.

A result is written in row-major form:

```text
p: A B C | D E F | G H I
```

or:

```text
p: None
```

when no magic square of squares is found.


## Project Layout

```text
finitefield-quarry/
├── scripts/
│   └── prime_order_mss.py
├── results/
│   └── prime_order_mss.txt
├── src/
│   └── ffquarry/
│       ├── __init__.py
│       └── search_tools.py
├── pyproject.toml
└── README.md
```

`ffquarry` is the importable library code. The scripts in `scripts/` are computational entry points that use the library.


## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project in editable mode:

```bash
pip install -e .
```

This installs the `ffquarry` package and its dependencies.


## Running the Prime-Order Search

Run:

```bash
python scripts/prime_order_mss.py
```

The script writes results to:

```text
results/prime_order_mss.txt
```

It also prints a terminal summary like:

```text
Completed search in X seconds.
Average search time: Y milliseconds.
Z finite fields had no MSS: [...]
```


## Search Methods

`quick_search(p)` searches only normalized magic squares of the form:

```text
A   B   49
D   25  F
1   H   I
```

`full_search(p)` searches a broader parametrized family. It fixes the center entry `E` to `0` and then `1`, iterates over square choices for `A` and `C`, and derives the remaining entries from the 3x3 magic-square relations.


## Notes

The project currently uses integer arithmetic modulo primes. Future work may add support for non-prime finite fields, such as fields of order `4`, `8`, or `9`, likely using the `galois` package.
