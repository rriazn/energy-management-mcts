import numpy as np


def initial_assignment():
    global P
    P = sort_plans(P)
    S = [P[0] for _ in range(K)]
    q_1 = P[0]
    B_end = battery_end(S)
    P_copy = P[::]
    while True:
        q_1 = P[0]
        if B_end >= B_start and check_battery_min(S):
            while True:
                print(P)
                P_copy = list(filter(lambda t: t["quality"] > q_1["quality"], P))
                B_end = battery_end(S)
                if B_start == B_end or len(P_copy) == 0:
                    print("?")
                    return S
                q_1 = P_copy[0]
                S = upgrade(S, q_1)
                P = P_copy
        B_end = battery_end(S)
        while B_end < B_start or not check_battery_min(S):
            print(P)
            P_copy = list(filter(lambda t: t["cost"] < q_1["cost"], P))
            if len(P_copy) == 0:
                return None
            q_1 = P_copy[0]
            S = downgrade(S, q_1)
            B_end = battery_end(S)



def sort_plans(P):
    P = sorted(P, key=lambda t: t["quality"] / t["cost"], reverse=True)
    for i in range(len(P) - 1):
        if P[i]["quality"] < P[i + 1]["quality"]:
            P[i + 1], P[i] = P[i], P[i + 1]
    return P


def battery_end(S):
    B_end = B_start
    for i in range(K):
        B_end = min(B_max, B_end + E[i] - S[i]["cost"])
    return B_end


def check_battery_min(S):
    B_lvl = B_start
    for i in range(K):
        B_lvl = min(B_max, B_lvl + E[i] - S[i]["cost"])
        if B_lvl < B_min:
            return False
    return True


def upgrade(S, q_1):
    s = sunrise
    j = 1
    while battery_end(S) - B_start >= q_1["cost"] - S[s]["cost"] and j <= K:
        H = S[s]
        S[s] = q_1
        if not check_battery_min(S):
            S[s] = H
            return S
        s = (s + 1) % K
        j += 1
    return S


def downgrade(S, q_1):
    s = sunset
    j = 1
    while (battery_end(S) - B_start < 0 or not check_battery_min(S)) \
            and j <= K:
        S[s] = q_1
        s = (s + 1) % K
        j += 1
    return S


def quality(assignment):
    q = 0
    for i in assignment:
        q += i["quality"]
    return q


P = [
    {'id': 1, 'cost': 3, 'quality': 5},
    {'id': 2, 'cost': 2, 'quality': 3},
    {'id': 3, 'cost': 4, 'quality': 6},
    {'id': 4, 'cost': 8, 'quality': 10},
    {'id': 5, 'cost': 1, 'quality': 1}
]
B_min = 10
B_max = 30
B_start = 20
K = 24
sunrise = 15
sunset = 0
E = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4]

result = initial_assignment()

print(result)
print(battery_end(result), check_battery_min(result))
print(quality(result))
