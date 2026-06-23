def legendre(a, p):
    """Return the Legendre symbol of a modulo p.

    For odd prime p, this returns:
      1     if a is a nonzero quadratic residue modulo p
      p - 1 if a is a non-residue, representing -1 modulo p
      0     if a == 0 modulo p
    """
    return pow(a, (p - 1) // 2, p)


def is_square(a, p):
    """Return whether a is a square modulo p, including 0."""
    return a % p == 0 or legendre(a, p) == 1


def are_distinct_squares(entries, p):
    """Return whether every entry is distinct and a square in F_p."""
    return len(set(entries)) == len(entries) and all(is_square(x, p) for x in entries)


def quick_search(p):
    """Search for a 3x3 magic square of squares over F_p.

    This only searches for magic squares of the form:

        A   B   49
        D   25  F
        1   H   I

    Every row, column, and diagonal is constrained to sum to 3E = 75.
    Returns the entries in row-major order, or None if no solution is found.
    """
    C = 49 % p
    E = 25 % p
    G = 1

    magic_sum = (3 * E) % p
    seen_A_values = set()

    for a in range(p):
        A = a**2 % p
        if A in seen_A_values:
            continue
        seen_A_values.add(A)

        B = (magic_sum - C - A) % p
        D = (magic_sum - G - A) % p
        F = (magic_sum - E - D) % p
        H = (magic_sum - E - B) % p
        I = (magic_sum - C - F) % p

        entries = [A, B, C, D, E, F, G, H, I]
        if are_distinct_squares(entries, p):
            return entries

    return None


def full_search(p):
    """Brute-force 3x3 magic squares of distinct squares over F_p.

    The search fixes the center entry to E = 0 and then E = 1. For each
    center value, it iterates over top-left and top-right entries A and C.
    The remaining entries are forced by the 3x3 magic square relations:

        A   B   C
        D   E   F
        G   H   I

    Every row, column, and diagonal sums to 3E.

    This search is certain to find a magic square of squares if one exists
    in F_p, since up to re-scaling, we can assume the E is either 0 or 1.

    Returns the entries in row-major order, or None if no solution is found.
    """
    for E in [0, 1]:
        seen_A_values = set()

        for a in range(p):
            A = a**2 % p
            if A in seen_A_values:
                continue
            seen_A_values.add(A)

            if A == E:
                continue

            seen_C_values = set()

            for c in range(p):
                C = c**2 % p
                if C in seen_C_values:
                    continue
                seen_C_values.add(C)

                if C in {A, E}:
                    continue

                B = (3 * E - A - C) % p
                D = (E - A + C) % p
                F = (E + A - C) % p
                G = (2 * E - C) % p
                H = (A + C - E) % p
                I = (2 * E - A) % p

                entries = [A, B, C, D, E, F, G, H, I]
                if are_distinct_squares(entries, p):
                    return entries

    return None
