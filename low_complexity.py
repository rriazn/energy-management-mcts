

def low_complexity_algo():
    Dc = [Dmin for _ in E]
    S = [i for i in range(len(E)) if E[i] >= Pc]
    D = [i for i in range(len(E)) if E[i] < Pc]
    print(S, D)

    W = [1 / Pc if i in S else 1 / ((Pc / eta) + E[i]*(1 - 1 / eta)) for i in range(len(E))]
    R = compute_r(D, S, Dc)

    print(R)
    if R < 0:
        return None

    W_sorted_coefficients = [i for i in range(len(E))]
    W_sorted_coefficients = sorted(W_sorted_coefficients, key=lambda j: W[j], reverse=True)

    Dc_copy = [i for i in Dc]
    j = 0
    while True:
        Dc_copy[W_sorted_coefficients[j]] = Dmax
        R = compute_r(D, S, Dc_copy)
        if R <= 0:
            break
        Dc[W_sorted_coefficients[j]] = Dmax
        j += 1
    R = compute_r(D, S, Dc)
    print(j, R)
    Dc[W_sorted_coefficients[j]] = R / Pc + Dmin if W_sorted_coefficients[j] in D \
        else R / ((E[W_sorted_coefficients[j]] - Pc) / eta - E[W_sorted_coefficients[j]]) + Dmin

    return Dc







def compute_r(D, S, Dc):
    R = 0
    for i in E:
        R += i
    for i in D:
        R -= Dc[i] * ((Pc / eta) + E[i] * (1 - 1 / eta))
    for i in S:
        R -= Pc * Dc[i]
    return R










E = [1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0]
Pc = 3
eta = 0.8
Dmin = 0
Dmax = 2

print(low_complexity_algo())

