import math
import numpy as np
from collections import deque
from pyvis.network import Network


E = [3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 5, 8, 9, 10, 10, 9, 8, 6]
thresholds = None

K = 24         # timeslots
B_start = 80
B_max = 100
B_min = 60


Tasks = [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 5},
     {'id': 3, 'cost': 5, 'quality': 7},
     {'id': 4, 'cost': 8, 'quality': 10},
     {'id': 5, 'cost': 2, 'quality': 3},
     {'id': 6, 'cost': 1, 'quality': 1}]

beam_width = 2
k_val = 10

nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)


class Edge:
    def __init__(self, task, parent, child):
        self.task = task
        self.parent = parent
        self.child = child


class Node:
    def __init__(self, battery_level, timeslot, parent, best_quality):
        self.battery_level = battery_level
        self.timeslot = timeslot
        self.parents = [parent]
        self.children = []
        self.best_quality = best_quality
        self.best_parent = parent


def calculate_thresholds():
    K = len(E)

    # find drought region
    drought_start = next((i for i in range(1, K) if E[i] == 0 and E[i-1] > 0), 0)

    drought_end = max((i for i in range(K - 1) if E[i] == 0 and E[i + 1] > 0), default=K-1)

    max_val = max(E)

    thresholds = np.zeros(K)

    peak = B_max   # how high we hoard before the drought
    if drought_end < drought_start:
        for k in range(drought_end):                # wait until drought is over
            thresholds[k] = B_start
        for k in range(drought_end, drought_start):     # rise
            thresholds[k] = B_start + (peak - B_start) * (k / drought_start)
        length = K - drought_start
        for i, k in enumerate(range(drought_start, K - 1)):
            thresholds[k] = peak - (peak - B_start) * (i / length)
        thresholds[-1] = B_start
    else:
        # Rising phase (harvest region)
        for k in range(drought_start):
            thresholds[k] = B_start + (peak - B_start) * (k / drought_start)

        # Falling phase (drought)
        drought_len = drought_end - drought_start + 1
        for i, k in enumerate(range(drought_start, drought_end + 1)):
            thresholds[k] = peak - (peak - B_start) * (i / drought_len)

        # After drought stay the same
        for k in range(drought_end + 1, K):
            thresholds[k] = B_start

    return thresholds.tolist()




def penalize(edge: Edge):
    if edge.child.battery_level >= thresholds[edge.child.timeslot - 1]:
        return edge.task["quality"]
    if edge.child.battery_level == B_min:
        return 0
    difference = thresholds[edge.child.timeslot - 1] - edge.child.battery_level
    k = k_val
    scale = difference / 10
    penalty = edge.task["quality"] * (1 - math.exp(-k * scale))
    return edge.task["quality"] - penalty


def expand(node: Node):
    for t in Tasks:
        battery_lvl = min(B_max, node.battery_level + E[node.timeslot] - t["cost"])
        if battery_lvl >= B_min:
            if nodes[node.timeslot][battery_lvl - B_min] is not None:
                # Node exists already -> add edge only
                edge = Edge(t, node, nodes[node.timeslot][battery_lvl - B_min])
                nodes[node.timeslot][battery_lvl - B_min].parents.append(edge)
                node.children.append(edge)
                if node.best_quality + t["quality"] > nodes[node.timeslot][battery_lvl - B_min].best_quality:
                    nodes[node.timeslot][battery_lvl - B_min].best_quality = node.best_quality + t["quality"]
                    nodes[node.timeslot][battery_lvl - B_min].best_parent = edge
            else:
                # Node doesnt exist -> add new node and edge
                edge = Edge(t, node, None)
                nodes[node.timeslot][battery_lvl - B_min] = Node(battery_lvl, node.timeslot + 1, edge, node.best_quality +
                                                                 t["quality"])
                edge.child = nodes[node.timeslot][battery_lvl - B_min]
                node.children.append(edge)


def evaluate(node):
    best_children = []
    for edge in node.children:
        edge_val = penalize(edge)
        if len(best_children) < beam_width:
            best_children.append((edge, edge_val))
        else:
            # remove worst from best_children if current edge is better
            minimum = min(best_children, key=lambda tpl: tpl[1])
            if minimum[1] < edge_val:
                best_children.remove(minimum)
                best_children.append((edge, edge_val))
    return list(map(lambda x: x[0].child, best_children))


def beam_search(root):
    global nodes, thresholds
    # reset
    nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)

    thresholds = calculate_thresholds()
    last_timeslot_nodes = [root] # start at root
    # assert beam_width <= len(Tasks) # sanity check
    for i in range(K):
        this_timeslot_nodes = [] # nodes chosen in previous iteration
        for curr_node in last_timeslot_nodes:
            expand(curr_node)
            best_children = evaluate(curr_node)
            for child in best_children:
                if child not in this_timeslot_nodes:
                    this_timeslot_nodes.append(child) # memorize chosen nodes
        last_timeslot_nodes = this_timeslot_nodes
    return last_timeslot_nodes, root


def visualize_tree(root, max_nodes=1000):
    """make a visual, tree-like graphic of the created graph"""
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

        label = f"T{current.timeslot}\nB{current.battery_level}"

        net.add_node(
            node_id,
            label=label,
            title=label,
            color="#a6cee3",
            level=current.timeslot
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
                    label=f"T{child.timeslot}\nB{child.battery_level}",
                    title=f"Battery={child.battery_level}, Timeslot={child.timeslot}",
                    color="#b2df8a",
                    level=child.timeslot
                )
                queue.append(child)

            net.add_edge(
                node_id,
                child_id,
                label=label_text,
                color="#1f78b4",
                title=f"Quality={edge.task['quality']}"
            )

    net.write_html("beam_search_tree.html")

# example usage:
'''
ltn, rt = beam_search(Node(B_start, 0, None, 0))
visualize_tree(rt)
for node in ltn:
    print("Node: ", node.battery_level, "; Quality: ", node.best_quality)

ns = list(filter(lambda n: n.battery_level >= B_start, ltn))
node = max(ns, key=lambda n: n.best_quality)
print(node.best_quality, node.battery_level)
tasks = []
while node.parents[0] is not None:
    tasks.append(node.best_parent.task["id"])
    node = node.best_parent.parent
tasks = list(reversed(tasks))

quality = 0
battery = B_start
for k in range(K):
    task = next(t for t in Tasks if t["id"] == tasks[k])
    quality += task["quality"]
    battery = min(B_max, battery - task["cost"] + E[k])
    print(task["quality"], quality, E[k], task["cost"], battery)
    #print(task["cost"], task["quality"])


print(calculate_thresholds())
'''