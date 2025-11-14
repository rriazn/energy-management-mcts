import math
import random
import statistics
from collections import deque
import plotly.express as px
import numpy as np
import pandas as pd
from pyvis.network import Network


class Edge:
    def __init__(self, parent, child, task):
        self.parent = parent
        self.child = child
        self.task = task
        self.visits = 0
        self.win_quality = 0


class Node:
    def __init__(self, battery, timeslot, parent=None):
        self.battery = battery
        self.timeslot = timeslot  # timeslot 1 meaning from 0 to 1
        self.parents = [parent]
        self.children = []
        self.possible_tasks = self.get_possible_tasks()

    def get_possible_tasks(self):
        return [] if self.timeslot == K \
            else list(filter(lambda t: self.battery + E[self.timeslot] - t["cost"] >= B_min, Tasks))

    def is_fully_expanded(self):
        return len(self.possible_tasks) == 0

    def is_terminal(self):
        return len(self.get_possible_tasks()) == 0 or self.timeslot == K

    # returns: created edge and information if a new node was created => selection can be stopped
    def expand(self):
        # look for unexplored children
        next_task = self.possible_tasks.pop()
        new_battery = min(B_max, self.battery + E[self.timeslot] - next_task["cost"])
        if nodes[self.timeslot, new_battery - B_min] is not None:
            # child already exists, add edge
            edge = Edge(self, nodes[self.timeslot, new_battery - B_min], next_task)
            self.children.append(edge)
            nodes[self.timeslot, new_battery - B_min].parents.append(edge)
            return edge, False
        else:
            # child doesn't yet exist, add it
            edge = Edge(self, None, next_task)
            edge.child = Node(new_battery, self.timeslot + 1, parent=edge)
            nodes[self.timeslot, new_battery - B_min] = edge.child
            self.children.append(edge)
            return edge, True

    def get_best_move(self, parent_edge_visits, c=math.sqrt(2)):
        try:
            return max(self.children, key=lambda edge: (edge.win_quality / edge.visits) + c *
                                                   math.sqrt(math.log(parent_edge_visits) / edge.visits))
        except ZeroDivisionError:
            print(len(list(filter(lambda e: e.visits == 0, self.children))))
            print(self.timeslot)
            exit(1)


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
    for edge in path:
        edge.visits += 1
        scaled_result = result
        edge.win_quality += scaled_result


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
        path = []
        task_path = []
        path_quality = 0
        new_node = False
        parent_edge_visits = j
        while not new_node:
            # select, create path
            while not node.is_terminal() and node.is_fully_expanded():
                best_move = node.get_best_move(parent_edge_visits)
                node = best_move.child
                parent_edge_visits = best_move.visits
                path.append(best_move)
                task_path.append(best_move.task)
                path_quality += best_move.task["quality"]
            # expand
            if not node.is_terminal():
                result, new_node = node.expand()
                node = result.child
                path.append(result)
                task_path.append(result.task)
                path_quality += result.task["quality"]
            else:
                break



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
    k = 1.5
    diff = max(0, B_start - B_lvl)  # only penalize if below start
    scale = diff / B_min
    penalty = quality * (1 - math.exp(-k * scale))
    return quality - penalty


Tasks = [{'id': 1, 'cost': 3, 'quality': 5},
         {'id': 2, 'cost': 2, 'quality': 3},
         {'id': 3, 'cost': 4, 'quality': 6},
         {'id': 4, 'cost': 8, 'quality': 10},
         {'id': 5, 'cost': 1, 'quality': 1}]
B_start = 20
B_max = 30
B_min = 10

E = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4]
K = 24


nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)

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


evaluate(1000)
'''

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
    fig = px.scatter(x=x_axis, y=y_axis)
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


curr_node = Node(B_start, 0)
resu, bp, bq, bpb = mcts(curr_node, 150)
quality = 0
par_edge_visits = 150
while len(curr_node.children) != 0:
    move = curr_node.get_best_move(par_edge_visits)
    print(curr_node.timeslot, curr_node.battery, quality, move.task)
    par_edge_visits = move.visits
    quality += move.task["quality"]
    curr_node = move.child


print(curr_node.timeslot, curr_node.battery, quality)
print(bp, bq, bpb, len(bp))
'''
eval_iterations()
'''

