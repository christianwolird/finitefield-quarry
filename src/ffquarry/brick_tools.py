"""Search tools for perfect Euler bricks over finite fields.

A brick is represented by its side-square values.  For example, ``(1, B,
C)`` represents side lengths whose squares are 1, B, and C.  It is perfect
when every subset sum of those values is a square and all subset sums are
distinct.
"""


# Small primitive integer Euler bricks.  Their face diagonals are integral,
# but their space diagonals are not.  After reduction into a finite field the
# space diagonal can become a square, making one of these a useful 3D seed for
# a 4D search.  The examples are listed at
# https://en.wikipedia.org/wiki/Euler_brick#Examples.
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
    """Return whether ``elements`` have distinct values in ``field``."""
    keys = [field.key(element) for element in elements]
    return len(set(keys)) == len(keys)


def subset_sums(field, side_squares):
    """Return all subset sums of ``side_squares``, beginning with zero."""
    sums = [field(0)]

    for value in side_squares:
        side_square = field(value)
        sums.extend(field(total + side_square) for total in tuple(sums))

    return sums


def is_perfect_brick(field, side_squares):
    """Check that all subset sums are distinct squares in ``field``."""
    sums = subset_sums(field, side_squares)
    return are_distinct(field, sums) and all(
        field.is_square(value) for value in sums
    )


def _square_values(field):
    """Yield square values lazily, using the field's Euler-criterion check."""

    for value in field.elements():
        candidate = field(value)
        if field.is_square(candidate):
            yield candidate


def _valid_extension(field, old_sums, new_sums):
    """Check only the new subset sums introduced by one additional side."""
    seen = {field.key(value) for value in old_sums}

    for value in new_sums:
        key = field.key(value)
        if key in seen:
            return False
        seen.add(key)

    # The field wrappers use Euler's criterion here; no square table is built.
    return all(field.is_square(value) for value in new_sums)


def extend_brick(field, side_squares):
    """Find one square side that makes ``side_squares`` a larger brick.

    The supplied sides must already form a perfect brick.  ``None`` is
    returned when the seed is invalid or no extension exists.
    """
    sides = tuple(field(value) for value in side_squares)
    old_sums = subset_sums(field, sides)

    if not are_distinct(field, old_sums):
        return None
    if not all(field.is_square(value) for value in old_sums):
        return None

    for candidate in _square_values(field):
        new_sums = tuple(field(total + candidate) for total in old_sums)
        if _valid_extension(field, old_sums, new_sums):
            return sides + (candidate,)

    return None


def three_dimensional_quick_search(field):
    """Search 3D bricks after fixing two sides to the 3-4-5 triple."""
    side_squares = (field(3) ** 2, field(4) ** 2)
    return extend_brick(field, side_squares)


def four_dimensional_quick_search(field):
    """Try extending reduced non-perfect integer Euler bricks to 4D."""
    for integer_sides in EULER_BRICK_SEEDS:
        side_squares = tuple(field(side) ** 2 for side in integer_sides)
        result = extend_brick(field, side_squares)
        if result is not None:
            return result

    return None


def full_search(field, dimensions=3):
    """Exhaustively search normalized perfect bricks of a given dimension.

    Scaling by the inverse of a nonzero side-square lets us fix the first
    side-square to 1.  The remaining sides are added recursively, rejecting a
    branch as soon as one of its new subset sums is repeated or is not square.
    Only dimensions 3 and 4 are exposed because those are the searches this
    project records.
    """
    if dimensions not in (3, 4):
        raise ValueError("dimensions must be 3 or 4")

    one = field(1)
    initial_sides = (one,)
    initial_sums = (field(0), one)
    visited = {depth: set() for depth in range(2, dimensions + 1)}

    def search(sides, sums):
        if len(sides) == dimensions:
            return sides

        next_depth = len(sides) + 1

        for candidate in _square_values(field):
            candidate_sides = sides + (candidate,)
            side_keys = frozenset(field.key(value) for value in candidate_sides)

            # Side order is immaterial.  This also rejects a repeated side.
            if len(side_keys) != next_depth:
                continue
            if side_keys in visited[next_depth]:
                continue
            visited[next_depth].add(side_keys)

            new_sums = tuple(field(total + candidate) for total in sums)
            if not _valid_extension(field, sums, new_sums):
                continue

            result = search(candidate_sides, sums + new_sums)
            if result is not None:
                return result

        return None

    return search(initial_sides, initial_sums)


def three_dimensional_full_search(field):
    return full_search(field, dimensions=3)


def four_dimensional_full_search(field):
    return full_search(field, dimensions=4)


def three_dimensional_smart_search(field):
    """Try the Pythagorean seed, then the normalized exhaustive search."""
    result = three_dimensional_quick_search(field)
    if result is not None:
        return result

    return three_dimensional_full_search(field)


def four_dimensional_smart_search(field):
    """Try integer Euler-brick seeds, then the exhaustive 4D search."""
    result = four_dimensional_quick_search(field)
    if result is not None:
        return result

    return four_dimensional_full_search(field)


def quick_search(field, dimensions=3):
    """Dispatch to the quick search for dimension 3 or 4."""
    if dimensions == 3:
        return three_dimensional_quick_search(field)
    if dimensions == 4:
        return four_dimensional_quick_search(field)
    raise ValueError("dimensions must be 3 or 4")


def smart_search(field, dimensions=3):
    """Dispatch to the smart search for dimension 3 or 4."""
    if dimensions == 3:
        return three_dimensional_smart_search(field)
    if dimensions == 4:
        return four_dimensional_smart_search(field)
    raise ValueError("dimensions must be 3 or 4")


# Concise aliases are convenient for callers that use the result-file naming.
three_dim_quick_search = three_dimensional_quick_search
three_dim_full_search = three_dimensional_full_search
three_dim_smart_search = three_dimensional_smart_search
four_dim_quick_search = four_dimensional_quick_search
four_dim_full_search = four_dimensional_full_search
four_dim_smart_search = four_dimensional_smart_search
quick_search_3d = three_dimensional_quick_search
full_search_3d = three_dimensional_full_search
smart_search_3d = three_dimensional_smart_search
quick_search_4d = four_dimensional_quick_search
full_search_4d = four_dimensional_full_search
smart_search_4d = four_dimensional_smart_search
