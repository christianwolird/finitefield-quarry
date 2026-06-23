from sympy import primerange

MAGIC_SUM = 75
PRIME_LIMIT = 400_000


def legendre(a, p):
    """Return the Legendre symbol of a modulo p.

    For odd prime p, this returns:
      1     if a is a nonzero quadratic residue modulo p
      p - 1 if a is a non-residue, representing -1 modulo p
      0     if a == 0 modulo p
    """
    return pow(a, (p - 1) // 2, p)


def is_square(a, p):
    return legendre(a, p) == 1


for p in primerange(PRIME_LIMIT):
    solution = None
    seen_a_values = set()

    for a in range(2, p):
        # Choose the top-left entry as a square, considering only one
        # representative per residue class.
        A = a**2 % p
        if A in seen_a_values:
            continue
        seen_a_values.add(A)

        # Complete the 3x3 magic square modulo p:
        #
        #   A   B   49
        #   D   25  F
        #   1   H   I
        #
        # Every row, column, and diagonal is constrained to sum to MAGIC_SUM.
        B = (MAGIC_SUM - 49 - A) % p
        D = (MAGIC_SUM - 1 - A) % p
        F = (MAGIC_SUM - 25 - D) % p
        H = (MAGIC_SUM - 25 - B) % p
        I = (MAGIC_SUM - 49 - F) % p

        entries = [A, B, 49 % p, D, 25 % p, F, 1, H, I]

        # Require a proper magic square over F_p: all entries must be distinct
        # field elements and each must be a nonzero square modulo p.
        if len(set(entries)) < 9:
            continue
        if all(is_square(x, p) for x in entries):
            solution = entries
            break

    if solution is None:
        print(p)
