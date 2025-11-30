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


Tasks = [{'id': 1, 'cost': 3, 'quality': 5},
         {'id': 2, 'cost': 2, 'quality': 3},
         {'id': 3, 'cost': 4, 'quality': 6},
         {'id': 4, 'cost': 8, 'quality': 10},
         {'id': 5, 'cost': 1, 'quality': 1}]

Task_sets = [
    [{'id': 1, 'cost': 2, 'quality': 3},
     {'id': 2, 'cost': 1, 'quality': 2},
     {'id': 3, 'cost': 4, 'quality': 5},
     {'id': 4, 'cost': 3, 'quality': 4}],

    [{'id': 1, 'cost': 3, 'quality': 5},
     {'id': 2, 'cost': 2, 'quality': 3},
     {'id': 3, 'cost': 4, 'quality': 6},
     {'id': 4, 'cost': 8, 'quality': 10},
     {'id': 5, 'cost': 1, 'quality': 1}],

    [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 4},
     {'id': 3, 'cost': 5, 'quality': 7},
     {'id': 4, 'cost': 10, 'quality': 12},
     {'id': 5, 'cost': 2, 'quality': 2},
     {'id': 6, 'cost': 1, 'quality': 1}],

    [{'id': 1, 'cost': 4, 'quality': 5},
     {'id': 2, 'cost': 5, 'quality': 6},
     {'id': 3, 'cost': 6, 'quality': 9},
     {'id': 4, 'cost': 11, 'quality': 14},
     {'id': 5, 'cost': 2, 'quality': 2},
     {'id': 6, 'cost': 3, 'quality': 3},
     {'id': 7, 'cost': 8, 'quality': 12}],

    [{'id': 1, 'cost': 4, 'quality': 5},
     {'id': 2, 'cost': 5, 'quality': 6},
     {'id': 3, 'cost': 6, 'quality': 9},
     {'id': 4, 'cost': 11, 'quality': 15},
     {'id': 5, 'cost': 2, 'quality': 2},
     {'id': 8, 'cost': 7, 'quality': 10},
     {'id': 6, 'cost': 3, 'quality': 3},
     {'id': 7, 'cost': 1, 'quality': 1}],

    [{'id': 1, 'cost': 5, 'quality': 6},
    {'id': 2, 'cost': 6, 'quality': 7},
    {'id': 3, 'cost': 7, 'quality': 10},
    {'id': 4, 'cost': 13, 'quality': 17},
    {'id': 5, 'cost': 3, 'quality': 3},
    {'id': 6, 'cost': 4, 'quality': 4},
    {'id': 7, 'cost': 10, 'quality': 14},
    {'id': 8, 'cost': 1, 'quality': 1},
    {'id': 9, 'cost': 12, 'quality': 18},
    ],
    [
    {'id': 1, 'cost': 6, 'quality': 7},
    {'id': 2, 'cost': 7, 'quality': 8},
    {'id': 3, 'cost': 8, 'quality': 11},
    {'id': 4, 'cost': 15, 'quality': 19},
    {'id': 5, 'cost': 3, 'quality': 3},
    {'id': 6, 'cost': 4, 'quality': 4},
    {'id': 7, 'cost': 11, 'quality': 15},
    {'id': 8, 'cost': 9, 'quality': 12},
    {'id': 9, 'cost': 13, 'quality': 19},
    {'id': 10, 'cost': 1, 'quality': 1},
    ],
    [
    {'id': 1, 'cost': 7, 'quality': 8},
    {'id': 2, 'cost': 8, 'quality': 9},
    {'id': 3, 'cost': 9, 'quality': 12},
    {'id': 4, 'cost': 17, 'quality': 21},
    {'id': 5, 'cost': 4, 'quality': 4},
    {'id': 6, 'cost': 5, 'quality': 5},
    {'id': 7, 'cost': 12, 'quality': 17},
    {'id': 8, 'cost': 10, 'quality': 13},
    {'id': 9, 'cost': 14, 'quality': 21},
    {'id': 10, 'cost': 6, 'quality': 7},
    {'id': 11, 'cost': 1, 'quality': 1},
    ],
[
    {'id': 1, 'cost': 8, 'quality': 9},
    {'id': 2, 'cost': 9, 'quality': 10},
    {'id': 3, 'cost': 10, 'quality': 13},
    {'id': 4, 'cost': 19, 'quality': 23},
    {'id': 5, 'cost': 5, 'quality': 5},
    {'id': 6, 'cost': 6, 'quality': 7},
    {'id': 7, 'cost': 13, 'quality': 18},
    {'id': 8, 'cost': 11, 'quality': 14},
    {'id': 9, 'cost': 15, 'quality': 22},
    {'id': 10, 'cost': 7, 'quality': 8},
    {'id': 11, 'cost': 2, 'quality': 2},
    {'id': 12, 'cost': 3, 'quality': 3},
],
[
    {'id': 1, 'cost': 9, 'quality': 10},
    {'id': 2, 'cost': 10, 'quality': 12},
    {'id': 3, 'cost': 12, 'quality': 15},
    {'id': 4, 'cost': 21, 'quality': 26},
    {'id': 5, 'cost': 6, 'quality': 6},
    {'id': 6, 'cost': 7, 'quality': 8},
    {'id': 7, 'cost': 15, 'quality': 20},
    {'id': 8, 'cost': 13, 'quality': 16},
    {'id': 9, 'cost': 17, 'quality': 24},
    {'id': 10, 'cost': 8, 'quality': 9},
    {'id': 11, 'cost': 3, 'quality': 3},
    {'id': 12, 'cost': 4, 'quality': 4},
    {'id': 13, 'cost': 1, 'quality': 1},
],
[
    {'id': 1, 'cost': 10, 'quality': 11},
    {'id': 2, 'cost': 12, 'quality': 13},
    {'id': 3, 'cost': 13, 'quality': 17},
    {'id': 4, 'cost': 24, 'quality': 30},
    {'id': 5, 'cost': 7, 'quality': 7},
    {'id': 6, 'cost': 8, 'quality': 9},
    {'id': 7, 'cost': 17, 'quality': 22},
    {'id': 8, 'cost': 14, 'quality': 18},
    {'id': 9, 'cost': 19, 'quality': 27},
    {'id': 10, 'cost': 9, 'quality': 10},
    {'id': 11, 'cost': 4, 'quality': 4},
    {'id': 12, 'cost': 5, 'quality': 5},
    {'id': 13, 'cost': 2, 'quality': 2},
    {'id': 14, 'cost': 3, 'quality': 3},
],
[
    {'id': 1, 'cost': 11, 'quality': 13},
    {'id': 2, 'cost': 13, 'quality': 15},
    {'id': 3, 'cost': 15, 'quality': 19},
    {'id': 4, 'cost': 27, 'quality': 33},
    {'id': 5, 'cost': 8, 'quality': 8},
    {'id': 6, 'cost': 9, 'quality': 11},
    {'id': 7, 'cost': 19, 'quality': 24},
    {'id': 8, 'cost': 16, 'quality': 20},
    {'id': 9, 'cost': 21, 'quality': 29},
    {'id': 10, 'cost': 11, 'quality': 12},
    {'id': 11, 'cost': 5, 'quality': 5},
    {'id': 12, 'cost': 6, 'quality': 6},
    {'id': 13, 'cost': 3, 'quality': 3},
    {'id': 14, 'cost': 4, 'quality': 4},
    {'id': 15, 'cost': 1, 'quality': 1},
],
[
    {'id': 1, 'cost': 13, 'quality': 15},
    {'id': 2, 'cost': 15, 'quality': 17},
    {'id': 3, 'cost': 17, 'quality': 21},
    {'id': 4, 'cost': 30, 'quality': 37},
    {'id': 5, 'cost': 9, 'quality': 9},
    {'id': 6, 'cost': 11, 'quality': 12},
    {'id': 7, 'cost': 21, 'quality': 26},
    {'id': 8, 'cost': 18, 'quality': 23},
    {'id': 9, 'cost': 24, 'quality': 32},
    {'id': 10, 'cost': 12, 'quality': 14},
    {'id': 11, 'cost': 6, 'quality': 6},
    {'id': 12, 'cost': 7, 'quality': 7},
    {'id': 13, 'cost': 4, 'quality': 4},
    {'id': 14, 'cost': 5, 'quality': 5},
    {'id': 15, 'cost': 2, 'quality': 2},
    {'id': 16, 'cost': 1, 'quality': 1},
],
[
    {'id': 1, 'cost': 14, 'quality': 16},
    {'id': 2, 'cost': 16, 'quality': 18},
    {'id': 3, 'cost': 18, 'quality': 23},
    {'id': 4, 'cost': 33, 'quality': 41},
    {'id': 5, 'cost': 10, 'quality': 10},
    {'id': 6, 'cost': 12, 'quality': 14},
    {'id': 7, 'cost': 23, 'quality': 28},
    {'id': 8, 'cost': 19, 'quality': 25},
    {'id': 9, 'cost': 26, 'quality': 35},
    {'id': 10, 'cost': 13, 'quality': 15},
    {'id': 11, 'cost': 7, 'quality': 7},
    {'id': 12, 'cost': 8, 'quality': 8},
    {'id': 13, 'cost': 5, 'quality': 5},
    {'id': 14, 'cost': 6, 'quality': 6},
    {'id': 15, 'cost': 3, 'quality': 3},
    {'id': 16, 'cost': 2, 'quality': 2},
    {'id': 17, 'cost': 1, 'quality': 1},
],
[
    {'id': 1, 'cost': 15, 'quality': 18},
    {'id': 2, 'cost': 18, 'quality': 20},
    {'id': 3, 'cost': 20, 'quality': 25},
    {'id': 4, 'cost': 36, 'quality': 45},
    {'id': 5, 'cost': 11, 'quality': 11},
    {'id': 6, 'cost': 14, 'quality': 15},
    {'id': 7, 'cost': 25, 'quality': 30},
    {'id': 8, 'cost': 21, 'quality': 27},
    {'id': 9, 'cost': 28, 'quality': 38},
    {'id': 10, 'cost': 15, 'quality': 17},
    {'id': 11, 'cost': 8, 'quality': 8},
    {'id': 12, 'cost': 9, 'quality': 9},
    {'id': 13, 'cost': 6, 'quality': 6},
    {'id': 14, 'cost': 7, 'quality': 7},
    {'id': 15, 'cost': 4, 'quality': 4},
    {'id': 16, 'cost': 3, 'quality': 3},
    {'id': 17, 'cost': 2, 'quality': 2},
    {'id': 18, 'cost': 1, 'quality': 1},
],
[
    {'id': 1, 'cost': 17, 'quality': 20},
    {'id': 2, 'cost': 19, 'quality': 22},
    {'id': 3, 'cost': 22, 'quality': 27},
    {'id': 4, 'cost': 39, 'quality': 49},
    {'id': 5, 'cost': 12, 'quality': 12},
    {'id': 6, 'cost': 15, 'quality': 17},
    {'id': 7, 'cost': 27, 'quality': 33},
    {'id': 8, 'cost': 23, 'quality': 29},
    {'id': 9, 'cost': 31, 'quality': 41},
    {'id': 10, 'cost': 16, 'quality': 19},
    {'id': 11, 'cost': 9, 'quality': 9},
    {'id': 12, 'cost': 10, 'quality': 10},
    {'id': 13, 'cost': 7, 'quality': 7},
    {'id': 14, 'cost': 8, 'quality': 8},
    {'id': 15, 'cost': 5, 'quality': 5},
    {'id': 16, 'cost': 4, 'quality': 4},
    {'id': 17, 'cost': 3, 'quality': 3},
    {'id': 18, 'cost': 2, 'quality': 2},
    {'id': 19, 'cost': 1, 'quality': 1},
],
[
    {'id': 1, 'cost': 18, 'quality': 22},
    {'id': 2, 'cost': 21, 'quality': 24},
    {'id': 3, 'cost': 24, 'quality': 29},
    {'id': 4, 'cost': 42, 'quality': 53},
    {'id': 5, 'cost': 13, 'quality': 13},
    {'id': 6, 'cost': 17, 'quality': 18},
    {'id': 7, 'cost': 29, 'quality': 35},
    {'id': 8, 'cost': 25, 'quality': 31},
    {'id': 9, 'cost': 33, 'quality': 44},
    {'id': 10, 'cost': 17, 'quality': 20},
    {'id': 11, 'cost': 10, 'quality': 10},
    {'id': 12, 'cost': 11, 'quality': 11},
    {'id': 13, 'cost': 8, 'quality': 8},
    {'id': 14, 'cost': 9, 'quality': 9},
    {'id': 15, 'cost': 6, 'quality': 6},
    {'id': 16, 'cost': 5, 'quality': 5},
    {'id': 17, 'cost': 4, 'quality': 4},
    {'id': 18, 'cost': 3, 'quality': 3},
    {'id': 19, 'cost': 2, 'quality': 2},
    {'id': 20, 'cost': 1, 'quality': 1},
],
[
    {'id': 1, 'cost': 20, 'quality': 24},
    {'id': 2, 'cost': 23, 'quality': 26},
    {'id': 3, 'cost': 26, 'quality': 32},
    {'id': 4, 'cost': 46, 'quality': 58},
    {'id': 5, 'cost': 14, 'quality': 14},
    {'id': 6, 'cost': 18, 'quality': 20},
    {'id': 7, 'cost': 32, 'quality': 38},
    {'id': 8, 'cost': 27, 'quality': 34},
    {'id': 9, 'cost': 36, 'quality': 48},
    {'id': 10, 'cost': 19, 'quality': 22},
    {'id': 11, 'cost': 11, 'quality': 11},
    {'id': 12, 'cost': 12, 'quality': 12},
    {'id': 13, 'cost': 9, 'quality': 9},
    {'id': 14, 'cost': 10, 'quality': 10},
    {'id': 15, 'cost': 7, 'quality': 7},
    {'id': 16, 'cost': 6, 'quality': 6},
    {'id': 17, 'cost': 5, 'quality': 5},
    {'id': 18, 'cost': 4, 'quality': 4},
    {'id': 19, 'cost': 3, 'quality': 3},
    {'id': 20, 'cost': 2, 'quality': 2},
    {'id': 21, 'cost': 1, 'quality': 1},
]





]

K = 24
Bstart = 20
Bmax = 30
Bmin = 10

E = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4,
     3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4,
     3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4,
     3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4,
     3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4]
E_b = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4]


def eval_iter_timeslots():
    x_axis = []
    y_axis = []

    for i in range(20, 100, 10):
        x_axis.append(i)
        times = []

        global K
        K = i

        for _ in range(100):
            # Start timing
            start = timeit.default_timer()


            solve(Tasks, K, Bmax, Bmin, Bstart, E)
            # Stop timing
            end = timeit.default_timer()
            elapsed = (end - start) * 1000
            times.append(elapsed)

        # Store mean execution time for this K
        y_axis.append(statistics.fmean(times))
        print(statistics.fmean(times))




def eval_iter_battery():
    x_axis = []
    y_axis = []
    p = 0

    for i in range(20, 200, 10):
        x_axis.append(i - Bmin)
        times = []

        magnifier = i / 30
        global Bmax, Bstart, E, Tasks
        Bmax = i
        Bstart = int((Bmax + Bmin) / 2)

        if magnifier != 1:
            E = list(map(lambda x: round(magnifier * x), E_b))
        else:
            E = E_b[::]

        Tasks = Task_sets[p]

        for _ in range(100):

            # Start timing
            start = timeit.default_timer()

            solve(Tasks, K, Bmax, Bmin, Bstart, E)

            # Stop timing
            end = timeit.default_timer()
            elapsed = end - start
            elapsed_ms = elapsed * 1000  # convert to milliseconds
            times.append(elapsed_ms)

        y_axis.append(statistics.fmean(times))
        print(y_axis[-1])
        p += 1


eval_iter_battery()
