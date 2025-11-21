import math
import random
import statistics
from collections import deque
import plotly.express as px
import numpy as np
import pandas as pd
from pyvis.network import Network

K = 24
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


        # node is fully explored, go back to selecting
        if len(self.possible_tasks) == 0 and not new_child:
            return None
        # child doesn't yet exist, add it
        edge = Edge(self, None, next_task)
        edge.child = Node(new_battery, self.timeslot + 1, parent=edge)
        nodes[self.timeslot, new_battery - B_min] = edge.child
        self.children.append(edge)
        return edge

    def get_best_move(self, c=math.sqrt(2)):
        return max(self.children, key=lambda edge: (edge.child.win_quality / edge.child.visits) + c *
                                                   math.sqrt(math.log(self.visits) / edge.child.visits))
        #return max(self.children, key=lambda edge: (edge.child.win_quality / edge.child.visits) + c *
        #                                           self.visits / (1 + edge.child.visits))

    def simulate(self, qual):
        sim_timeslot = self.timeslot
        sim_state_battery = self.battery
        sim_state_quality = qual
        sim_path = []
        while True:
            if sim_timeslot == K:
                return (sim_state_quality, sim_path, sim_state_quality, sim_state_battery) if sim_state_battery >= B_start else \
                    (penalized_quality(sim_state_quality, sim_state_battery), [], 0, 0)

            available_tasks = list(filter(lambda t: sim_state_battery + E[sim_timeslot] -
                                                    t["cost"] >= B_min, Tasks))
            if not available_tasks:
                return 0, [], 0, 0
            chosen_task = random.choice(available_tasks)
            sim_timeslot += 1
            sim_state_battery = min(B_max, sim_state_battery - chosen_task["cost"] + E[sim_timeslot - 1])
            sim_state_quality += chosen_task["quality"]
            sim_path.append(chosen_task)


def backpropagate(result, path):
    for node in path:
        node.visits += 1
        scaled_result = result
        node.win_quality += scaled_result


def mcts(start_node, iterations=500):
    root = start_node

    # save the best path explored by selection, expansion and simulation
    best_path = []
    best_quality = 0
    best_path_remaining_battery = 0
    for j in range(iterations):
        node = root
        result = None

        # select until expand creates a new node
        # also memorize chosen path for backpropagation
        path = [node]
        task_path = []
        path_quality = 0

        while result is None:
            # select, create path
            while not node.is_terminal() and node.is_fully_expanded():
                best_move = node.get_best_move()
                node = best_move.child
                path.append(node)
                task_path.append(best_move.task)
                path_quality += best_move.task["quality"]
            # expand
            if not node.is_terminal():
                result = node.expand()
            else:
                break

        # if new node was created, add it to path
        if result is not None:
            node = result.child
            path.append(node)
            task_path.append(result.task)
            path_quality += result.task["quality"]
        # simulate
        res, sim_path, sim_quality, sim_battery = node.simulate(path_quality)
        if sim_quality > best_quality:
            best_path = task_path + sim_path
            best_quality = sim_quality
            best_path_remaining_battery = sim_battery
        # backpropagate
        backpropagate(res, path)

    return root, best_path, best_quality, best_path_remaining_battery


def penalized_quality(quality, B_lvl):
    k = 1
    diff = max(0, B_start - B_lvl)  # only penalize if below start
    scale = diff / B_min
    penalty = quality * (1 - math.exp(-k * scale))
    return 0


Tasks = []


Task_sets = [
    [{'id': 1, 'cost': 2, 'quality': 4},
     {'id': 2, 'cost': 2, 'quality': 2},
     {'id': 3, 'cost': 3, 'quality': 5},
     {'id': 4, 'cost': 1, 'quality': 1}],

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
     {'id': 7, 'cost': 9, 'quality': 13}],

    [{'id': 1, 'cost': 5, 'quality': 6},
    {'id': 2, 'cost': 6, 'quality': 7},
    {'id': 3, 'cost': 7, 'quality': 10},
    {'id': 4, 'cost': 13, 'quality': 17},
    {'id': 5, 'cost': 3, 'quality': 3},
    {'id': 6, 'cost': 4, 'quality': 4},
    {'id': 7, 'cost': 10, 'quality': 14},
    {'id': 8, 'cost': 8, 'quality': 11},
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
    {'id': 10, 'cost': 5, 'quality': 6},
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
    {'id': 11, 'cost': 3, 'quality': 2},
    ]

]


E = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3,
     4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1,
     0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3,
     4, 5, 5, 6, 6, 6, 6, 5, 5, 4]
B_start = 17
B_max = 25
B_min = 10


nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)

'''
'''
def evaluate(iterations=100):
    battery_values = []
    quality_values = []
    battery_underflow = 0
    errors = 0
    no_full_path = 0
    for i in range(iterations):
        global nodes
        nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)
        curr_node = Node(B_start, 0)
        error = False
        solution = None
        try:
            solution = mcts(curr_node, 200)
        except ValueError:
            errors += 1
            error = True
        curr_node = solution[0]
        if not error:
            quality = 0
            while len(curr_node.children) != 0:
                move = curr_node.get_best_move()
                quality += move.task["quality"]
                curr_node = move.child
            battery_values.append(solution[3])
            quality_values.append(solution[2])
            if battery_values[-1] < B_start:
                battery_underflow += 1
            if curr_node.timeslot < 24:
                no_full_path += 1

    print(statistics.fmean(battery_values), statistics.fmean(quality_values), statistics.stdev(quality_values))


#evaluate(10000)


def eval_iterations():
    x_axis = []
    y_axis = []
    for i in range(10, 501, 10):
        x_axis.append(i)
        battery_values = []
        quality_values = []
        battery_underflow = 0
        errors = 0
        no_full_path = 0
        for j in range(100):
            global nodes
            nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)
            curr_node = Node(B_start, 0)
            solution = mcts(curr_node, iterations=i)
            quality_values.append(solution[2])
            battery_values.append(solution[3])
            if battery_values[-1] < B_start:
                battery_underflow += 1
        y_axis.append(statistics.fmean(quality_values))
    fig = px.line(
        x=x_axis,
        y=y_axis,
        markers=True,  # keeps the dots visible
        color_discrete_sequence=['#FF8C00']  # same color as before
    )
    fig.show()


def exists_full_path(root, depth):
    node = root
    while len(node.children) > 0:
        node = node.get_best_move().child
    if node.timeslot == depth:
        return True
    return False


def eval_iter_timeslots():
    x_axis = []
    y_axis = []
    for i in range(20, 100, 5):
        x_axis.append(i)
        iter_count = []
        global K
        K = i
        for k in range(100):
            global nodes
            nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)
            root = Node(B_start, 0)
            for j in range(1000):
                mcts(root, 1)
                if exists_full_path(root, i):
                    iter_count.append(j)
                    break
        y_axis.append(statistics.fmean(iter_count))
    fig = px.line(
        x=x_axis,
        y=y_axis,
        markers=True,  # keeps the dots visible
        color_discrete_sequence=['#FF8C00']  # same color as before
    )
    fig.show()


def eval_iter_battery():
    x_axis = []
    y_axis = []
    p = 0
    for i in range(20, 100, 5):
        x_axis.append(i - B_min)
        iter_count = []
        magnifier = i / 30
        global B_max, B_start, E, Tasks
        B_max = i
        B_start = int((B_max + B_min) / 2)
        if magnifier > 1:
            E = list(map(lambda x: int(magnifier * x), E))
        Tasks = Task_sets[p]
        print(B_max, B_start, p)
        for k in range(100):
            global nodes
            nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)
            root = Node(B_start, 0)
            for j in range(1000):
                mcts(root, 1)
                if exists_full_path(root, 24):
                    iter_count.append(j)
                    break
        y_axis.append(statistics.fmean(iter_count))
        print(y_axis[-1])
        if i % 2 == 1:
            p += 1
    fig = px.line(
        x=x_axis,
        y=y_axis,
        markers=True,  # keeps the dots visible
        color_discrete_sequence=['#FF8C00']  # same color as before
    )
    fig.show()



def visualize_tree(root, max_nodes=1000):
    net = Network(height='800px', width='100%', directed=True)
    queue = deque([root])
    visited = set()
    count = 0

    while queue and count < max_nodes:
        current = queue.popleft()
        node_id = str(id(current))
        if node_id in visited:
            continue
        visited.add(node_id)
        count += 1

        # node label
        label = f"T{current.timeslot}\nB{current.battery}"
        net.add_node(node_id, label=label, title=label, color="#a6cee3")

        for edge in current.children:
            child = edge.child
            if not child:
                continue
            child_id = str(id(child))
            label_text = f"Task {edge.task['id']}\nQ={edge.task['quality']}"
            color = "#1f78b4"

            # add child node if not seen yet
            if child_id not in visited:
                net.add_node(
                    child_id,
                    label=f"T{child.timeslot}\nB{child.battery}",
                    title=f"Battery={child.battery}, Timeslot={child.timeslot}",
                    color="#b2df8a"
                )
                queue.append(child)

            # Add edge with quality label
            net.add_edge(node_id, child_id, label=label_text, color=color, title=f"Quality={edge.task['quality']}")
    net.write_html("tree.html")
'''
Tasks = Task_sets[0]
curr_node = Node(B_start, 0)
resu, bp, bq, bpb = mcts(curr_node, 500)
quality = 0
while len(curr_node.children) != 0:
    move = curr_node.get_best_move()
    print(curr_node.timeslot, curr_node.battery, quality, move.task)
    quality += move.task["quality"]
    curr_node = move.child


print(curr_node.timeslot, curr_node.battery, quality)
print(bp, bq, bpb, len(bp))
'''
eval_iter_battery()


