
class PrimeField:
    def __init__(self, p):
        self.p = p

    def elements(self):
        return range(self.p)

    def power(self, a, exponent):
        return pow(a, exponent, self.p)

    def is_square(self, a):
        a = a % self.p
        if a == 0:
            return True

        exponent = (self.p - 1) // 2
        return self.power(a, exponent) == 1
