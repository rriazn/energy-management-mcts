import numpy as np

def initial_assignment(P, B_start, B_max, B_min, K, E, sunrise, sunset):
    P = sort_plans(P)
    S = [P[0] for _ in range(K)]
    q_1 = P[0]
    B_end = battery_end(B_start, K, E, S, B_max)
    P_copy = P.copy()
    while B_end < B_start or not check_battery_min(B_start, B_min, K, E, S, B_max):
        P_copy = list(filter(lambda t: t["quality"] < q_1["quality"], P_copy))
        if len(P_copy) == 0:
            return None
        q_1 = P_copy[0]
        S = downgrade(S, q_1, sunset, B_start, B_min, K, E)
        B_end = battery_end(B_start, K, E, S, B_max)

    P_copy = P.copy()
    if B_end >= B_start and check_battery_min(B_start, B_min, K, E, S, B_max):
        while True:
            P_copy = list(filter(lambda t: t["quality"] > q_1["quality"], P_copy))
            B_end = battery_end(B_start, K, E, S, B_max)
            if B_start == B_end or len(P_copy) == 0:
                return S
            q_1 = P_copy[0]
            S = upgrade(S, q_1, sunrise, B_start, B_min, K, E)


def sort_plans(P):
    P = sorted(P, key=lambda t: t["quality"] / t["cost"], reverse=True)
    for i in range(len(P) - 1):
        if P[i]["quality"] < P[i + 1]["quality"]:
            P[i + 1], P[i] = P[i], P[i + 1]
    return P


def battery_end(B_start, K, E, S, B_max):
    B_end = B_start
    for i in range(K):
        B_end = min(B_max, B_end + E[i] - S[i]["cost"])
    return B_end


def check_battery_min(B_start, B_min, K, E, S, B_max):
    B_lvl = B_start
    for i in range(K):
        B_lvl = min(B_max, B_lvl + E[i] - S[i]["cost"])
        if B_lvl < B_min:
            return False
    return True


def upgrade(S, q_1, sunrise, B_start, B_min, K, E):
    s = sunrise
    j = 1
    while battery_end(B_start, K, E, S, B_max) - B_start >= q_1["cost"] - S[s]["cost"] and j <= K:
        H = S[s]
        S[s] = q_1
        if not check_battery_min(B_start, B_min, K, E, S, B_max):
            S[s] = H
            return S
        s = (s + 1) % K
        j += 1
    return S


def downgrade(S, q_1, sunset, B_start, B_min, K, E):
    s = sunset
    j = 1
    while (battery_end(B_start, K, E, S, B_max) - B_start < 0 or not check_battery_min(B_start, B_min, K, E, S, B_max))\
            and j <= K:
        S[s] = q_1
        s = (s + 1) % K
        j += 1
    return S


plans = [
    {'id': 1, 'cost': 3, 'quality': 5},
    {'id': 2, 'cost': 2, 'quality': 3},
    {'id': 3, 'cost': 4, 'quality': 6},
    {'id': 4, 'cost': 8, 'quality': 10},
    {'id': 5, 'cost': 1, 'quality': 1}
]
B_min = 10
B_max = 30
B_start = 15
K = 24
sunrise = 1
sunset = 18
E = [1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0]

result = initial_assignment(plans, B_start, B_max, B_min, K, E, sunrise, sunset)

print(result)
print(battery_end(B_start, K, E, result, B_max), check_battery_min(B_start, B_min, K, E, result, B_max))