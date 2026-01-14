import statistics
import timeit

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




K = 24
Bstart = 30
Bmax = 50
Bmin = 10

E_b = [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 16, 24, 30, 33, 32, 29, 23, 14]
E = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4]



Tasks = Tasks = [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 4},
     {'id': 3, 'cost': 5, 'quality': 7},
     {'id': 4, 'cost': 8, 'quality': 10},
     {'id': 5, 'cost': 2, 'quality': 2},
     {'id': 6, 'cost': 1, 'quality': 1}]
#print(max(solve(Tasks, K, Bmax, Bmin, Bstart, E)[1][0][:Bstart + 1:]))
