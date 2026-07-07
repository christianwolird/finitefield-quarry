
class PrimeField:
    def __init__(self, p):
        self.p = p

    def __call__(self, value):
        # Keep prime-field elements as ordinary integers in the range 0,...,p-1.
        return value % self.p

    def elements(self):
        return range(self.p)

    def is_square(self, a):
        a = self(a)
        if a == 0:
            return True

        # Euler's criterion: a^((p-1)/2) is 1 exactly for nonzero squares.
        exponent = (self.p - 1) // 2
        return pow(a, exponent, self.p) == 1

    def key(self, value):
        return self(value)

    def format(self, value):
        return str(self(value))
