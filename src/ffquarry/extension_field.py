"""Arithmetic for finite fields whose size is a proper power of a prime.

The ``galois`` library constructs the field and performs the arithmetic. This
wrapper gives extension fields the same basic interface as ``PrimeField`` so
the search algorithms can run on either kind of field interchangably.
"""

import galois


class ExtensionField:
    """Represent F_q and provide the operations used by the searches."""

    def __init__(self, q):
        self.q = q
        self.gf = galois.GF(q)

        # Store the binary digits of (q-1)/2 from least to most significant.
        # is_square() reuses them for every candidate (instead of converting
        # the same exponent to binary on every call).
        self.square_exponent_bits = [
            bit == "1"
            for bit in reversed(bin((q - 1) // 2)[2:])
        ]

    def __call__(self, value):
        """Interpret a value as an element of this field.

        Existing field elements are kept as they are. 
        Ordinary integers are reduced and recaste.
        """
        if isinstance(value, self.gf):
            return value
        return self.gf(value % self.gf.characteristic)

    def elements(self):
        """Return the library's fixed enumeration of all q field elements."""
        return self.gf.elements

    def square_elements(self):
        """List the square elements of the field without repeats."""
        seen = set()
        for x in self.elements():
            square = x**2
            key = self.key(square)
            if key in seen:
                continue
            seen.add(key)
            yield square

    def is_square(self, value):
        """Test whether value has a square root in this finite field.

        In odd characteristic, Euler's criterion says that a nonzero element
        is a square precisely when value^((q-1)/2)=1. Repeated squaring
        evaluates this power without first building a list of all squares.
        """
        value = self(value)
        # Count zero as a square.
        if value == self.gf(0):
            return True

        # Every element of a finite field of characteristic two is a square.
        # The Frobenius map x -> x^2 is an automorphism.
        if self.gf.characteristic == 2:
            return True

        result = self.gf(1)
        power = value

        # Binary exponentiation. At position i, ``power`` is value^(2^i).
        # Multiplying it into ``result`` for each 1-bit produces exactly
        # value^((q-1)/2), with every operation carried out inside F_q.
        # This lets us apply Euler's criterion with log(q) complexity.
        for bit in self.square_exponent_bits:
            if bit:
                result = result * power
            power = power * power

        return result == self.gf(1)

    def key(self, value):
        """Give an element a unique integer label for equality checks."""
        # `galois` elements are not hashable, but int(...) providdes a unique 
        # label for all extension field elements.
        return int(self(value))

    def format(self, value):
        """Write an element as a polynomial in the field's chosen generator."""
        with self.gf.repr("poly"):
            return str(self(value))
