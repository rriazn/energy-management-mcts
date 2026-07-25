from collections import deque

from pyvis.network import Network

K = 6
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

    def get_possible_tasks(self):
        return list(filter(lambda t: self.battery_level + E[self.timeslot] - t["cost"] >= B_min, Tasks))


def generate_tree():
    root = Node(B_start, 0, None)
    global nodes, edges
    nodes += 1
    last_timeslot = [root]
    for i in range(K):
        battery_level_nodes = [None for i in range(B_min, B_max + 1)]
        for j in last_timeslot:
            if j is not None:
                possible_tasks = j.get_possible_tasks()
                for t in possible_tasks:
                    battery_level = min(B_max, j.battery_level + E[j.timeslot] - t["cost"]) - B_min
                    edge = None
                    if battery_level_nodes[battery_level] is not None:
                        edge = Edge(t, j, battery_level_nodes[battery_level])
                        edges += 1
                        battery_level_nodes[battery_level].parents.append(edge)
                    else:
                        edge = Edge(t, j, None)
                        edges += 1
                        battery_level_nodes[battery_level] = Node(battery_level + B_min, j.timeslot + 1, edge)
                        nodes += 1
                        edge.child = battery_level_nodes[battery_level]
                    j.children.append(edge)
        last_timeslot = battery_level_nodes
    return root

# time: O(V + E)
def find_best_path(root, visited=None):
    if visited is None:
        visited = {}

    if id(root) in visited:
        return visited[id(root)]

    best_task = None
    best_quality = -1

    # Leaf
    if len(root.children) == 0:
        # no full schedule or battery lower than start
        if root.timeslot != K or root.battery_level < B_start:
            visited[id(root)] = ([], -1)
        else:
            visited[id(root)] = ([], 0)
        return visited[id(root)]
    best_path = []
    # middle Node
    for edge in root.children:
        path, quality = find_best_path(edge.child, visited)
        if quality != -1:
            quality += edge.task["quality"]
            if quality > best_quality:
                best_quality = quality
                best_task = edge.task
                best_path = path
    best_path = [best_task] + best_path
    visited[id(root)] = (best_path, best_quality)

    return best_path, best_quality


def check_solution(solution):
    B_lvl = B_start
    for i in range(len(solution)):
        B_lvl = min(B_max, B_lvl + E[i] - solution[i]["cost"])
    return B_lvl >= B_start, B_lvl


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

        label = f"T{current.timeslot}\nB{current.battery_level}"

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
                    label=f"T{child.timeslot}\nB{child.battery_level}",
                    title=f"Battery={child.battery_level}, Timeslot={child.timeslot}",
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

    net.write_html("entire_tree.html")



Tasks = [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 5},
     {'id': 3, 'cost': 2, 'quality': 3},
     {'id': 4, 'cost': 1, 'quality': 1}]
K = 6         # timeslots
B_start = 40
B_max = 50
B_min = 30

E = [2,0,0,2,4,6]
E_2 = [1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0]


nodes = 0
edges = 0

roots = generate_tree()
visualize_tree(roots)
sol = find_best_path(roots)
print(sol)
print(check_solution(sol[0]))
print(nodes, edges)

