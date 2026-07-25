import math
from collections import deque

from pyvis.network import Network

K = 25
nodes = 0
edges = 0

Tasks = [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 4},
     {'id': 3, 'cost': 5, 'quality': 7},
     {'id': 4, 'cost': 10, 'quality': 12},
     {'id': 5, 'cost': 2, 'quality': 2},
     {'id': 6, 'cost': 1, 'quality': 1}]


class Edge:
    def __init__(self, task, parent, child):
        self.task = task
        self.parent = parent
        self.child = child


class Node:
    def __init__(self, battery_level, timeslot, parent):
        self.battery_level = battery_level
        self.timeslot = timeslot
        self.parents = [parent]
        self.children = []


def generate_graph():
    root = Node(0, 0, None)
    global nodes, edges, Tasks
    nodes += 1
    last_timeslot = [root]
    Tasks = sorted(Tasks, key=lambda t: t["cost"])
    for i in range(K):
        if len(last_timeslot) != 0:
            range_min = min(last_timeslot, key=lambda node: node.battery_level if node is not None else math.inf).battery_level + Tasks[0]["cost"]
            range_max = max(last_timeslot, key=lambda node: node.battery_level if node is not None else 0).battery_level + Tasks[-1]["cost"]
            battery_level_nodes = [None for i in range(range_min, range_max + 1)]
        for j in last_timeslot:
            if j is not None:
                for t in Tasks:
                    battery_level = j.battery_level + t["cost"] - range_min
                    edge = None
                    if battery_level_nodes[battery_level] is not None:
                        edge = Edge(t, j, battery_level_nodes[battery_level])
                        edges += 1
                        battery_level_nodes[battery_level].parents.append(edge)
                    else:
                        edge = Edge(t, j, None)
                        edges += 1
                        battery_level_nodes[battery_level] = Node(battery_level + range_min, j.timeslot + 1, edge)
                        nodes += 1
                        edge.child = battery_level_nodes[battery_level]
                    j.children.append(edge)
        last_timeslot = battery_level_nodes
    return root


def visualize_graph(root, max_nodes=1000100):
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
        label = f"T{current.timeslot}\nB{current.battery_level}"
        node_color = "#0000ff" if len(current.children) == 0 else "#a6cee3"
        net.add_node(node_id, label=label, title=label, color=node_color)

        for edge in current.children:
            child = edge.child
            if not child:
                continue
            child_id = str(id(child))
            label_text = f"Task {edge.task['id']}\nQ={edge.task['quality']}"
            color = "#1f78b4"

            if child_id not in visited:
                child_color = "#0000ff" if len(child.children) == 0 else "#b2df8a"
                net.add_node(
                    child_id,
                    label=f"T{child.timeslot}\nB{child.battery_level}",
                    title=f"Battery={child.battery_level}, Timeslot={child.timeslot}",
                    color=child_color
                )
                queue.append(child)

            net.add_edge(
                node_id,
                child_id,
                label=label_text,
                color=color,
                title=f"Quality={edge.task['quality']}",
                length=300
            )

    # Hierarchical layout: root at top, leaves at bottom
    net.set_options("""
    {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed"
        }
      },
      "physics": {
        "enabled": false
      },
      "interaction": {
        "dragNodes": true
      }
    }
    """)

    net.write_html("tree_with_quality.html")
    print("✅ Tree visualization saved as tree_with_quality.html — open it in your browser.")


root = generate_graph()
visualize_graph(root)
