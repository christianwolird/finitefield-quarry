# finitefield-quarry

Search code for 3x3 generalized arithmetic progressions of distinct squares over finite fields.

A 3x3 GAP is written as

```text
A        A + y        A + 2y
A + x    A + x + y    A + x + 2y
A + 2x   A + 2x + y   A + 2x + 2y
```

The search records a solution by its base and two common differences:

```text
base=A, steps=(x, y)
```

where `x` is the row step and `y` is the column step.


## Project Layout

```text
finitefield-quarry/
├── scripts/
│   └── gap_search.py
├── results/
│   └── gaps/
│       ├── prime_field_solutions.txt
│       └── power_field_solutions.txt
├── src/
│   └── ffquarry/
│       ├── __init__.py
│       ├── gap_tools.py
│       ├── power_field.py
│       └── prime_field.py
├── pyproject.toml
└── README.md
```

`ffquarry` contains the finite-field wrappers and GAP search code. `scripts/gap_search.py` is the main computational entry point.


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

This installs the package dependencies, including `sympy` and `galois`.


## Running the Search

Run the search with an order bound:

```bash
python scripts/gap_search.py 400000
```

For more detailed progress during the prime-power search, use:

```bash
python scripts/gap_search.py 400000 --verbose
```

The script skips characteristic `2`.

It first searches odd prime fields below the order bound. If a solution is found over `F_p`, then all extension fields of characteristic `p` are considered settled by inclusion, so no prime-power fields of that characteristic are searched.

For prime fields with no solution, the script searches fields of order `p^a` with `a >= 2` and `p^a` below the bound. If a solution is found over `F_{p^a}`, then fields `F_{p^b}` with `a | b` inherit that solution and are not searched separately.


## Output Files

Prime-field results are written to:

```text
results/gaps/prime_field_solutions.txt
```

Example lines:

```text
29: base=1, steps=(4, 24)
31: None
```

Prime-power results are written to:

```text
results/gaps/power_field_solutions.txt
```

Example lines:

```text
3^2: None
3^4: base=1, steps=(α^3 + α^2 + 1, 2); polynomial=x^4 + 2x^3 + 2
3^8: inherited from 3^4
```

For prime-power fields, entries are printed in polynomial notation. The `polynomial=...` field records the irreducible polynomial used by `galois` to construct that finite field.


## Search Methods

`smart_search(field)` first tries `quick_search(field)` and falls back to `full_search(field)` only if needed.

`quick_search(field)` searches the normalized family

```text
1   25  49
D   E   F
G   H   I
```

where `D` varies over square values.

`full_search(field)` searches the normalized 3x3 GAP family by fixing `A = 1` and then `A = 0`, iterating over square values for `B` and `D`, and deriving the rest of the GAP from the row and column steps.

Both searches return either `None` or

```python
(A, x, y)
```

where `x = D - A` and `y = B - A`.


## Field Wrappers

`PrimeField(p)` uses ordinary Python integers modulo `p`.

`PowerField(q)` wraps `galois.GF(q)` for prime-power fields. Arithmetic is done with `galois` field elements, while result output uses polynomial notation for readability.
