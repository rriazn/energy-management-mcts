import math
from collections import deque

from pyvis.network import Network


class Edge:
    def __init__(self, task, parent, child):
        self.task = task
        self.parent = parent
        self.child = child


class Node:
    def __init__(self, battery_bin, timeslot, parent):
        self.battery_bin = battery_bin
        self.timeslot = timeslot
        self.parents = [parent]
        self.children = []

    def get_possible_tasks(self):
        return list(filter(lambda t: bins[self.battery_bin][-1] + E[self.timeslot] - t["cost"] >= B_min, Tasks))


def generate_tree():
    root = Node(get_bin(B_start), 0, None)
    global nodes, edges
    nodes += 1
    last_timeslot = [root]
    for i in range(K):
        battery_bin_nodes = [None for i in range(len(bins))]
        for j in last_timeslot:
            if j is not None:
                possible_tasks = j.get_possible_tasks()
                for t in possible_tasks:
                    # add all possíble edges for this battery bin and task
                    for b in bins[j.battery_bin]:
                        battery_level = min(B_max, b + E[j.timeslot] - t["cost"])
                        if battery_level < B_min:
                            continue
                        new_bin = get_bin(battery_level)
                        edge = None
                        # node already exists
                        if battery_bin_nodes[new_bin] is not None:
                            # check if edge already exits as to not add it again
                            if not any(e.task == t and e.child.battery_bin == new_bin for e in j.children):
                                edge = Edge(t, j, battery_bin_nodes[new_bin])
                                edges += 1
                                battery_bin_nodes[new_bin].parents.append(edge)
                            else:
                                continue
                        # node doesnt exit yet, create it and edge
                        else:
                            edge = Edge(t, j, None)
                            edges += 1
                            battery_bin_nodes[new_bin] = Node(new_bin, j.timeslot + 1, edge)
                            nodes += 1
                            edge.child = battery_bin_nodes[new_bin]
                        j.children.append(edge)
        last_timeslot = battery_bin_nodes
    return root


def get_bin(B_lvl):
    return math.floor((B_lvl - B_min) / len(bins[0]))


def visualize_tree(root, max_nodes=300):
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

        # Node label
        label = f"T{current.timeslot}\nB{current.battery_bin}"
        net.add_node(node_id, label=label, title=label, color="#a6cee3")

        for edge in current.children:
            child = edge.child
            if not child:
                continue
            child_id = str(id(child))
            label_text = f"Task {edge.task['id']}\nQ={edge.task['quality']}"
            color = "#1f78b4"

            # Add child node if not seen yet
            if child_id not in visited:
                net.add_node(
                    child_id,
                    label=f"T{child.timeslot}\nB{child.battery_bin}",
                    title=f"Battery Bin={child.battery_bin}, Timeslot={child.timeslot}",
                    color="#b2df8a"
                )
                queue.append(child)

            # Add edge with quality label
            net.add_edge(node_id, child_id, label=label_text, color=color, title=f"Quality={edge.task['quality']}")

    # Save and open in browser
    net.write_html("tree_with_quality.html")
    print("✅ Tree visualization saved as tree_with_quality.html — open it in your browser.")


Tasks = [{'id': 1, 'cost': 3, 'quality': 5},
         {'id': 2, 'cost': 2, 'quality': 3},
         {'id': 3, 'cost': 4, 'quality': 6},
         {'id': 4, 'cost': 8, 'quality': 10},
         {'id': 5, 'cost': 1, 'quality': 1}]
B_start = 20
B_max = 30
B_min = 10

E = [1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0]
K = 24

bins = [[10, 11, 12], [13, 14, 15], [16, 17, 18], [19, 20, 21], [22, 23, 24], [25, 26, 27], [28, 29, 30]]


nodes, edges = 0, 0
root = generate_tree()
#visualize_tree(root)

print(nodes, edges)
