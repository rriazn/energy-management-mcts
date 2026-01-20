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
E = [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 8, 12, 15, 17, 17, 15, 12, 8]



Tasks = Tasks = [
    {'id': 2, 'cost': 2,  'quality': 3},   # low-power sensing / sync
    {'id': 3, 'cost': 4,  'quality': 6},   # moderate task (fits early hours)
    {'id': 4, 'cost': 6,  'quality': 9},   # mid-day processing
    {'id': 5, 'cost': 9,  'quality': 13},  # heavy task (needs solar ramp-up)
    {'id': 6, 'cost': 12, 'quality': 18},  # peak-hour workload
    {'id': 1, 'cost': 1,  'quality': 1},   # trivial background task
    {'id': 7, 'cost': 15, 'quality': 22} # maximum-value task (solar peak)
]
#print(max(solve(Tasks, K, Bmax, Bmin, Bstart, E)[1][0][:Bstart + 1:]))
