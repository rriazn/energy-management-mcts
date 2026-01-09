import math
from collections import deque

import numpy as np
from pyvis.network import Network

K = 24
B_max = 50
B_min = 10
B_start = 30
E = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4]


Tasks = [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 5},
     {'id': 3, 'cost': 5, 'quality': 7},
     {'id': 4, 'cost': 8, 'quality': 10},
     {'id': 5, 'cost': 2, 'quality': 3},
     {'id': 6, 'cost': 1, 'quality': 1}]

beam_width = 3* round(len(Tasks) / 3)

nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)


class Edge:
    def __init__(self, task, parent, child):
        self.task = task
        self.parent = parent
        self.child = child


class Node:
    def __init__(self, battery_level, timeslot, parent, best_quality,):
        self.battery_level = battery_level
        self.timeslot = timeslot
        self.parents = [parent]
        self.children = []
        self.best_quality = best_quality
        self.best_parent = parent


def penalize(edge: Edge):
    if edge.child.battery_level == B_min:
        return 0
    difference = B_start - edge.child.battery_level
    k = 10
    scale = difference / B_min
    penalty = edge.task["quality"] * (1 - math.exp(-k * scale))
    return edge.task["quality"] - penalty


def expand(node: Node):
    for t in Tasks:
        battery_lvl = min(B_max, node.battery_level + E[node.timeslot] - t["cost"])
        if battery_lvl >= B_min:
            if nodes[node.timeslot][battery_lvl - B_min] is not None:
                edge = Edge(t, node, nodes[node.timeslot][battery_lvl - B_min])
                nodes[node.timeslot][battery_lvl - B_min].parents.append(edge)
                node.children.append(edge)
                if node.best_quality + t["quality"] > nodes[node.timeslot][battery_lvl - B_min].best_quality:
                    nodes[node.timeslot][battery_lvl - B_min].best_quality = node.best_quality + t["quality"]
                    nodes[node.timeslot][battery_lvl - B_min].best_parent = edge
            else:
                edge = Edge(t, node, None)
                nodes[node.timeslot][battery_lvl - B_min] = Node(battery_lvl, node.timeslot + 1, edge, node.best_quality +
                                                                 t["quality"])
                edge.child = nodes[node.timeslot][battery_lvl - B_min]
                node.children.append(edge)


def evaluate(node):
    best_children = []
    for edge in node.children:
        edge_val = edge.task["quality"] if edge.child.battery_level >= B_start else penalize(edge)
        if len(best_children) < beam_width:
            best_children.append((edge, edge_val))
        else:
            minimum = min(best_children, key=lambda tpl: tpl[1])
            if minimum[1] < edge_val:
                best_children.remove(minimum)
                best_children.append((edge, edge_val))
    return list(map(lambda x: x[0].child, best_children))


def beam_search():
    root = Node(B_start, 0, None, 0)
    last_timeslot_nodes = [root]
    assert beam_width <= len(Tasks)
    for i in range(K):
        this_timeslot_nodes = []
        for curr_node in last_timeslot_nodes:
            expand(curr_node)
            best_children = evaluate(curr_node)
            for child in best_children:
                if child not in this_timeslot_nodes:
                    this_timeslot_nodes.append(child)
        last_timeslot_nodes = this_timeslot_nodes
    return last_timeslot_nodes, root

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
        label = f"T{current.timeslot}\nB{current.battery_level}"
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
                    label=f"T{child.timeslot}\nB{child.battery_level}",
                    title=f"Battery={child.battery_level}, Timeslot={child.timeslot}",
                    color="#b2df8a"
                )
                queue.append(child)

            # Add edge with quality label
            net.add_edge(node_id, child_id, label=label_text, color=color, title=f"Quality={edge.task['quality']}")
    net.write_html("beam_search_tree.html")


ltn, rt = beam_search()
for node in ltn:
    print("Node: ", node.battery_level, "; Quality: ", node.best_quality)

node = ltn[2]
while len(node.parents) != 0:
    print(node.best_parent.task["id"])
    node = node.best_parent.parent

visualize_tree(rt)
