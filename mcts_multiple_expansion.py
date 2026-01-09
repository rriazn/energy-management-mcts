import math
import random
import statistics
from collections import deque
import plotly.express as px
import numpy as np
import timeit
from pyvis.network import Network


class Edge:
    def __init__(self, parent, child, task):
        self.parent = parent
        self.child = child
        self.task = task


class Node:
    def __init__(self, battery, timeslot, parent=None):
        self.battery = battery
        self.timeslot = timeslot  # timeslot 1 meaning from 0 to 1
        self.parents = [parent]
        self.children = []
        self.visits = 0
        self.win_quality = 0
        self.possible_tasks = self.get_possible_tasks()

    def get_possible_tasks(self):
        return [] if self.timeslot == K \
            else list(filter(lambda t: self.battery + E[self.timeslot] - t["cost"] >= B_min, Tasks))

    def is_fully_expanded(self):
        return len(self.possible_tasks) == 0

    def is_terminal(self):
        return len(self.get_possible_tasks()) == 0 or self.timeslot == K

    def expand(self):
        edges = []
        while True:
            next_task, new_battery = None, 0
            new_child = False
            # look for unexplored children
            while len(self.possible_tasks) != 0:
                next_task = self.possible_tasks.pop()
                new_battery = min(B_max, self.battery + E[self.timeslot] - next_task["cost"])
                if nodes[self.timeslot, new_battery - B_min] is not None:
                    # child already exists, add edge
                    edge = Edge(self, nodes[self.timeslot, new_battery - B_min], next_task)
                    self.children.append(edge)
                    nodes[self.timeslot, new_battery - B_min].parents.append(edge)
                else:
                    # new child found
                    new_child = True
                    break
            # node is fully explored
            if len(self.possible_tasks) == 0 and not new_child:
                break
            # child doesn't yet exist, add it
            edge = Edge(self, None, next_task)
            edge.child = Node(new_battery, self.timeslot + 1, parent=edge)
            nodes[self.timeslot, new_battery - B_min] = edge.child
            self.children.append(edge)
            edges.append(edge)
        return edges

    def get_best_move(self, c=math.sqrt(2)):
        if self.battery == B_max:
            return max(self.children, key=lambda edge: edge.task["quality"])
        return max(self.children, key=lambda edge: (edge.child.win_quality / edge.child.visits))
        # + c * math.sqrt(math.log(self.visits) / edge.child.visits))
        # return max(self.children, key=lambda edge: (edge.child.win_quality / edge.child.visits) + c *
        #                                           self.visits / (1 + edge.child.visits))

    def simulate(self, qual):
        sim_timeslot = self.timeslot
        sim_state_battery = self.battery
        sim_state_quality = qual
        sim_path = []
        while True:
            if sim_timeslot == K:
                return (
                    sim_state_quality, sim_path, sim_state_quality,
                    sim_state_battery) if sim_state_battery >= B_start else \
                    (penalized_quality(sim_state_quality, sim_state_battery), sim_path, sim_state_quality,
                     sim_state_battery)

            available_tasks = list(filter(lambda t: sim_state_battery + E[sim_timeslot] -
                                                        t["cost"] >= B_min, Tasks))

            if not available_tasks:
                return 0, [], 0, 0
            chosen_task = random.choice(available_tasks)
            if sim_state_battery == B_max:
                chosen_task = max(list(filter(
                    lambda t: sim_state_battery + E[sim_timeslot] - t["cost"] >= B_start, available_tasks
                )), key=lambda task: task["quality"])

            sim_timeslot += 1
            sim_state_battery = min(B_max, sim_state_battery - chosen_task["cost"] + E[sim_timeslot - 1])
            sim_state_quality += chosen_task["quality"]
            sim_path.append(chosen_task)


def backpropagate(summed_up_result, path, edges_count):
    for node in path:
        node.visits += edges_count
        node.win_quality += summed_up_result


def mcts(start_node, iterations=500):
    root = start_node

    # save the best path explored by selection, expansion and simulation
    best_path = []
    best_quality = 0
    best_path_remaining_battery = 0
    for j in range(iterations):
        node = root
        result = []

        # select until expand creates a new node
        # also memorize chosen path for backpropagation
        path = [node]
        task_path = []
        path_quality = 0

        while len(result) == 0:
            # select, create path
            while not node.is_terminal() and node.is_fully_expanded():
                best_move = node.get_best_move()
                node = best_move.child
                path.append(node)
                task_path.append(best_move.task)
                path_quality += best_move.task["quality"]
            # expand
            if not node.is_terminal():
                # result is now a list of all newly created outgoing edges to newly created nodes
                result = node.expand()
            else:
                break
        if len(result) != 0:
            summed_up_result = 0
            for edge in result:
                # simulate
                node = edge.child
                backpropagation_value, sim_path, sim_quality, sim_battery = node.simulate(
                    path_quality + edge.task["quality"])
                if backpropagation_value > best_quality and sim_battery >= B_start:
                    best_path = task_path + [edge.task] + sim_path
                    best_quality = sim_quality
                    best_path_remaining_battery = sim_battery
                summed_up_result += backpropagation_value
                node.visits += 1
                node.win_quality += backpropagation_value

            # backpropagation
            backpropagate(summed_up_result, path, len(result))
        else:
            backpropagation_value, sim_path, sim_quality, sim_battery = node.simulate(path_quality)
            if backpropagation_value > best_quality and sim_battery >= B_start:
                best_path = task_path + [edge.task] + sim_path
                best_quality = sim_quality
                best_path_remaining_battery = sim_battery
            backpropagate(backpropagation_value, path, 1)

    return root, best_path, best_quality, best_path_remaining_battery


def penalized_quality(quality, B_lvl):
    if B_lvl >= B_start:
        return quality
    k = 1
    diff = max(0, B_start - B_lvl)
    scale = diff / B_min
    penalty = quality * (1 - math.exp(-k * scale))
    return quality - penalty


Tasks = []

Task_sets = [
    [{'id': 1, 'cost': 2, 'quality': 3},
     {'id': 3, 'cost': 4, 'quality': 5},
     {'id': 4, 'cost': 3, 'quality': 4},
     {'id': 2, 'cost': 1, 'quality': 2}],

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
     {'id': 6, 'cost': 3, 'quality': 3},
     {'id': 7, 'cost': 8, 'quality': 12},
     {'id': 5, 'cost': 1, 'quality': 1}],

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
     {'id': 9, 'cost': 12, 'quality': 18},
     {'id': 5, 'cost': 1, 'quality': 1}],
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
        {'id': 5, 'cost': 27, 'quality': 32},
        {'id': 6, 'cost': 6, 'quality': 7},
        {'id': 7, 'cost': 13, 'quality': 18},
        {'id': 8, 'cost': 25, 'quality': 29},
        {'id': 9, 'cost': 15, 'quality': 22},
        {'id': 10, 'cost': 7, 'quality': 8},
        {'id': 11, 'cost': 2, 'quality': 2},
        {'id': 12, 'cost': 1, 'quality': 1},
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
        {'id': 14, 'cost': 1, 'quality': 1},
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
E_10 = [3, 1, 0, 0, 1, 2, 4, 6, 6, 5]
E_15 = [3, 1, 0, 0, 0, 0, 1, 2, 4, 5, 6, 6, 6, 5, 4]
E_20 = [3, 2, 1, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 6, 6, 6, 6, 5, 4]
E_25 = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 6, 5, 5, 4]
E_30 = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6, 6, 6, 6, 5, 5, 4, 4, 3]
E_35 = [3, 2, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 6, 6, 6, 6, 5, 5, 5, 4, 4, 3]
E_40 = [3, 3, 2, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 5, 5, 5,
        4, 4, 3]
E_45 = [3, 3, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6,
        6, 6, 5, 5, 5, 4, 4, 3]
E_50 = [3, 3,
        2, 2, 2,
        1, 1, 1, 1,
        0, 0, 0, 0, 0, 0, 0, 0, 0,
        1, 1, 1,
        2, 2, 2,
        3, 3, 3,
        4, 4, 4,
        5, 5, 5,
        6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
        5, 5, 5,
        4, 4, 4,
        3
        ]
E_b = [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 16, 24, 30, 33, 32, 29, 23, 14]

E = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4]
B_start = 30
B_max = 50
B_min = 10
magnifier = B_max / 30
E = list(map(lambda e: round(magnifier * e), E))
nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)
Tasks = [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 5},
     {'id': 3, 'cost': 5, 'quality': 7},
     {'id': 4, 'cost': 8, 'quality': 10},
     {'id': 5, 'cost': 2, 'quality': 3},
     {'id': 6, 'cost': 1, 'quality': 1}]
'''
'''





'''
Tasks = Task_sets[1]
'''
curr_node = Node(B_start, 0)
res = mcts(curr_node, 10)
quality = 0
print(curr_node.win_quality)
#visualize_tree(curr_node)

while len(curr_node.children) != 0:
    move = curr_node.get_best_move()
    print(curr_node.timeslot, curr_node.battery, quality, move.task)
    quality += move.task["quality"]
    curr_node = move.child

print(curr_node.timeslot, curr_node.battery, quality)
print(res[0], res[1], res[2], res[3], len(res[1]))
'''

Tasks = Task_sets[1]
random_assignment_eval()


eval_iter_timeslots()
'''



