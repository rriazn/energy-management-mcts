import numpy as np
import random


def solve(Tasks, K, Bmax, Bmin, Bstart, E):
    opt, schedule = np.zeros((K, Bmax+1)), np.zeros((K, Bmax+1))
    for i in range(K - 1, -1, -1):
        for B in range(Bmax + 1):
            qmax = -100
            idmax = -1
            for t in Tasks:
                if i == K - 1:
                    if B - t['cost'] + E[i] >= Bstart and t['quality'] > qmax:
                        qmax = t['quality']
                        idmax = t['id']
                else:
                    # recurrence: look ahead
                    Br = min(B - t['cost'] + E[i], Bmax)
                    if Br >= Bmin:
                        q = opt[i + 1][Br]
                        if q != 0 and q + t['quality'] > qmax:
                            qmax = q + t['quality']
                            idmax = t['id']
            opt[i][B] = qmax
            schedule[i][B] = idmax
    return schedule, opt


Tasks = [{'id': 1, 'cost': 3, 'quality': 5},
         {'id': 2, 'cost': 2, 'quality': 3},
         {'id': 3, 'cost': 4, 'quality': 6},
         {'id': 4, 'cost': 8, 'quality': 10},
         {'id': 5, 'cost': 1, 'quality': 1}]

K = 24
Bstart = 20
Bmax = 30
Bmin = 10

E = [1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0]

print(solve(Tasks, K, Bmax, Bmin, Bstart, E))
