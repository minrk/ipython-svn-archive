def factor2(n):
    intn = int(n)
    factors = []
    i = 0

    # 1 is a special case
    if n == 1:
        return [(1,1)]

    while 1:
        i += 1

        if i > n:
            break

        if n % i == 0:
            # if n/i not in factors.keys():
            factors.append((i, n/i))

    return factors

