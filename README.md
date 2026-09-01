# finitefield-quarry

Search code for 3x3 generalized arithmetic progressions and 3D or 4D perfect Euler bricks of distinct squares over finite fields.

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
├── verification/
│   ├── brick_coverage.py
│   ├── brick_verify.py
│   ├── gap_coverage.py
│   └── gap_verify.py
├── scripts/
│   ├── brick_search.py
│   └── gap_search.py
├── results/
│   ├── bricks/
│   │   ├── four_dim/
│   │   │   ├── power_field_solutions.txt
│   │   │   └── prime_field_solutions.txt
│   │   └── three_dim/
│   │       ├── power_field_solutions.txt
│   │       └── prime_field_solutions.txt
│   └── gaps/
│       ├── prime_field_solutions.txt
│       └── power_field_solutions.txt
├── src/
│   └── ffquarry/
│       ├── __init__.py
│       ├── brick_tools.py
│       ├── gap_tools.py
│       ├── power_field.py
│       └── prime_field.py
├── tests/
│   └── test_brick_tools.py
├── pyproject.toml
└── README.md
```

`ffquarry` contains the finite-field wrappers and search code. The two scripts are the computational entry points for GAP and brick searches.


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

### GAPs

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

### Perfect bricks

The brick dimension is required because 3D and 4D searches will generally use very different order bounds. Search one dimension at a time with:

```bash
python scripts/brick_search.py 400000 --dimension 3
```

To search 4D bricks or print each field as it is searched, use:

```bash
python scripts/brick_search.py 400000 --dimension 4 --verbose
```

The brick script also skips characteristic `2` and applies the same prime-field and extension-field inheritance rules as the GAP search.


## Output Files

### GAPs

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

### Perfect bricks

Each dimension has separate prime-field and prime-power result files:

```text
results/bricks/three_dim/prime_field_solutions.txt
results/bricks/three_dim/power_field_solutions.txt
results/bricks/four_dim/prime_field_solutions.txt
results/bricks/four_dim/power_field_solutions.txt
```

A brick is recorded by side-square values, not by a choice of square roots:

```text
101: side_squares=(1, 36, 95, 87)
```

Every one of the 16 subset sums of this example is a distinct square in `F_101`. Prime-power results additionally record the field's irreducible polynomial.


## Verifying Results

Verify every explicit witness and every extension-field inheritance reference:

```bash
python verification/gap_verify.py
python verification/brick_verify.py
```

The GAP verifier reconstructs each 3x3 progression and checks that its nine
entries are distinct squares with the recorded row and column steps. The brick
verifier checks that all `2^d` subset sums of each `d`-dimensional result are
distinct squares. Extension-field coordinates are interpreted using the
irreducible polynomial stored on the same result line.

Check that the result files cover the searches' checked-in order bounds:

```bash
python verification/gap_coverage.py
python verification/brick_coverage.py
```

The default bounds are 350,000 for GAPs, 1,000 for 3D bricks, and 700,000 for
4D bricks. A different GAP bound may be passed positionally. For bricks, use
`--dimension 3|4 --order-bound BOUND`. Coverage follows the search's inclusion
rule: a solution over `F_p` covers every extension of characteristic `p`, while
an unresolved prime requires an explicit entry for every power below the bound.


## Search Methods

### GAPs

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

### Perfect bricks

For side-square values `(A, B, C)`, `subset_sums()` constructs

```text
0, A, B, A+B, C, A+C, B+C, A+B+C
```

and `is_perfect_brick()` requires all eight values to be squares and distinct. A 4D brick is checked in the same way with all 16 subset sums.

The normalized exhaustive search fixes the first side-square to `1`, then adds square side values one at a time. It rejects a branch as soon as a newly introduced subset sum is repeated or fails the field wrapper's Euler-criterion test. Candidate squares are tested lazily; the search does not construct a table of all quadratic residues.

The 3D smart search first fixes two side-squares to `3²` and `4²`, whose sum is `5²`, and varies the third. The 4D smart search first reduces several [small primitive integer Euler bricks](https://en.wikipedia.org/wiki/Euler_brick#Examples) into the field and tries to extend each with a fourth square side. In either dimension, the smart search falls back to the normalized exhaustive search if its integer seeds do not produce a result.


## Field Wrappers

`PrimeField(p)` uses ordinary Python integers modulo `p`.

`PowerField(q)` wraps `galois.GF(q)` for prime-power fields. Arithmetic is done with `galois` field elements, while result output uses polynomial notation for readability.
