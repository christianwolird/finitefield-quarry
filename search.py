from sympy import primerange

def legendre(a, p):
    return pow(a, (p - 1) // 2, p)

for p in primerange(400000):
    solution = None
    squares = set()
    for a in range(2, p):
        A = a**2
        if A in squares:
            continue
        squares.add(A)
        B = (75 - 49 - A) % p
        D = (75 - 1  - A) % p
        F = (75 - 25 - D) % p
        H = (75 - 25 - B) % p
        I = (75 - 49 - F) % p
        entries = [A, B, 49 % p, D, 25 % p, F, 1, H, I]
        if len(set(entries)) < 9:
            continue
        if all(legendre(X, p) == 1 for X in entries):
            solution = entries
            break
    if solution is None:
        print(p)
