import numpy as np


def initial_assignment():
    global P
    P_c = P.copy()
    P = sort_plans(P)
    S = [P[0] for _ in range(K)]
    q_1 = P[0]
    B_end = battery_end(S)
    P_copy = P[::]
    while True:
        q_1 = P[0]
        if B_end >= B_start and check_battery_min(S):
            while True:
                P_copy = list(filter(lambda t: t["quality"] > q_1["quality"], P))
                B_end = battery_end(S)
                if B_start == B_end or len(P_copy) == 0:
                    #print("?")
                    P = P_c
                    return S
                q_1 = P_copy[0]
               # print("up:", [s["id"] for s in S])
                S = upgrade(S, q_1)
                P = P_copy
        B_end = battery_end(S)
        while B_end < B_start or not check_battery_min(S):
            P_copy = list(filter(lambda t: t["cost"] < q_1["cost"], P))
            if len(P_copy) == 0:
                P = P_c
                return None
            q_1 = P_copy[0]
            #print("down")
            S = downgrade(S, q_1)
            B_end = battery_end(S)



def sort_plans(P):
    P = sorted(P, key=lambda t: t["quality"] / t["cost"], reverse=True)
    for i in range(len(P) - 1):
        if P[i]["quality"] < P[i + 1]["quality"] and P[i]["quality"] / P[i]["cost"] == P[i + 1]["quality"] / P[i + 1]["cost"]:
            P[i + 1], P[i] = P[i], P[i + 1]
    return P


def battery_end(S):
    B_end = starting_battery
    for i in range(K):
        B_end = min(B_max, B_end + E[i] - S[i]["cost"])
    return B_end


def check_battery_min(S):
    B_lvl = starting_battery
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


def get_plan_idx_by_id(id, P):
    return next((i for i, p in enumerate(P) if p.get("id") == id), None)


def get_plan_idx(plan, P):
    return next((i for i, p in enumerate(P) if p.get("id") == plan["id"]), None)


def reoptimize(S, P, slot, tolerance):
    P = sorted(P, key=lambda p: p["cost"])
    if battery_end(S) >= B_start + tolerance and check_battery_min(S):
        replaced = True
        while replaced:
            s = slot
            replaced = False
            while s < K:
                pj = get_plan_idx(S[s], P)
                if pj < len(P) - 1:
                    if battery_end(S) - B_start >= P[pj + 1]["cost"] - P[pj]["cost"]:
                        S[s] = P[pj + 1]
                        replaced = True
                        if not check_battery_min(S):
                            S[s] = P[pj]
                            replaced = False
                s += 1
    if battery_end(S) <= B_start - tolerance or not check_battery_min(S):
        replaced = True
        while replaced:
            s = slot
            replaced = False
            while s < K:
                pj = get_plan_idx(S[s], P)
                if pj > 0 and (battery_end(S) < B_start or not check_battery_min(S)):
                    S[s] = P[pj - 1]
                    replaced = True
                s += 1
    return S


P = [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 5},
     {'id': 3, 'cost': 5, 'quality': 7},
     {'id': 4, 'cost': 8, 'quality': 10},
     {'id': 5, 'cost': 2, 'quality': 3},
     {'id': 6, 'cost': 1, 'quality': 1}]
def get_sol_qual_bat(res):
    qual = 0
    battery = starting_battery
    for k in range(K):
        try:
            qual += res[k]["quality"]
        except TypeError:
            print(B_min, B_start, B_max, len(E), K, sunrise, sunset)
            exit(1)
        battery = min(B_max, battery - res[k]["cost"] + E[k])
    return qual, battery


B_min = 60
B_max = 100
B_start = 80
K = 24
sunrise = 12
sunset = 2
starting_battery = B_start
E = [3, 1, 3, 4, 4, 2, 4, 2, 2, 4, 4, 6, 7, 7, 5, 5, 6, 10, 10, 10, 10, 10, 10, 10]
P_c = P.copy()

print(get_plan_idx({'id': 5, 'cost': 53, 'quality': 14}, P))
result = initial_assignment()
#reoptimize(list(map(lambda id: P[get_plan_idx_by_id(id, P)], plan)), P, 12, 0)

result = initial_assignment()

res = list(map(lambda t: t["id"], result))
qual = 0
battery = starting_battery
print(res)
for k in range(K):
    task = next((t for t in P_c if t["id"] == res[k]), None)
    qual += task["quality"]
    battery = min(B_max, battery - task["cost"] + E[k])
    print(task["quality"], qual, E[k], task["cost"], battery)
    #print(task["cost"], task["quality"])

