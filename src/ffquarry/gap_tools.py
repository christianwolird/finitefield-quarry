
def smart_search(field):
    result = quick_search(field)
    if result is not None:
        return result

    return full_search(field)


def quick_search(field):
    """Search for a 3x3 GAP of squares over F_p.

    This only searches for a GAP of the form:

        1   25  49
        D   E   F
        G   H   I

    Returns the entries in row-major order, or None if no solution is found.
    """
    A = field(1)
    B = field(25)
    C = field(49)

    seen_D_values = set()

    for d in field.elements():
        D = field(d**2)
        if D in seen_D_values:
            continue
        seen_D_values.add(D)

        diff = D - A

        E = field(B + diff)
        F = field(C + diff)

        G = field(A + 2 * diff)
        H = field(B + 2 * diff)
        I = field(C + 2 * diff)

        gap_elements = [A, B, C, D, E, F, G, H, I]
        if len(set(gap_elements)) != len(gap_elements):
            continue

        if all(field.is_square(element) for element in [E, F, G, H, I]):
            return gap_elements

    return None


def full_search(field):
    """Brute-force 3x3 GAP of distinct squares over F_p.

    The search fixes the top-left entry to A = 1 and then A = 0. It
    iterates over square values for B and D. The remaining entries are
    forced by the 3x3 GAP structure.

        A   B   C
        D   E   F
        G   H   I

    This search is certain to find a GAP of distinct squares if one exists
    in F_p, since up to re-scaling, we can assume the A is either 0 or 1.

    Returns the entries in row-major order, or None if no solution is found.
    """
    for A in [field(1), field(0)]:
        seen_B_values = set()

        for b in field.elements():
            B = field(b**2)
            if B in seen_B_values:
                continue
            seen_B_values.add(B)

            if B == A:
                continue

            seen_D_values = set()

            for d in field.elements():
                D = field(d**2)
                if D in seen_D_values:
                    continue
                seen_D_values.add(D)

                if D == A or D == B:
                    continue

                x = D - A
                y = B - A

                C = field(A + 2 * y)

                E = field(D + y)
                F = field(D + 2 * y)

                G = field(A + 2 * x)
                H = field(A + 2 * x + y)
                I = field(A + 2 * x + 2 * y)

                gap_elements = [A, B, C, D, E, F, G, H, I]
                if len(set(gap_elements)) != len(gap_elements):
                    continue

                if all(field.is_square(element) for element in [C, E, F, G, H, I]):
                    return gap_elements

    return None

