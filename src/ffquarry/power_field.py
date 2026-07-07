import galois


class PowerField:
    def __init__(self, q):
        self.q = q
        self.gf = galois.GF(q)

        self.square_exponent_bits = [
            bit == "1"
            for bit in reversed(bin((q - 1) // 2)[2:])
        ]

    def __call__(self, value):
        if isinstance(value, self.gf):
            return value

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
        return int(self(value))

    def format(self, value):
        with self.gf.repr("poly"):
            return str(self(value))
