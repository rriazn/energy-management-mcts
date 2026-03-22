import mcts_multiple_expansion as mcts
import beam_search_iot as bs
import iot_algo
from energy_harvesting_prediction import get_energy_predictions_clearsky, get_energy_for_day
import random
import statistics
import timeit
import plotly.express as px
from pyvis.network import Network
from collections import deque
import up_down as ud
from datetime import datetime


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
    for i in range(1, 24, 1):
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
    print(y_axis)
    fig.show()


def eval_beam_width():
    x_axis = [i for i in range(1, 7)]
    y_axis = []
    for i in range(1, 7):
        bs.beam_width = i
        sol, _ = bs.beam_search(bs.Node(bs.B_start, 0, None, 0))
        if len(sol) != 0:
            ns = list(filter(lambda n: n.battery_level >= bs.B_start, sol))
            node = max(ns, key=lambda n: n.best_quality)
            y_axis.append(node.best_quality)
        else:
            y_axis.append(0)
    fig = px.line(
        x=x_axis,
        y=y_axis,
        markers=True,  # keeps the dots visible
        color_discrete_sequence=['#FF8C00']  # same color as before
    )
    print(y_axis)
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


import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta


def create_calendar_heatmaps_mcts():
    year = 2023
    days_in_year = (date(year + 1, 1, 1) - date(year, 1, 1)).days
    start = date(year, 1, 1)

    battery_calendar = np.full((7, 53), np.nan)
    qual_calendar = np.full((7, 53), np.nan)
    date_labels = np.empty((7, 53), dtype=object)
    next_battery = mcts.B_start
    dp_next_battery = iot_algo.Bstart
    higher_than_dp = 0
    lower_10 = 0
    lower_15 = 0
    lower_20 = 0
    lower_energy_than_dp = 0
    energy_higher_10 = 0
    energy_higher_25 = 0
    qual_sum = 0
    dp_qual_sum = 0
    for i in range(days_in_year - 1):
        current_day = start + timedelta(days=i)
        weekday = current_day.weekday()  # 0 = monday, 6 = sunday
        if current_day.day == 1 and current_day.month == 1:
            week = 0
        else:
            week = current_day.isocalendar()[1]

        if week >= 53:
            continue

        harvesting_predictions = list(map(lambda p: round(p), get_energy_for_day(datetime(
            current_day.year, current_day.month, current_day.day, 16, 10
        ))))

        #harvesting_predictions = get_energy_predictions_clearsky(24, current_day.strftime("%Y-%m-%d"))
        #harvesting_predictions = [round(p) for p in harvesting_predictions]
        #print(harvesting_predictions)
        mcts.E = harvesting_predictions
        iot_algo.E = harvesting_predictions
        while True:
            result = mcts.mcts(mcts.Node(next_battery, 0, None), 24)
            if result[3] != 0:
                break
        next_battery = result[3]


        try:
            dp_solution = iot_algo.solve(
                iot_algo.Tasks, iot_algo.K, iot_algo.Bmax, iot_algo.Bmin, iot_algo.Bstart, iot_algo.E
            )
        except IndexError:
            print(len(harvesting_predictions))
            exit(1)
        max_qual = dp_solution[1][0][dp_next_battery]
        dp_battery = iot_algo.reconstruct(dp_solution[0])[1]
        dp_next_battery = dp_battery
        print(max_qual)
        qual_diff = result[2] - max_qual
        battery_diff = result[3] - dp_battery
        qual_sum += result[2]
        dp_qual_sum += max_qual
        battery_calendar[weekday, week] = battery_diff
        qual_calendar[weekday, week] = qual_diff / max_qual
        date_labels[weekday, week] = current_day.strftime("%b %d")

        if battery_diff > 0:
            if battery_diff / dp_battery > 0.25:
                energy_higher_25 += 1
            elif battery_diff / dp_battery > 0.10:
                energy_higher_10 += 1
        else:
            lower_energy_than_dp += 1

        if qual_diff >= 0:
            higher_than_dp += 1
        else:
            if qual_diff / max_qual <= -0.2:
                lower_20 += 1
            elif qual_diff / max_qual <= -0.15:
                lower_15 += 1
            elif qual_diff / max_qual <= -0.10:
                lower_10 += 1

        #print(f"{current_day.strftime('%Y-%m-%d')}: Final={result[3]}, Diff={battery_diff:+.1f}")

    text = np.round(battery_calendar, 2).astype(str)
    battery_calendar = np.flipud(battery_calendar)
    text = text[::-1]
    weekday_labels = ["Sun", "Sat", "Fri", "Thu", "Wed", "Tue", "Mon"]
    week_labels = [str(i + 1) for i in range(53)]
    custom_colorscale = [
        [0.0, '#d73027'],  # Deep red (very negative)
        [0.3, '#fc8d59'],  # Orange-red (negative)
        [0.45, '#fee08b'],  # Light orange (slightly negative)
        [0.5, '#1a9850'],  # Green (zero/neutral - ideal)
        [0.55, '#91cf60'],  # Light green (slightly positive)
        [0.7, '#d9ef8b'],  # Yellow-green (positive)
        [0.85, '#ffffbf'],  # Light yellow (more positive)
        [1.0, '#ffff00']  # Bright yellow (very positive)
    ]

    fig = go.Figure(data=go.Heatmap(
        z=battery_calendar,
        x=week_labels,
        y=weekday_labels,
        text=text,
        texttemplate='%{text}',
        colorscale=custom_colorscale,
        zmid=0,
        colorbar=dict(
            title="Battery Δ<br>(vs DP)",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig.update_layout(
        title=f"MCTS Energy Neutrality Calendar - {year}",
        xaxis_title="Week of Year",
        yaxis_title="Day of Week",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig.show()

    text = np.round(qual_calendar, 2).astype(str)
    qual_calendar = np.flipud(qual_calendar)
    text = text[::-1]
    weekday_labels = ["Sun", "Sat", "Fri", "Thu", "Wed", "Tue", "Mon"]
    week_labels = [str(i + 1) for i in range(53)]
    custom_colorscale = [
        [0.00, '#FFFFCC'],  # very light yellow
        [0.05, '#FFF799'],  # pale yellow
        [0.10, '#FFE066'],  # warm yellow
        [0.15, '#FFD633'],  # golden yellow
        [0.20, '#FFCC00'],  # strong yellow
        [0.25, '#E6E600'],  # yellow-green
        [0.30, '#B3E600'],  # lime-yellow
        [0.35, '#80FF00'],  # bright lime
        [0.40, '#4DFF00'],  # vivid greenish
        [0.45, '#1AFF00'],  # neon green
        [0.50, '#00FFFF'],  # cyan (new midpoint)
        [0.55, '#00E6FF'],
        [0.60, '#00CCFF'],
        [0.65, '#00B3FF'],
        [0.70, '#0099FF'],
        [0.75, '#007FFF'],
        [0.80, '#0066CC'],
        [0.85, '#004C99'],
        [0.90, '#003366'],
        [0.95, '#001F99'],
        [1.00, '#000066']  # deep navy blue
    ]
    fig = go.Figure(data=go.Heatmap(
        z=qual_calendar,
        x=week_labels,
        y=weekday_labels,
        text=text,
        texttemplate='%{text}',
        colorscale=custom_colorscale,
        zmid=0,
        zmin=-0.3,
        zmax=0.3,
        zauto=False,
        colorbar=dict(
            title="Quality value vs. max.",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig.update_layout(
        title=f"MCTS Quality Calendar - {year}",
        xaxis_title="Week of Year",
        yaxis_title="Day of Week",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig.show()
    print("higher ", higher_than_dp)
    print("lower than 10%:", lower_10)
    print("lower than 15%:", lower_15)
    print("lower than 20%:", lower_20)
    print("lower energy: ", lower_energy_than_dp)
    print("10% higher energy: ", energy_higher_10)
    print("25% higher energy: ", energy_higher_25)
    print("quality sum: ", qual_sum)
    print("DP quality sum: ", dp_qual_sum)
    return battery_calendar



energy_vectors = [
    [1, 0, 0, 0, 0, 0, 2, 5, 6, 4],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 4, 6, 6, 6, 4],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 5, 7, 7, 7, 6, 4],
    [3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 4, 6, 7, 8, 8, 7, 6, 5],
    [3, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 4, 6, 7, 8, 8, 8, 8, 7, 6, 4]
]

sunrise_set = [
    (9, 6),
    (14, 9),
    (19, 13),
    (0, 16),
    (0, 19)
]


def create_timeslot_battery_heatmap_quality(n):
    qual_values = np.empty((n, n))
    battery_values = np.empty((n,n))
    mcts.B_min = 10
    for i in range(n):
        mcts.E = energy_vectors[i]
        iot_algo.E = energy_vectors[i]
        mcts.K = 10 + 5 * i
        iot_algo.K = 10 + 5 * i
        for j in range(n):
            mcts.B_max = 30 + 10 * i
            iot_algo.B_max = 30 + 10 * i
            mcts.B_start = round((mcts.B_max + mcts.B_min) / 2)
            iot_algo.B_start = round((mcts.B_max + mcts.B_min) / 2)
            quals = []
            batts = []
            while len(quals) < 11:
                result = mcts.mcts(mcts.Node(mcts.B_start, 0), iterations=round(mcts.K))
                if result[2] != 0:
                    quals.append(result[2])
                    batts.append(result[3])
            quality = statistics.fmean(quals)
            battery = statistics.fmean(batts)
            max_qual = iot_algo.solve(
                        iot_algo.Tasks, iot_algo.K, iot_algo.Bmax, iot_algo.Bmin, iot_algo.Bstart, iot_algo.E
                        )[1][0][iot_algo.Bstart]
            print(quals, max_qual)
            qual_diff = quality - max_qual
            qual_values[i, j] = qual_diff / max_qual

            battery_diff = battery - mcts.B_start
            battery_values[i, j] = battery_diff / mcts.B_start
    text_qual = np.round(qual_values, 2).astype(str)
    text_battery = np.round(battery_values, 2).astype(str)
    custom_qual_colorscale = [
        [0.00, '#000000'],  # Black
        [0.05, '#0d0000'],  # Almost black
        [0.10, '#1a0000'],  # Almost black
        [0.15, '#330000'],  # Almost black red
        [0.20, '#550000'],  # Very dark red
        [0.25, '#770000'],  # Very dark red
        [0.30, '#990000'],  # Darker red
        [0.35, '#cc0000'],  # Dark red
        [0.40, '#dd0000'],  # Dark red
        [0.45, '#ee0000'],  # Slightly darker red
        [0.50, '#ff0000'],  # Pure red
        [0.55, '#ff3300'],  # Red-orange
        [0.60, '#ff6600'],  # Orange-red
        [0.65, '#ff9900'],  # Orange
        [0.70, '#ffcc00'],  # Orange-yellow
        [0.75, '#ffff00'],  # Pure yellow
        [0.80, '#eeff00'],  # Yellow
        [0.85, '#ccff00'],  # Yellow
        [0.90, '#66ff00'],  # Yellow-green
        [0.95, '#33ff00'],  # Yellow-green
        [1.00, '#00ff00']  # Bright green
    ]
    custom_battery_colorscale = [
        [0.0, '#d73027'],  # Deep red (very negative)
        [0.3, '#fc8d59'],  # Orange-red (negative)
        [0.45, '#fee08b'],  # Light orange (slightly negative)
        [0.5, '#1a9850'],  # Green (zero/neutral - ideal)
        [0.55, '#91cf60'],  # Light green (slightly positive)
        [0.7, '#d9ef8b'],  # Yellow-green (positive)
        [0.85, '#ffffbf'],  # Light yellow (more positive)
        [1.0, '#ffff00']  # Bright yellow (very positive)
    ]

    timeslot_labels = [str(10 + i * 5) for i in range(n)]
    battery_labels = [str(300 + 100 * i) for i in range(n)]

    fig_qual = go.Figure(data=go.Heatmap(
        z=qual_values,
        x=timeslot_labels,
        y=battery_labels,
        text=text_qual,
        texttemplate='%{text}',
        colorscale=custom_qual_colorscale,
        zmin=-1,
        zmax=0,
        zauto=False,
        colorbar=dict(
            title="Quality value vs. max.",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig_qual.update_layout(
        title=f"MCTS Quality evaluation",
        xaxis_title="timeslots",
        yaxis_title="maximum Battery in mAh",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig_battery = go.Figure(data=go.Heatmap(
        z=battery_values,
        x=timeslot_labels,
        y=battery_labels,
        text=text_battery,
        texttemplate='%{text}',
        colorscale=custom_battery_colorscale,
        zmid=0,
        colorbar=dict(
            title="Battery Δ<br>(vs DP)",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig_battery.update_layout(
        title=f"MCTS Energy Neutrality Evaluation",
        xaxis_title="timeslots",
        yaxis_title="maximum Battery in mAh",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig_qual.show()
    fig_battery.show()


def create_calendar_heatmaps_bs():
    year = 2023
    days_in_year = (date(year + 1, 1, 1) - date(year, 1, 1)).days
    start = date(year, 1, 1)

    battery_calendar = np.full((7, 53), np.nan)
    qual_calendar = np.full((7, 53), np.nan)
    date_labels = np.empty((7, 53), dtype=object)
    iot_algo.Tasks = bs.Tasks
    next_battery = bs.B_start
    dp_next_battery = iot_algo.Bstart

    higher_than_dp = 0
    lower_10 = 0
    lower_15 = 0
    lower_20 = 0
    lower_energy_than_dp = 0
    energy_higher_10 = 0
    energy_higher_25 = 0
    qual_sum = 0
    for i in range(days_in_year - 1):
        current_day = start + timedelta(days=i)
        weekday = current_day.weekday()

        if current_day.day == 1 and current_day.month == 1:
            week = 0
        else:
            week = current_day.isocalendar()[1]

        if week >= 53:
            continue

        #harvesting_predictions = get_energy_predictions_clearsky(24, current_day.strftime("%Y-%m-%d"))
        #harvesting_predictions = [round(p) for p in harvesting_predictions]
        harvesting_predictions = list(map(lambda p: round(p), get_energy_for_day(datetime(
            current_day.year, current_day.month, current_day.day, 16, 10
        ))))

        bs.E = harvesting_predictions
        bs.beam_width = 3
        while True:
            try:
                result, rt = bs.beam_search(bs.Node(next_battery, 0, None, 0))
                best_leaf_node = max(list(filter(lambda n: n.battery_level >= bs.B_start, result)),
                                     key=lambda n: n.best_quality)
                break
            except ValueError:
                bs.beam_width += 1

        next_battery = best_leaf_node.battery_level
        iot_algo.E = harvesting_predictions
        dp_res = iot_algo.solve(
            iot_algo.Tasks, iot_algo.K, iot_algo.Bmax, iot_algo.Bmin, iot_algo.Bstart, iot_algo.E
        )
        max_qual = dp_res[1][0][dp_next_battery]

        dp_next_battery = iot_algo.reconstruct(dp_res[0])[1]
        qual_sum += best_leaf_node.best_quality
        qual_diff = best_leaf_node.best_quality - max_qual
        battery_diff = best_leaf_node.battery_level - dp_next_battery
        battery_calendar[weekday, week] = battery_diff
        qual_calendar[weekday, week] = qual_diff / max_qual
        date_labels[weekday, week] = current_day.strftime("%b %d")
        if battery_diff > 0:
            if battery_diff / dp_next_battery > 0.25:
                energy_higher_25 += 1
            elif battery_diff / dp_next_battery > 0.10:
                energy_higher_10 += 1
        else:
            lower_energy_than_dp += 1

        if qual_diff >= 0:
            higher_than_dp += 1
        else:
            if qual_diff / max_qual <= -0.2:
                lower_20 += 1
            elif qual_diff / max_qual <= -0.15:
                lower_15 += 1
            elif qual_diff / max_qual <= -0.10:
                lower_10 += 1
        print(f"{current_day.strftime('%Y-%m-%d')}: Final={best_leaf_node.best_quality}, Diff={qual_diff:+.1f}")


    text = np.round(qual_calendar, 2).astype(str)
    qual_calendar = np.flipud(qual_calendar)
    text = text[::-1]
    weekday_labels = ["Sun", "Sat", "Fri", "Thu", "Wed", "Tue", "Mon"]
    week_labels = [str(i + 1) for i in range(53)]
    custom_qual_colorscale = [
        [0.00, '#FFFFCC'],  # very light yellow
        [0.05, '#FFF799'],  # pale yellow
        [0.10, '#FFE066'],  # warm yellow
        [0.15, '#FFD633'],  # golden yellow
        [0.20, '#FFCC00'],  # strong yellow
        [0.25, '#E6E600'],  # yellow-green
        [0.30, '#B3E600'],  # lime-yellow
        [0.35, '#80FF00'],  # bright lime
        [0.40, '#4DFF00'],  # vivid greenish
        [0.45, '#1AFF00'],  # neon green
        [0.50, '#00FFFF'],  # cyan (new midpoint)
        [0.55, '#00E6FF'],
        [0.60, '#00CCFF'],
        [0.65, '#00B3FF'],
        [0.70, '#0099FF'],
        [0.75, '#007FFF'],
        [0.80, '#0066CC'],
        [0.85, '#004C99'],
        [0.90, '#003366'],
        [0.95, '#001F99'],
        [1.00, '#000066']  # deep navy blue
    ]
    fig = go.Figure(data=go.Heatmap(
        z=qual_calendar,
        x=week_labels,
        y=weekday_labels,
        text=text,
        texttemplate='%{text}',
        colorscale=custom_qual_colorscale,
        zmin=-0.3,
        zmax=0.3,
        zmid=0,
        zauto=False,
        colorbar=dict(
            title="Quality value vs. max.",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig.update_layout(
        title=f"Beam Search Quality Calendar - {year}",
        xaxis_title="Week of Year",
        yaxis_title="Day of Week",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig.show()

    text = np.round(battery_calendar, 2).astype(str)
    battery_calendar = np.flipud(battery_calendar)
    text = text[::-1]
    weekday_labels = ["Sun", "Sat", "Fri", "Thu", "Wed", "Tue", "Mon"]
    week_labels = [str(i + 1) for i in range(53)]
    custom_colorscale = [
        [0.0, '#d73027'],  # Deep red (very negative)
        [0.3, '#fc8d59'],  # Orange-red (negative)
        [0.45, '#fee08b'],  # Light orange (slightly negative)
        [0.5, '#1a9850'],  # Green (zero/neutral - ideal)
        [0.55, '#91cf60'],  # Light green (slightly positive)
        [0.7, '#d9ef8b'],  # Yellow-green (positive)
        [0.85, '#ffffbf'],  # Light yellow (more positive)
        [1.0, '#ffff00']  # Bright yellow (very positive)
    ]

    fig = go.Figure(data=go.Heatmap(
        z=battery_calendar,
        x=week_labels,
        y=weekday_labels,
        text=text,
        texttemplate='%{text}',
        colorscale=custom_colorscale,
        zmid=0,
        zmin=-200,
        zmax=200,
        colorbar=dict(
            title="Battery Δ<br>(vs DP)",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig.update_layout(
        title=f"Beam Search Energy Neutrality Calendar - {year}",
        xaxis_title="Week of Year",
        yaxis_title="Day of Week",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig.show()
    print("higher ", higher_than_dp)
    print("lower than 10%:", lower_10)
    print("lower than 15%:", lower_15)
    print("lower than 20%:", lower_20)
    print("lower energy: ", lower_energy_than_dp)
    print("10% higher energy: ", energy_higher_10)
    print("25% higher energy: ", energy_higher_25)
    print("quality sum: ", qual_sum)

    return qual_calendar


def create_battery_calendar_heatmap_bs():
    year = 2026
    days_in_year = (date(year + 1, 1, 1) - date(year, 1, 1)).days
    start = date(year, 1, 1)

    battery_calendar = np.full((7, 53), np.nan)
    date_labels = np.empty((7, 53), dtype=object)

    for i in range(days_in_year):
        current_day = start + timedelta(days=i)
        weekday = current_day.weekday()  # 0 = monday, 6 = sunday

        week = current_day.isocalendar()[1] - 1

        if week >= 53:
            continue

        harvesting_predictions = get_energy_predictions_clearsky(24, current_day.strftime("%Y-%m-%d"))
        harvesting_predictions = [round(p / 10) for p in harvesting_predictions]

        bs.E = harvesting_predictions
        result, rt = bs.beam_search(bs.Node(bs.B_start, 0, None, 0))
        best_leaf_node = max(result, key=lambda n: n.best_quality)
        battery_diff = best_leaf_node.battery_level - bs.B_start

        battery_calendar[weekday, week] = battery_diff / bs.B_start
        date_labels[weekday, week] = current_day.strftime("%b %d")


        print(f"{current_day.strftime('%Y-%m-%d')}: Final={result[3]}, Diff={battery_diff:+.1f}")

    text = np.round(battery_calendar, 2).astype(str)
    battery_calendar = np.flipud(battery_calendar)
    text = text[::-1]
    weekday_labels = ["Sun", "Sat", "Fri", "Thu", "Wed", "Tue", "Mon"]
    week_labels = [str(i + 1) for i in range(53)]
    custom_colorscale = [
        [0.0, '#d73027'],  # Deep red (very negative)
        [0.3, '#fc8d59'],  # Orange-red (negative)
        [0.45, '#fee08b'],  # Light orange (slightly negative)
        [0.5, '#1a9850'],  # Green (zero/neutral - ideal)
        [0.55, '#91cf60'],  # Light green (slightly positive)
        [0.7, '#d9ef8b'],  # Yellow-green (positive)
        [0.85, '#ffffbf'],  # Light yellow (more positive)
        [1.0, '#ffff00']  # Bright yellow (very positive)
    ]

    fig = go.Figure(data=go.Heatmap(
        z=battery_calendar,
        x=week_labels,
        y=weekday_labels,
        text=text,
        texttemplate='%{text}',
        colorscale=custom_colorscale,
        zmid=0,
        colorbar=dict(
            title="Battery Δ<br>(vs DP)",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig.update_layout(
        title=f"Beam Search Energy Neutrality Calendar - {year}",
        xaxis_title="Week of Year",
        yaxis_title="Day of Week",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig.show()



    return battery_calendar


def create_timeslot_battery_heatmap_quality_ud(n):
    qual_values = np.empty((n, n))
    battery_values = np.empty((n,n))
    iot_algo.Tasks = bs.Tasks
    ud.B_min = 10
    for i in range(n):
        ud.E = energy_vectors[i]
        iot_algo.E = energy_vectors[i]
        ud.K = 10 + 5 * i
        iot_algo.K = 10 + 5 * i
        sunrs = sunrise_set[i]
        ud.sunrise = sunrs[1]
        ud.sunset = sunrs[0]
        for j in range(1):
            ud.B_max = 30 + 10 * i
            iot_algo.B_max = 30 + 10 * i
            ud.B_start = round((ud.B_max + ud.B_min) / 2)
            iot_algo.B_start = round((bs.B_max + bs.B_min) / 2)
            qual, bat = ud.get_sol_qual_bat(ud.initial_assignment())
            print(bat)
            battery_diff = bat - ud.B_start
            max_qual = iot_algo.solve(
                iot_algo.Tasks, iot_algo.K, iot_algo.Bmax, iot_algo.Bmin, iot_algo.Bstart, iot_algo.E
            )[1][0][iot_algo.Bstart]

            qual_diff = qual - max_qual
            qual_values[i, j] = qual_diff / max_qual

            battery_values[i, j] = battery_diff / bs.B_start
    text_qual = np.round(qual_values, 2).astype(str)
    text_battery = np.round(battery_values, 2).astype(str)
    custom_qual_colorscale = [
        [0.00, '#000000'],  # Black
        [0.05, '#0d0000'],  # Almost black
        [0.10, '#1a0000'],  # Almost black
        [0.15, '#330000'],  # Almost black red
        [0.20, '#550000'],  # Very dark red
        [0.25, '#770000'],  # Very dark red
        [0.30, '#990000'],  # Darker red
        [0.35, '#cc0000'],  # Dark red
        [0.40, '#dd0000'],  # Dark red
        [0.45, '#ee0000'],  # Slightly darker red
        [0.50, '#ff0000'],  # Pure red
        [0.55, '#ff3300'],  # Red-orange
        [0.60, '#ff6600'],  # Orange-red
        [0.65, '#ff9900'],  # Orange
        [0.70, '#ffcc00'],  # Orange-yellow
        [0.75, '#ffff00'],  # Pure yellow
        [0.80, '#eeff00'],  # Yellow
        [0.85, '#ccff00'],  # Yellow
        [0.90, '#66ff00'],  # Yellow-green
        [0.95, '#33ff00'],  # Yellow-green
        [1.00, '#00ff00']  # Bright green
    ]
    custom_battery_colorscale = [
        [0.0, '#d73027'],  # Deep red (very negative)
        [0.3, '#fc8d59'],  # Orange-red (negative)
        [0.45, '#fee08b'],  # Light orange (slightly negative)
        [0.5, '#1a9850'],  # Green (zero/neutral - ideal)
        [0.55, '#91cf60'],  # Light green (slightly positive)
        [0.7, '#d9ef8b'],  # Yellow-green (positive)
        [0.85, '#ffffbf'],  # Light yellow (more positive)
        [1.0, '#ffff00']  # Bright yellow (very positive)
    ]

    timeslot_labels = [str(10 + i * 5) for i in range(n)]
    battery_labels = [str(300 + 100 * i) for i in range(n)]

    fig_qual = go.Figure(data=go.Heatmap(
        z=qual_values,
        x=timeslot_labels,
        y=battery_labels,
        text=text_qual,
        texttemplate='%{text}',
        colorscale=custom_qual_colorscale,
        zmin=-1,
        zmax=0,
        zauto=False,
        colorbar=dict(
            title="Quality value vs. max.",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig_qual.update_layout(
        title=f"Beam Search Quality evaluation",
        xaxis_title="timeslots",
        yaxis_title="maximum Battery in mAh",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig_battery = go.Figure(data=go.Heatmap(
        z=battery_values,
        x=timeslot_labels,
        y=battery_labels,
        text=text_battery,
        texttemplate='%{text}',
        colorscale=custom_battery_colorscale,
        zmid=0,
        colorbar=dict(
            title="Battery Δ<br>(vs DP)",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig_battery.update_layout(
        title=f"Beam Search Energy Neutrality Evaluation",
        xaxis_title="timeslots",
        yaxis_title="maximum Battery in mAh",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig_qual.show()
    fig_battery.show()


def create_timeslot_battery_heatmap_quality_bs(n):
    qual_values = np.empty((n, n))
    battery_values = np.empty((n,n))
    iot_algo.Tasks = bs.Tasks
    bs.B_min = 10
    for i in range(n):
        bs.E = energy_vectors[i]
        iot_algo.E = energy_vectors[i]
        bs.K = 10 + 5 * i
        iot_algo.K = 10 + 5 * i
        for j in range(n):
            bs.B_max = 30 + 10 * i
            iot_algo.B_max = 30 + 10 * i
            bs.B_start = round((bs.B_max + bs.B_min) / 2)
            iot_algo.B_start = round((bs.B_max + bs.B_min) / 2)

            result, rt = bs.beam_search(bs.Node(bs.B_start, 0, None, 0))
            best_leaf_node = max(filter(lambda n: n.battery_level >= bs.B_start, result), key=lambda m: m.best_quality)
            battery_diff = best_leaf_node.battery_level - bs.B_start
            max_qual = iot_algo.solve(
                iot_algo.Tasks, iot_algo.K, iot_algo.Bmax, iot_algo.Bmin, iot_algo.Bstart, iot_algo.E
            )[1][0][iot_algo.Bstart]

            qual_diff = best_leaf_node.best_quality - max_qual
            qual_values[i, j] = qual_diff / max_qual

            battery_values[i, j] = battery_diff / bs.B_start
    text_qual = np.round(qual_values, 2).astype(str)
    text_battery = np.round(battery_values, 2).astype(str)
    custom_qual_colorscale = [
        [0.00, '#000000'],  # Black
        [0.05, '#0d0000'],  # Almost black
        [0.10, '#1a0000'],  # Almost black
        [0.15, '#330000'],  # Almost black red
        [0.20, '#550000'],  # Very dark red
        [0.25, '#770000'],  # Very dark red
        [0.30, '#990000'],  # Darker red
        [0.35, '#cc0000'],  # Dark red
        [0.40, '#dd0000'],  # Dark red
        [0.45, '#ee0000'],  # Slightly darker red
        [0.50, '#ff0000'],  # Pure red
        [0.55, '#ff3300'],  # Red-orange
        [0.60, '#ff6600'],  # Orange-red
        [0.65, '#ff9900'],  # Orange
        [0.70, '#ffcc00'],  # Orange-yellow
        [0.75, '#ffff00'],  # Pure yellow
        [0.80, '#eeff00'],  # Yellow
        [0.85, '#ccff00'],  # Yellow
        [0.90, '#66ff00'],  # Yellow-green
        [0.95, '#33ff00'],  # Yellow-green
        [1.00, '#00ff00']  # Bright green
    ]
    custom_battery_colorscale = [
        [0.0, '#d73027'],  # Deep red (very negative)
        [0.3, '#fc8d59'],  # Orange-red (negative)
        [0.45, '#fee08b'],  # Light orange (slightly negative)
        [0.5, '#1a9850'],  # Green (zero/neutral - ideal)
        [0.55, '#91cf60'],  # Light green (slightly positive)
        [0.7, '#d9ef8b'],  # Yellow-green (positive)
        [0.85, '#ffffbf'],  # Light yellow (more positive)
        [1.0, '#ffff00']  # Bright yellow (very positive)
    ]

    timeslot_labels = [str(10 + i * 5) for i in range(n)]
    battery_labels = [str(300 + 100 * i) for i in range(n)]

    fig_qual = go.Figure(data=go.Heatmap(
        z=qual_values,
        x=timeslot_labels,
        y=battery_labels,
        text=text_qual,
        texttemplate='%{text}',
        colorscale=custom_qual_colorscale,
        zmin=-1,
        zmax=0,
        zauto=False,
        colorbar=dict(
            title="Quality value vs. max.",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig_qual.update_layout(
        title=f"Beam Search Quality evaluation",
        xaxis_title="timeslots",
        yaxis_title="maximum Battery in mAh",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig_battery = go.Figure(data=go.Heatmap(
        z=battery_values,
        x=timeslot_labels,
        y=battery_labels,
        text=text_battery,
        texttemplate='%{text}',
        colorscale=custom_battery_colorscale,
        zmid=0,
        colorbar=dict(
            title="Battery Δ<br>(vs DP)",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig_battery.update_layout(
        title=f"Beam Search Energy Neutrality Evaluation",
        xaxis_title="timeslots",
        yaxis_title="maximum Battery in mAh",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig_qual.show()
    fig_battery.show()
    
    
def create_calendar_heatmaps_ud():
    year = 2023
    days_in_year = (date(year + 1, 1, 1) - date(year, 1, 1)).days
    start = date(year, 1, 1)

    battery_calendar = np.full((7, 53), np.nan)
    qual_calendar = np.full((7, 53), np.nan)
    date_labels = np.empty((7, 53), dtype=object)
    iot_algo.Tasks = ud.P
    next_battery = ud.B_start
    dp_next_battery = iot_algo.Bstart

    higher_than_dp = 0
    lower_10 = 0
    lower_15 = 0
    lower_20 = 0
    lower_energy_than_dp = 0
    energy_higher_10 = 0
    energy_higher_25 = 0
    qual_sum = 0
    for i in range(days_in_year - 1):
        ud.starting_battery = next_battery
        current_day = start + timedelta(days=i)
        weekday = current_day.weekday()

        if current_day.day == 1 and current_day.month == 1:
            week = 0
        else:
            week = current_day.isocalendar()[1]

        if week >= 53:
            continue

        #harvesting_predictions = get_energy_predictions_clearsky(24, current_day.strftime("%Y-%m-%d"))
        #harvesting_predictions = [round(p) for p in harvesting_predictions]
        harvesting_predictions = list(map(lambda p: round(p), get_energy_for_day(datetime(
            current_day.year, current_day.month, current_day.day, 16, 10
        ))))

        ud.E = harvesting_predictions
        ud.sunrise = next((i for i in range(24) if harvesting_predictions[i] == 0))
        ud.sunset = max((i for i in range(24) if harvesting_predictions[i] == 0))
        
        assignment = ud.initial_assignment()
        quality, next_battery = ud.get_sol_qual_bat(assignment)
        qual_sum += quality
        iot_algo.E = harvesting_predictions
        dp_res = iot_algo.solve(
            iot_algo.Tasks, iot_algo.K, iot_algo.Bmax, iot_algo.Bmin, iot_algo.Bstart, iot_algo.E
        )
        max_qual = dp_res[1][0][dp_next_battery]

        dp_next_battery = iot_algo.reconstruct(dp_res[0])[1]
        qual_diff = quality - max_qual
        battery_diff = next_battery - dp_next_battery
        battery_calendar[weekday, week] = battery_diff
        qual_calendar[weekday, week] = qual_diff / max_qual
        date_labels[weekday, week] = current_day.strftime("%b %d")

        if battery_diff > 0:
            if battery_diff / dp_next_battery > 0.25:
                energy_higher_25 += 1
            elif battery_diff / dp_next_battery > 0.10:
                energy_higher_10 += 1
        else:
            lower_energy_than_dp += 1

        if qual_diff >= 0:
            higher_than_dp += 1
        else:
            if qual_diff / max_qual <= -0.2:
                lower_20 += 1
            elif qual_diff / max_qual <= -0.15:
                lower_15 += 1
            elif qual_diff / max_qual <= -0.10:
                lower_10 += 1

        print(f"{current_day.strftime('%Y-%m-%d')}: Final={quality}, Diff={qual_diff:+.1f}")


    text = np.round(qual_calendar, 2).astype(str)
    qual_calendar = np.flipud(qual_calendar)
    text = text[::-1]
    weekday_labels = ["Sun", "Sat", "Fri", "Thu", "Wed", "Tue", "Mon"]
    week_labels = [str(i + 1) for i in range(53)]
    custom_qual_colorscale = [
        [0.00, '#FFFFCC'],  # very light yellow
        [0.05, '#FFF799'],  # pale yellow
        [0.10, '#FFE066'],  # warm yellow
        [0.15, '#FFD633'],  # golden yellow
        [0.20, '#FFCC00'],  # strong yellow
        [0.25, '#E6E600'],  # yellow-green
        [0.30, '#B3E600'],  # lime-yellow
        [0.35, '#80FF00'],  # bright lime
        [0.40, '#4DFF00'],  # vivid greenish
        [0.45, '#1AFF00'],  # neon green
        [0.50, '#00FFFF'],  # cyan (new midpoint)
        [0.55, '#00E6FF'],
        [0.60, '#00CCFF'],
        [0.65, '#00B3FF'],
        [0.70, '#0099FF'],
        [0.75, '#007FFF'],
        [0.80, '#0066CC'],
        [0.85, '#004C99'],
        [0.90, '#003366'],
        [0.95, '#001F99'],
        [1.00, '#000066']  # deep navy blue
    ]
    fig = go.Figure(data=go.Heatmap(
        z=qual_calendar,
        x=week_labels,
        y=weekday_labels,
        text=text,
        texttemplate='%{text}',
        colorscale=custom_qual_colorscale,
        zmin=-0.3,
        zmax=0.3,
        zmid=0,
        zauto=False,
        colorbar=dict(
            title="Quality value vs. max.",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig.update_layout(
        title=f"UD Quality Calendar - {year}",
        xaxis_title="Week of Year",
        yaxis_title="Day of Week",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig.show()

    text = np.round(battery_calendar, 2).astype(str)
    battery_calendar = np.flipud(battery_calendar)
    text = text[::-1]
    weekday_labels = ["Sun", "Sat", "Fri", "Thu", "Wed", "Tue", "Mon"]
    week_labels = [str(i + 1) for i in range(53)]
    custom_colorscale = [
        [0.0, '#d73027'],  # Deep red (very negative)
        [0.3, '#fc8d59'],  # Orange-red (negative)
        [0.45, '#fee08b'],  # Light orange (slightly negative)
        [0.5, '#1a9850'],  # Green (zero/neutral - ideal)
        [0.55, '#91cf60'],  # Light green (slightly positive)
        [0.7, '#d9ef8b'],  # Yellow-green (positive)
        [0.85, '#ffffbf'],  # Light yellow (more positive)
        [1.0, '#ffff00']  # Bright yellow (very positive)
    ]

    fig = go.Figure(data=go.Heatmap(
        z=battery_calendar,
        x=week_labels,
        y=weekday_labels,
        text=text,
        texttemplate='%{text}',
        colorscale=custom_colorscale,
        zmid=0,
        zmin=-200,
        zmax=200,
        colorbar=dict(
            title="Battery Δ<br>(vs DP)",
            ticksuffix=" ",
        ),
        xgap=1,
        ygap=1
    ))

    fig.update_layout(
        title=f"UD Energy Neutrality Calendar - {year}",
        xaxis_title="Week of Year",
        yaxis_title="Day of Week",
        height=400,
        width=1400,
        xaxis=dict(side='top'),
    )

    fig.show()
    print("higher ", higher_than_dp)
    print("lower than 10%:", lower_10)
    print("lower than 15%:", lower_15)
    print("lower than 20%:", lower_20)
    print("lower energy: ", lower_energy_than_dp)
    print("10% higher energy: ", energy_higher_10)
    print("25% higher energy: ", energy_higher_25)
    print("quality sum: ", qual_sum)

    return qual_calendar


def eval_k_values_mcts():
    k = 0
    values = [0 for i in range(13)]
    while max(values) == 0 or max(values) != values[4]:
        for i in range(13):
            mcts.k_val = k
            vals = []
            for j in range(10):
                res = mcts.mcts(mcts.Node(mcts.B_start, 0), 20)
                vals.append(res[2])
            values[i] = statistics.fmean(vals)
            k = k + 0.25
    print(values)

def eval_k_values_bs():
    k = 0
    values = [0 for i in range(21)]

    for i in range(21):
        bs.k_val = k
        res = bs.beam_search(bs.Node(bs.B_start, 0, None, 0))
        try:
            maximum = max(res[0], key=lambda n: n.best_quality).best_quality
        except ValueError:
            maximum = 0
        values[i] = maximum
        print(k, values[i])
        k = k + 1

    print(values)

eval_k_values_mcts()
