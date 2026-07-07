import galois


class PowerField:
    def __init__(self, q):
        self.q = q
        self.gf = galois.GF(q)

        # Store the binary expansion once; is_square() uses repeated squaring.
        self.square_exponent_bits = [
            bit == "1"
            for bit in reversed(bin((q - 1) // 2)[2:])
        ]

    def __call__(self, value):
        if isinstance(value, self.gf):
            return value

        # Python integers enter through the prime subfield, not as galois's
        # internal integer encoding of extension-field elements.
        return self.gf(value % self.gf.characteristic)

    def elements(self):
        return self.gf.elements

    def is_square(self, value):
        value = self(value)
        if value == self.gf(0):
            return True

        if self.gf.characteristic == 2:
            return True

        result = self.gf(1)
        power = value

        for bit in self.square_exponent_bits:
            if bit:
                result = result * power
            power = power * power

        return result == self.gf(1)

    def key(self, value):
        # galois elements are not hashable, but int(...) is a unique label.
        return int(self(value))

    def format(self, value):
        # Polynomial notation is easier to read in result files.
        with self.gf.repr("poly"):
            return str(self(value))
