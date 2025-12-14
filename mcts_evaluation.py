import mcts_multiple_expansion as mcts
import numpy as np
import random
import statistics
import timeit
import plotly.express as px
from pyvis.network import Network
from collections import deque


def evaluate(iterations=100):
    battery_values = []
    quality_values = []
    battery_underflow = 0
    errors = 0
    no_full_path = 0
    for i in range(iterations):
        mcts.nodes = np.full((mcts.K, mcts.B_max + 1 - mcts.B_min), None, dtype=object)
        curr_node = mcts.Node(mcts.B_start, 0)
        error = False
        solution = None
        try:
            solution = mcts.mcts(curr_node, 200)
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
            if battery_values[-1] < mcts.B_start:
                battery_underflow += 1
            if curr_node.timeslot < 24:
                no_full_path += 1

    print(statistics.fmean(battery_values), statistics.fmean(quality_values), statistics.stdev(quality_values))


# evaluate(10000)


def eval_iterations():
    x_axis = []
    y_axis = []
    for i in range(1, 51, 1):
        x_axis.append(i)
        battery_values = []
        quality_values = []
        battery_underflow = 0
        errors = 0
        no_full_path = 0
        for j in range(100):
            mcts.nodes = np.full((mcts.K, mcts.B_max + 1 - mcts.B_min), None, dtype=object)
            curr_node = mcts.Node(mcts.B_start, 0)
            solution = mcts.mcts(curr_node, iterations=i)
            quality_values.append(solution[2])
            battery_values.append(solution[3])
            if battery_values[-1] < mcts.B_start:
                battery_underflow += 1
        y_axis.append(statistics.fmean(quality_values))
        print(statistics.fmean(quality_values))
    fig = px.line(
        x=x_axis,
        y=y_axis,
        markers=True,  # keeps the dots visible
        color_discrete_sequence=['#FF8C00']  # same color as before
    )
    fig.show()


def exists_full_path(root, depth):
    node = root
    while len(node.children) > 0:
        node = node.get_best_move().child
    if node.timeslot == depth:
        return True
    return False


def eval_iter_timeslots():
    x_axis = []
    y_axis = []

    for i in range(20, 60, 10):
        x_axis.append(i)
        times = []
        mcts.K = i
        for _ in range(1):
            mcts.nodes = np.full((mcts.K, mcts.B_max + 1 - mcts.B_min), None, dtype=object)
            root = mcts.Node(mcts.B_start, 0)

            # Start timing
            start = timeit.default_timer()
            res = (root, [], 0, 0)
            i = 0
            while len(res[1]) == 0:
                res = mcts.mcts(root, 1)
                i += 1

            # Stop timing
            end = timeit.default_timer()
            elapsed = (end - start) * 1000
            times.append(i)

        # Store mean execution time for this K
        y_axis.append(statistics.fmean(times))
        print(statistics.fmean(times))

    fig = px.line(
        x=x_axis,
        y=y_axis,
        markers=True,
        labels={"x": "K", "y": "mean time (s)"},
        color_discrete_sequence=["#FF8C00"]
    )
    fig.show()


def eval_iter_battery():
    x_axis = []
    y_axis = []
    p = 0

    for i in range(20, 200, 10):
        x_axis.append(i - mcts.B_min)
        times = []

        magnifier = i / 30
        mcts.B_max = i
        mcts.B_start = int((mcts.B_max + mcts.B_min) / 2)

        if magnifier != 1:
            mcts.E = list(map(lambda x: round(magnifier * x), mcts.E_b))
        else:
            mcts.E = mcts.E_b[::]

        mcts.Tasks = mcts.Task_sets[p]

        for _ in range(100):
            mcts.nodes = np.full((mcts.K, mcts.B_max + 1 - mcts.B_min), None, dtype=object)
            root = mcts.Node(mcts.B_start, 0)

            # Start timing
            start = timeit.default_timer()

            res = (root, [], 0, 0)

            while len(res[1]) == 0:
                res = mcts.mcts(root, 1)

            # Stop timing
            end = timeit.default_timer()
            elapsed = end - start
            elapsed_ms = elapsed * 1000  # convert to milliseconds
            times.append(elapsed_ms)

        y_axis.append(statistics.fmean(times))
        print(y_axis[-1])
        p += 1

    fig = px.line(
        x=x_axis,
        y=y_axis,
        markers=True,  # keeps the dots visible
        labels={"x": "B_max - B_min", "y": "mean time (ms)"},
        color_discrete_sequence=['#FF8C00']
    )
    fig.show()


def eval_iter_timeslots_battery():
    x_axis = []
    y_axis = []
    p = 0

    for i in range(20, 100, 10):
        x_axis.append(i - mcts.B_min)
        times = []

        magnifier = i / 30
        mcts.B_max = i
        mcts.B_start = int((mcts.B_max + mcts.B_min) / 2)
        mcts.K = i
        if magnifier != 1:
            mcts.E = list(map(lambda x: round(magnifier * x), mcts.E_b))
        else:
            mcts.E = mcts.E_b[::]

        mcts.Tasks = mcts.Task_sets[p]

        for _ in range(10):
            mcts.nodes = np.full((mcts.K, mcts.B_max + 1 - mcts.B_min), None, dtype=object)
            root = mcts.Node(mcts.B_start, 0)

            # Start timing
            start = timeit.default_timer()

            while not exists_full_path(root, i):
                mcts.mcts(root, 1)

            # Stop timing
            end = timeit.default_timer()
            elapsed = end - start
            elapsed_ms = elapsed * 1000  # convert to milliseconds
            times.append(elapsed_ms)

        y_axis.append(statistics.fmean(times))
        print(y_axis[-1])
        p += 1


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


def random_assignment_eval():
    quality_vals = []
    no_solution = 0
    not_energy_neutral = 0
    battery_underflow = 0
    for i in range(10000):
        qual = 0
        batt = mcts.B_start
        for j in range(mcts.K):
            task = random.choice(mcts.Tasks)
            qual += task["quality"]
            batt = min(mcts.B_max, batt + mcts.E[j] - task["cost"])
            if batt < mcts.B_min:
                no_solution += 1
                battery_underflow += 1
                break
            if j == mcts.K - 1:
                if batt < mcts.B_start:
                    no_solution += 1
                    not_energy_neutral += 1
                else:
                    quality_vals.append(qual)
    print("No solution: ", no_solution)
    print("Not energy neutral: ", not_energy_neutral)
    print("Battery underflow: ", battery_underflow)
    if len(quality_vals) > 0:
        print("Avg quality: ", statistics.fmean(quality_vals))


eval_iterations()