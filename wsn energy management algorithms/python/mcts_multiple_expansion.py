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
        self.timeslot = timeslot  # if timeslot = n, it is the timeslot after the n-th task
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

        # loop until there are no more children to be added
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
        # UCT, but without exploration parameter, if all children have win_quality 0 choose the cheapest
        #if all(edge.child.win_quality == 0 for edge in self.children):
            #return min(self.children, key=lambda e: e.task["cost"])
        return max(self.children, key=lambda edge: (edge.child.win_quality / edge.child.visits)
                   + c * math.sqrt(math.log(self.visits) / edge.child.visits))


    def simulate(self, qual):
        # simulation state
        sim_timeslot = self.timeslot
        sim_state_battery = self.battery
        sim_state_quality = qual
        sim_path = []

        # simulate until reaching leaf
        while True:
            # full path found
            if sim_timeslot == K:
                return penalized_quality(sim_state_quality,
                                         sim_state_battery), sim_path, sim_state_quality, sim_state_battery

            # which tasks can be assigned without violating B >= B_min
            available_tasks = list(filter(lambda t: sim_state_battery + E[sim_timeslot] -
                                                    t["cost"] >= B_min, Tasks))

            # leaf node without full path -> return 0
            if not available_tasks:
                return 0, [], 0, 0
            chosen_task = random.choice(available_tasks)

            # force it to take highest quality task, that does not cause the quality to go below B_start
            # in order to use battery properly
            if sim_state_battery == B_max:
                chosen_task = max(list(filter(
                    lambda t: sim_state_battery + E[sim_timeslot] - t["cost"] >= B_start, available_tasks
                )), key=lambda task: task["quality"])

            # update sim state with chosen task
            sim_timeslot += 1
            sim_state_battery = min(B_max, sim_state_battery - chosen_task["cost"] + E[sim_timeslot - 1])
            sim_state_quality += chosen_task["quality"]
            sim_path.append(chosen_task["id"])


def backpropagate(summed_up_result, path, edges_count):
    # apply simulation values to all tasks in selection path, update visit count with number of simulations
    for node in path:
        node.visits += edges_count
        node.win_quality += summed_up_result


def upgrade(path, end_battery):
    # index to get certain task by their id
    task_index = {task["id"]: i for i, task in enumerate(Tasks)}

    # calculate battery value in each timeslot for current solution
    battery_vals = [B_start]
    for i in range(K):
        battery_vals.append(battery_vals[-1] + E[i] - Tasks[task_index[path[i]]]["cost"])

    # monitor battery, so it never goes below B_min
    smallest_battery = max(end_battery, battery_vals[-1])
    battery_at_timeslot = end_battery  # battery before executing task at timeslot i

    # go backwards through solution and try to upgrade the tasks until it is not possible anymore
    for i in range(K - 1, -1, -1):
        old_task = Tasks[task_index[path[i]]]
        best_task = None

        # find highest quality task that satisfies: battery at timeslot >= B_min and B_end >= B_start
        for j in range(task_index[path[i]]):
            new_task = Tasks[j]
            cost_diff = new_task["cost"] - old_task["cost"]
            if end_battery - cost_diff >= B_start \
                    and battery_at_timeslot - cost_diff >= B_min \
                    and smallest_battery - cost_diff >= B_min:
                best_task = new_task
                break

        # no better task found (but better tasks exist): stop upgrading
        if best_task is None and old_task["id"] != Tasks[0]["id"]:
            break
        # no better task exist -> continue with next timeslot
        elif old_task["id"] == Tasks[0]["id"]:
            continue

        # apply new better task
        cost_diff = best_task["cost"] - old_task["cost"]
        end_battery -= cost_diff
        battery_at_timeslot -= cost_diff
        smallest_battery -= cost_diff
        smallest_battery = min(smallest_battery, battery_at_timeslot)

        path[i] = best_task["id"]
        battery_at_timeslot = battery_vals[i]

    # recalculate quality
    qual = 0
    for i in path:
        qual += Tasks[task_index[i]]["quality"]
    return qual, path, end_battery


def mcts(root, iterations):
    global nodes, Tasks

    # reset graph state
    nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)

    # sort task by cost in descending order, eliminate all tasks that are dominated by another task
    eliminate_dominated_tasks()

    # reset possible tasks in root to account for sorted tasks
    root.possible_tasks = root.get_possible_tasks()

    # always save the best path explored by selection, expansion and simulation
    best_path = []
    best_quality = 0
    best_path_remaining_battery = 0

    for j in range(iterations):
        node = root
        result = []

        # also memorize chosen path for backpropagation
        path = [node]
        task_path = []
        path_quality = 0

        # select until expand creates at least one new node
        while len(result) == 0:
            # select, create path
            while not node.is_terminal() and node.is_fully_expanded():
                best_move = node.get_best_move()

                node = best_move.child
                path.append(node)
                task_path.append(best_move.task["id"])
                path_quality += best_move.task["quality"]
            # expand
            if not node.is_terminal():
                # result is now a list of all newly created outgoing edges to newly created nodes
                result = node.expand()
            else:
                # selected until a leaf node
                break
        if len(result) != 0:
            # not a leaf node selected

            # summed up simulation results to backpropagate
            summed_up_result = 0

            # do simulation for each new child node
            for edge in result:
                # simulate
                node = edge.child
                backpropagation_value, sim_path, sim_quality, sim_battery = node.simulate(
                    path_quality + edge.task["quality"])

                # update best path, if selection and simulation path together are better
                if backpropagation_value > best_quality and sim_battery >= B_start:
                    best_path = task_path + [edge.task["id"]] + sim_path
                    best_quality = sim_quality
                    best_path_remaining_battery = sim_battery
                summed_up_result += backpropagation_value
                node.visits += 1
                node.win_quality += backpropagation_value
            # backpropagation
            backpropagate(summed_up_result, path, len(result))
        else:
            # leaf node selected

            backpropagation_value, sim_path, sim_quality, sim_battery = node.simulate(path_quality)

            # update best path, if selection and simulation path together are better
            if backpropagation_value > best_quality and sim_battery >= B_start:
                best_path = task_path + [edge.task] + sim_path
                best_quality = sim_quality
                best_path_remaining_battery = sim_battery

            # backpropagation
            backpropagate(backpropagation_value, path, 1)

    # revisit path to use excess energy (optional, but uses energy budged better)
    #if len(best_path) != 0:
        #best_quality, best_path, best_path_remaining_battery = upgrade(best_path, best_path_remaining_battery)
    return root, best_path, best_quality, best_path_remaining_battery


def penalized_quality(quality, B_lvl):
    if B_lvl >= B_start:
        return quality
    k = k_val
    diff = max(0, B_start - B_lvl)
    scale = diff / B_min
    penalty = quality * (1 - math.exp(-k * scale))
    return quality - penalty


def eliminate_dominated_tasks():
    global Tasks

    # sort ascending by cost first for pruning logic
    tasks_sorted = sorted(Tasks, key=lambda t: (t["cost"], -t["quality"]))

    pruned = []
    best_quality = 0

    # Pareto pruning pass
    for t in tasks_sorted:
        if t["quality"] > best_quality:
            pruned.append(t)
            best_quality = t["quality"]

    # return descending order by cost
    Tasks = sorted(pruned, key=lambda t: t["cost"], reverse=True)

def visualize_tree(root, max_nodes=1000):
    net = Network(height='800px', width='100%', directed=True)

    # Enable hierarchical layout
    net.set_options("""
    {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "levelSeparation": 200,
          "nodeSpacing": 160
        }
      },
      "physics": {
        "enabled": false
      }
    }
    """)

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

        label = f"T{current.timeslot}\nB{current.battery}"

        net.add_node(
            node_id,
            label=label,
            title=label,
            color="#a6cee3",
            level=current.timeslot   # <-- THIS creates tiers
        )

        for edge in current.children:
            child = edge.child
            if not child:
                continue

            child_id = str(id(child))
            label_text = f"τ {edge.task['id']}\nQ={edge.task['quality']}"

            if child_id not in visited:
                net.add_node(
                    child_id,
                    label=f"T{child.timeslot}\nB{child.battery}",
                    title=f"Battery={child.battery}, Timeslot={child.timeslot}",
                    color="#b2df8a",
                    level=child.timeslot   # <-- child tier
                )
                queue.append(child)

            net.add_edge(
                node_id,
                child_id,
                label=label_text,
                color="#1f78b4",
                title=f"Quality={edge.task['quality']}"
            )

    net.write_html("mcts_tree.html")


# energy harvesting predicitons in 10mAh for 01. June 2026 in Greenwich, UK (Clearsky)
# for the setup specified in energy_harvesting_prediction.py
E = [3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 5, 8, 9, 10, 10, 9, 8, 6]

K = 24  # timeslots
B_start = 80
B_max = 100
B_min = 60
k_val = 1
nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)  # find nodes based on timeslot & battery

Tasks = [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 5},
     {'id': 3, 'cost': 5, 'quality': 7},
     {'id': 4, 'cost': 8, 'quality': 10},
     {'id': 5, 'cost': 2, 'quality': 3},
     {'id': 6, 'cost': 1, 'quality': 1}]

# example usage:
'''
curr_node = Node(B_start, 0)
res = mcts(curr_node, 6)
visualize_tree(res[0])
print(res, res[0].win_quality)
quality = 0

nod = res[0]
while True:
    try:
        bt = nod.get_best_move()
    except ValueError:
        break
    print(bt.task["cost"])
    nod = bt.child

battery = B_start
for k in range(K):
    task = next(t for t in Tasks if t["id"] == res[1][k])
    quality += task["quality"]
    battery = min(B_max, battery - task["cost"] + E[k])
    print(task["quality"], quality, E[k], task["cost"], battery)
    #print(task["cost"], task["quality"])

# print(curr_node.timeslot, curr_node.battery, quality)
# print(res[0], res[1], res[2], res[3], len(res[1]))
'''