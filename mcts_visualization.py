import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile
import os
import random
import math
import numpy as np



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
                self.children.append(Edge(self, nodes[self.timeslot, new_battery - B_min], next_task))
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


def mcts_one_iteration(start_node):
    root = start_node

    # save the best path explored by selection, expansion and simulation
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
    # backpropagate
    backpropagate(res, path)

    return path, task_path


def penalized_quality(quality, B_lvl):
    return 0


def visualize_tree(root, highlight_nodes):
    net = Network(height="600px", width="100%", bgcolor="#111", font_color="white", directed=True)
    q = [root]
    visited = set()

    while q:
        node = q.pop(0)
        nid = f"{node.timeslot}_{node.battery}"
        if nid not in visited:
            visited.add(nid)
            color = "orange" if node in highlight_nodes else "skyblue"
            net.add_node(
                nid,
                label=f"T{node.timeslot},B{node.battery},V{node.visits}",
                color=color,
                size=15,
            )
            for e in node.children:
                child = e.child
                cid = f"{child.timeslot}_{child.battery}"
                if cid not in net.get_nodes():
                    ccolor = "orange" if child in highlight_nodes else "lightgreen"
                    net.add_node(
                        cid,
                        label=f"T{child.timeslot},B{child.battery},V{child.visits}",
                        color=ccolor,
                        size=15,
                    )
                net.add_edge(nid, cid, label=f"Q{e.task['quality']}/C{e.task['cost']}")
                q.append(child)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    net.write_html(tmp.name)  # ✅ safer than net.show()
    return tmp.name


Tasks = [{'id': 1, 'cost': 3, 'quality': 5},
         {'id': 2, 'cost': 2, 'quality': 3},
         {'id': 3, 'cost': 4, 'quality': 6},
         {'id': 4, 'cost': 8, 'quality': 10},
         {'id': 5, 'cost': 1, 'quality': 1}]
B_start, B_max, B_min = 20, 30, 10
E = [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4]
K = 5
nodes = np.full((K, B_max + 1 - B_min), None, dtype=object)


st.set_page_config(layout="wide")
st.title("🧠 Live MCTS Tree Visualizer")

if "root" not in st.session_state:
    root = Node(B_start, 0)
    st.session_state.root = root
    st.session_state.iter_count = 0

col1, col2 = st.columns([1, 2])
with col1:
    if st.button("Run one MCTS iteration"):
        path, task_path = mcts_one_iteration(st.session_state.root)
        st.session_state.last_path = path
        st.session_state.iter_count += 1
        st.success(f"Iteration {st.session_state.iter_count} completed! Path length {len(path)}.")

with col2:
    st.markdown("#### Tree Visualization")
    if "last_path" in st.session_state:
        html_path = visualize_tree(st.session_state.root, st.session_state.last_path)
    else:
        html_path = visualize_tree(st.session_state.root, [])
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    st.components.v1.html(html_code, height=600, scrolling=True)
