"""Arithmetic for the field of integers modulo a prime number.

The search programs use this class so that the same search procedures can
work with both prime fields and extension fields. An element is represented
by its remainder from 0 through p-1.
"""


class PrimeField:
    """Represent and perform the arithmetic of F_p, where p is prime."""

    def __init__(self, p):
        self.p = p

    def __call__(self, value):
        """Reduce an integer to its canonical representative in F_p."""
        return value % self.p

    def elements(self):
        """List the representatives of all p elements of the field."""
        return range(self.p)
    
    def square_elements(self):
        """List the square elements of the field without repeats."""
        seen = set()
        for x in self.elements():
            square = x**2
            if square in seen:
                continue
            seen.add(square)
            yield square

    def is_square(self, a):
        """Say whether ``a`` is a square in F_p, including zero.

        The search is concerned with squared lengths, so we count zero as a
        square even though Euler's criterion applies only to nonzero elements.
        """
        a = self(a)
        if a == 0:
            return True

        # Euler's criterion: for odd prime p, a^((p-1)/2) is 1 exactly when
        # the nonzero residue a is a quadratic residue. Python's three-argument
        # pow performs this exponentiation while reducing modulo p throughout.
        exponent = (self.p - 1) // 2
        return pow(a, exponent, self.p) == 1

    def key(self, value):
        """Give an element a standard integer label for comparisons."""
        return self(value)

    def format(self, value):
        """Write an element in the usual integer notation for F_p."""
        return str(self(value))
