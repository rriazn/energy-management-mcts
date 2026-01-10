import numpy as np

K = 24
B_max = 50
B_min = 10
B_start = 30
E = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4]
nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)


Tasks = [{'id': 1, 'cost': 4, 'quality': 6},
     {'id': 2, 'cost': 3, 'quality': 5},
     {'id': 3, 'cost': 5, 'quality': 7},
     {'id': 4, 'cost': 8, 'quality': 10},
     {'id': 5, 'cost': 2, 'quality': 3},
     {'id': 6, 'cost': 1, 'quality': 1}]

max_quality = max(t["quality"] for t in Tasks)

def calc_quality_at_end(timeslot, battery_level):
    remaining_slots = K - timeslot
    return remaining_slots * max_quality

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
        self.quality_at_end = calc_quality_at_end(timeslot, battery_level)

def reconstruct_path(node):
    path = []
    quality = 0
    while node.best_parent is not None:
        path.append(node.best_parent.task["id"])
        quality += node.best_parent.task["quality"]
        node = node.best_parent.parent
    return list(reversed(path)), quality


def a_star(start_node):
    open_list = [start_node]
    closed_list = []

    while open_list:
        # Pick node with highest f = g + h
        best_node = max(open_list, key=lambda n: n.best_quality + n.quality_at_end)
        open_list.remove(best_node)
        closed_list.append(best_node)

        # If we reached the last timeslot, return best path
        if best_node.timeslot == K and best_node.battery_level >= B_start:
            return reconstruct_path(best_node)
        elif best_node.timeslot == K:
            continue
        # Expand node
        for t in Tasks:
            new_battery = min(B_max, best_node.battery_level + E[best_node.timeslot] - t["cost"])

            # Skip impossible battery states
            if new_battery < B_min:
                continue

            next_timeslot = best_node.timeslot + 1
            child_quality = best_node.best_quality + t["quality"]

            # Retrieve or create node
            node = nodes[best_node.timeslot][new_battery - B_min]

            if node is not None:
                # Node already exists -> check if new path is better
                old_score = node.best_quality + node.quality_at_end
                new_score = child_quality + calc_quality_at_end(next_timeslot, new_battery)
                if old_score >= new_score:
                    continue

                # Update node with better path
                node.best_quality = child_quality
                node.best_parent.task = t
                node.best_parent.parent = best_node

                if node not in open_list and node not in closed_list:
                    open_list.append(node)

            else:
                # Create new node
                node = Node(new_battery, next_timeslot, best_node, child_quality)
                nodes[best_node.timeslot][new_battery - B_min] = node
                node.best_parent = Edge(t, best_node, node)
                open_list.append(node)


    return None  # No solution found

print(a_star(Node(B_start, 0, None, 0)))



