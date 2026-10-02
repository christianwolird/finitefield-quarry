"""Algorithms for finding 3-by-3 progressions of distinct squares.

For a base A and steps x and y, the entry in row i and column j is

    A + i*x + j*y,    0 <= i,j <= 2.

Thus choosing A and the adjacent entries B=A+y and D=A+x determines all nine
entries. A valid result requires those entries to be pairwise distinct and to
be squares in the finite field.

The command-line program is in ``scripts/gap_search.py``. The functions here
do the mathematical search: they construct candidate arrays, check their
entries, and return the base and the two common differences when successful.
"""


def are_distinct(field, elements):
    """Return whether no two entries represent the same field element."""
    # The field decides how to turn an element into a hashable representative.
    keys = [field.key(element) for element in elements]
    return len(set(keys)) == len(keys)


def smart_search(field):
    """Try a quick special-case search, then the exhaustive search if needed.

    The quick search can save substantial work but doesn't find every
    progression. Falling back to ``full_search`` is what makes a final
    ``None`` result exhaustive.
    """
    result = quick_search(field)
    if result is not None:
        return result

    return full_search(field)


def quick_search(field):
    """Search a useful fixed family of 3x3 GAPs over ``field``.

    This only searches for a GAP of the form:

        1   25  49
        D   E   F
        G   H   I

    Returns (A, x, y), where x is the row step and y is the column step,
    or None if no solution is found.
    """
    # Fix the first row to 1, 25, 49, a progression with square entries.
    # The second row's first entry D is varied; the other entries are then
    # forced by the requirement that rows and columns have constant steps.
    A = field(1)
    B = field(25)
    C = field(49)

    seen_D_values = set()

    for d in field.elements():
        D = field(d**2)
        # d and -d give the same square, so only try each square value once.
        D_key = field.key(D)
        if D_key in seen_D_values:
            continue
        seen_D_values.add(D_key)

        # Since D is directly below A, their difference is the row step x.
        diff = D - A

        # Adding x once gives the middle row; adding it twice gives the last.
        # The top row already has column step 24 because 25-1 = 49-25.
        E = field(B + diff)
        F = field(C + diff)

        G = field(A + 2 * diff)
        H = field(B + 2 * diff)
        I = field(C + 2 * diff)

        gap_elements = [A, B, C, D, E, F, G, H, I]
        if not are_distinct(field, gap_elements):
            continue

        # A, B, C, and D were constructed as squares. Only the five derived
        # entries still require square tests.
        if all(field.is_square(element) for element in [E, F, G, H, I]):
            return A, diff, B - A

    return None


def full_search(field):
    """Exhaustively search normalized 3x3 GAPs over the given `field`.

    The search fixes the top-left entry to A = 1 and then A = 0. It
    iterates over square values for B and D. The remaining entries are
    forced by the 3x3 GAP structure.

        A   B   C
        D   E   F
        G   H   I

    This search is certain to find a GAP of distinct squares if one exists:
    up to rescaling, A is either 0 or 1. If A=a^2 is a non-zero square,
    we multiply the entire array by A^(-1)=(a^(-1))^2; square status,
    equalities, and the additive progression relations are all preserved.

    Returns (A, x, y), where x is the row step and y is the column step,
    or None if no solution is found.
    """
    for A in [field(1), field(0)]:
        seen_B_values = set()

        for b in field.elements():
            B = field(b**2)
            # Check if we've tried this value of B already.
            # We need this check since b^2 and (-b)^2 are equal.
            B_key = field.key(B)
            if B_key in seen_B_values:
                continue
            seen_B_values.add(B_key)

            if B == A:
                continue

            # B is the entry to the right of A, so y is forced. The third
            # entry of the first row must consequently be C=A+2y.
            y = B - A
            C = field(A + 2 * y)

            # C depends only on A and B, so reject this whole B-branch early
            # if C is non-square.
            if not field.is_square(C):
                continue

            seen_D_values = set()

            for d in field.elements():
                D = field(d**2)
                # Similarly, check if we've tried this value of D already.
                D_key = field.key(D)
                if D_key in seen_D_values:
                    continue
                seen_D_values.add(D_key)

                if D == A or D == B:
                    continue

                # D is the entry below A, so it similarly determines x. Once
                # A, B, and D are fixed, no choices remain for E through I.
                x = D - A

                E = field(D + y)
                F = field(D + 2 * y)

                G = field(A + 2 * x)
                H = field(A + 2 * x + y)
                I = field(A + 2 * x + 2 * y)

                gap_elements = [A, B, C, D, E, F, G, H, I]
                if not are_distinct(field, gap_elements):
                    continue

                # A, B, C, and D have already passed their square tests.
                if all(field.is_square(element) for element in [E, F, G, H, I]):
                    return A, x, y

    return None
