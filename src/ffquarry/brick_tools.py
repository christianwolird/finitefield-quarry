"""Search tools for strong perfect Euler bricks over finite fields.

A brick is represented by its side-square values.  For example, ``(1, B,
C)`` represents side lengths whose squares are 1, B, and C. It is perfect
when every subset sum is a square, and strong when those sums are all
distinct. The searches here require both properties.

The command-line program that chooses fields and saves results is
``scripts/brick_search.py``. The functions in this file perform the actual
mathematical searches, using a quick search with known examples before trying
an exhaustive search.
"""


# Starting examples for the 4D search: these integer Euler bricks have
# integer face diagonals but noninteger space diagonals. After reducing their
# values into a finite field, a space diagonal may become a square there.
# Source: https://en.wikipedia.org/wiki/Euler_brick#Examples.
EULER_BRICK_SEEDS = (
    (44, 117, 240),
    (85, 132, 720),
    (140, 480, 693),
    (160, 231, 792),
    (187, 1020, 1584),
    (195, 748, 6336),
    (240, 252, 275),
    (429, 880, 2340),
    (495, 4888, 8160),
    (528, 5796, 6325),
)


def are_distinct(field, elements):
    """Return whether ``elements`` have distinct values in ``field``.

    Extension-field objects cannot themselves be placed in a Python set, so
    the field wrapper supplies a unique integer key for each field element.
    """
    keys = [field.key(element) for element in elements]
    return len(set(keys)) == len(keys)


# Starting with the empty choice (sum zero), add each side-square to the sums
# already formed. This lists one sum for every subset of the chosen sides.
def subset_sums(field, side_squares):
    """Return all subset sums of ``side_squares``, including the empty sum.

    After k sides, the list has 2^k entries, one for each subset. When a new
    side-square s is introduced, the subsets divide into those omitting s
    (the old list) and those containing s (the old list plus s).
    """
    sums = [field(0)]

    for value in side_squares:
        side_square = field(value)
        sums.extend(field(total + side_square) for total in tuple(sums))

    return sums


def is_strong_perfect_brick(field, side_squares):
    """Check that the brick is both perfect and strong in ``field``.

    Perfection requires every subset sum of the side squares to be a square;
    strength requires those sums to be distinct. Both conditions are tested.
    """
    sums = subset_sums(field, side_squares)
    return are_distinct(field, sums) and all(
        field.is_square(value) for value in sums
    )


def is_strong_perfect_extension(field, old_sums, new_sums):
    """Check only the new subset sums introduced by one additional side.

    The caller has already established that ``old_sums`` are distinct
    squares. The union is therefore a valid larger brick exactly when every
    new sum is a square and none coincides with an old or earlier new sum.
    """
    seen = {field.key(value) for value in old_sums}

    for value in new_sums:
        key = field.key(value)
        if key in seen:
            return False
        seen.add(key)

    # The field wrappers use Euler's criterion here.
    return all(field.is_square(value) for value in new_sums)


def extend_brick(field, side_squares):
    """Find one square side that makes ``side_squares`` a larger brick.

    The supplied sides must already form a strong perfect brick. ``None`` is
    returned when the seed is invalid or no extension exists.
    """
    # First reject an invalid starting brick; then try each possible new
    # side-square until its newly created sums pass both required tests.
    old_sums = subset_sums(field, side_squares)

    if not are_distinct(field, old_sums):
        return None
    if not all(field.is_square(value) for value in old_sums):
        return None

    for candidate in field.square_elements():
        # The 2^k new subsets are exactly the old subsets with the candidate
        # side adjoined. No other subset sums arise when one side is added.
        new_sums = tuple(field(total + candidate) for total in old_sums)
        if is_strong_perfect_extension(field, old_sums, new_sums):
            return side_squares + (candidate,)

    return None


def quick_search_3d(field):
    """Search 3D bricks after fixing two sides to the 3-4-5 triple."""
    # The 3-4-5 right triangle gives two sides whose pairwise diagonal is
    # already a square. Search only for a third side to complete the brick.
    side_squares = (field(3) ** 2, field(4) ** 2)
    return extend_brick(field, side_squares)


def quick_search_4d(field):
    """Try extending reduced non-perfect integer Euler bricks to 4D."""
    # Try each known three-sided Euler brick after reducing its lengths into
    # this field. A successful fourth side completes the 4D example.
    for integer_sides in EULER_BRICK_SEEDS:
        side_squares = tuple(field(side) ** 2 for side in integer_sides)
        result = extend_brick(field, side_squares)
        if result is not None:
            return result

    return None


def full_search(field, dimension=3):
    """Exhaustively search normalized strong perfect bricks of a dimension.

    Scaling by the inverse of a nonzero side-square lets us fix the first
    side-square to 1.  The remaining sides are added recursively, rejecting a
    branch as soon as one of its new subset sums is repeated or is not square.
    Only dimensions 3 and 4 are exposed because those are the searches this
    project records.
    """
    if dimension not in (3, 4):
        raise ValueError("dimension must be 3 or 4")

    # Strength rules out a zero side-square, because it would equal the empty
    # subset sum. Scaling all side-squares by the inverse of any chosen side
    # square preserves both being squares and being distinct. We can therefore
    # put that side first, set it to 1, and search only for the remaining sides.
    one = field(1)
    initial_sides = (one,)
    initial_sums = (field(0), one)
    # A brick is unchanged by permuting its sides. At each depth, remember the
    # unordered set of chosen sides so equivalent permutations are explored
    # only once. The depth is kept separately because a partial brick and a
    # longer brick belong to different stages of the recursion.
    visited = {depth: set() for depth in range(2, dimension + 1)}

    # Add one side at a time. As soon as it creates a nonsquare or repeated
    # subset sum, abandon that choice instead of exploring it further.
    def search(sides, sums):
        if len(sides) == dimension:
            return sides

        next_depth = len(sides) + 1

        for candidate in field.square_elements():
            candidate_sides = sides + (candidate,)
            side_keys = frozenset(field.key(value) for value in candidate_sides)

            # Side order is immaterial.  This also rejects a repeated side.
            if len(side_keys) != next_depth:
                continue
            if side_keys in visited[next_depth]:
                continue
            visited[next_depth].add(side_keys)

            new_sums = tuple(field(total + candidate) for total in sums)
            if not is_strong_perfect_extension(field, sums, new_sums):
                continue

            result = search(candidate_sides, sums + new_sums)
            if result is not None:
                return result

        return None

    return search(initial_sides, initial_sums)


def full_search_3d(field):
    """Run the normalized exhaustive search for three side squares."""
    return full_search(field, dimension=3)


def full_search_4d(field):
    """Run the normalized exhaustive search for four side squares."""
    return full_search(field, dimension=4)


def smart_search_3d(field):
    """Try the Pythagorean seed, then the normalized exhaustive search."""
    result = quick_search_3d(field)
    if result is not None:
        return result

    return full_search_3d(field)


def smart_search_4d(field):
    """Try integer Euler-brick seeds, then the exhaustive 4D search."""
    result = quick_search_4d(field)
    if result is not None:
        return result

    return full_search_4d(field)


def quick_search(field, dimension=3):
    """Dispatch to the quick search for dimension 3 or 4."""
    if dimension == 3:
        return quick_search_3d(field)
    if dimension == 4:
        return quick_search_4d(field)
    raise ValueError("dimension must be 3 or 4")


def smart_search(field, dimension=3):
    """Dispatch to the smart search for dimension 3 or 4."""
    if dimension == 3:
        return smart_search_3d(field)
    if dimension == 4:
        return smart_search_4d(field)
    raise ValueError("dimension must be 3 or 4")
