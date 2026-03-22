import statistics
import timeit

import numpy as np
import random


def solve(Tasks, K, Bmax, Bmin, Bstart, E):
    opt, schedule = np.empty((K, Bmax+1)), np.zeros((K, Bmax+1))
    for i in range(K - 1, -1, -1):
        for B in range(Bmax + 1):
            qmax = -100
            idmax = -1
            for t in Tasks:
                if i == K - 1:
                    if B - t['cost'] + E[i] >= Bstart and t['quality'] > qmax:
                        qmax = t['quality']
                        idmax = t["id"]
                else:
                    # recurrence: look ahead
                    Br = min(B - t['cost'] + E[i], Bmax)
                    if Br >= Bmin:
                        q = opt[i + 1][Br]
                        if q != 0 and q + t['quality'] > qmax:
                            qmax = q + t['quality']
                            idmax = t["id"]
            opt[i][B] = qmax
            schedule[i][B] = idmax
    return schedule, opt


def reconstruct(schedule):
    assignment = []
    B = Bstart

    for i in range(K):
        task_id = int(schedule[i][B])
        if task_id == -1:
            break  # no valid action

        # get full task info
        task = next(t for t in Tasks if t["id"] == task_id)
        assignment.append(task["id"])

        # update battery
        B = min(B - task["cost"] + E[i], Bmax)

    return assignment, B

E = [3, 1, 3, 4, 4, 2, 4, 2, 2, 4, 4, 6, 7, 7, 5, 5, 6, 10, 10, 10, 10, 10, 10, 10]

K = 24          # timeslots
Bstart = 80
Bmax = 100
Bmin = 60


Tasks = [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 5},
     {'id': 3, 'cost': 5, 'quality': 7},
     {'id': 4, 'cost': 8, 'quality': 10},
     {'id': 5, 'cost': 2, 'quality': 3},
     {'id': 6, 'cost': 1, 'quality': 1}]
'''
sol = solve(Tasks, K, Bmax, Bmin, Bstart, E)
print(sol[1][0][Bstart])
schedule = reconstruct(sol[0])[0]
print(schedule)
quality = 0

battery = Bstart

for k in range(K):
    task = next(t for t in Tasks if t["id"] == schedule[k])
    quality += task["quality"]
    battery = min(Bmax, battery - task["cost"] + E[k])
    print(task["quality"], quality, E[k], task["cost"], battery)
    #print(task["cost"], task["quality"])
'''