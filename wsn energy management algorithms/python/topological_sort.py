import numpy as np

E = [2,0,0,2,4,6]

K = 6         # timeslots
B_start = 40
B_max = 50
B_min = 30


Tasks = [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 5},
     {'id': 3, 'cost': 2, 'quality': 3},
     {'id': 4, 'cost': 1, 'quality': 1}]

top_ordering = []

nodes = np.full((K + 1, B_max + 1 - B_min), None, dtype=object)


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
        self.possible_tasks = self.get_possible_tasks()
        self.best_quality = best_quality
        self.best_parent = parent


    def get_possible_tasks(self):
        return [] if self.timeslot == K \
            else list(filter(lambda t: self.battery_level + E[self.timeslot] - t["cost"] >= B_min, Tasks))

    def dfs_topo(self):
        nodes[self.timeslot, self.battery_level - B_min] = self
        for i in self.possible_tasks:
            battery_lvl = min(B_max, self.battery_level + E[self.timeslot] - i["cost"])
            if nodes[self.timeslot + 1, battery_lvl - B_min] is None:
                edge = Edge(i, self, None)
                child = Node(battery_lvl, self.timeslot + 1, edge, self.best_quality + i["quality"])
                edge.child = child
                child.dfs_topo()
            else:
                edge = Edge(i, self, nodes[self.timeslot + 1, battery_lvl - B_min])
                self.children.append(edge)
                nodes[self.timeslot + 1, battery_lvl - B_min].parents.append(edge)
        top_ordering.append(self)


def find_best_path_topological(root):
    root.dfs_topo()
    global top_ordering
    top_ordering = reversed(top_ordering)
    leaves = []
    for node in top_ordering:
        if node.timeslot == K and node.battery_level >= B_start:
            leaves.append(node)
            continue
        for edge in node.children:
            v = edge.child
            if v.best_quality < node.best_quality + edge.task["quality"]:
                v.best_quality = node.best_quality + edge.task["quality"]
                v.best_parent = edge
    return max(leaves, key=lambda l: l.best_quality)


def reconstruct_path(leaf):
    path = []
    node = leaf
    for i in range(K):
        path.append(node.best_parent.task["id"])
        node = node.best_parent.parent
    return path, leaf.battery_level, leaf.best_quality

leaf = find_best_path_topological(Node(B_start, 0, None, 0))
solution = reconstruct_path(leaf)
print(solution)

