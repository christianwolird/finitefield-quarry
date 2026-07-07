import galois


class PowerField:
    def __init__(self, q):
        self.q = q
        self.gf = galois.GF(q)

    def elements(self):
        return [self.gf(x) for x in self.gf.elements]

    def power(self, a, exponent):
        result = self.gf(1)
        base = self.gf(a)

        while exponent:
            if exponent % 2 == 1:
                result = result * base
            base = base * base
            exponent = exponent // 2

        return result

    def is_square(self, a):
        if a == self.gf(0):
            return True

        exponent = (self.q - 1) // 2
        return self.power(a, exponent) == self.gf(1)
