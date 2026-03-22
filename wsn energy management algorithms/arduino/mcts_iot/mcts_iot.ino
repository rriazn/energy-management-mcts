#include <Arduino.h>
#include <math.h>
#include <string.h>
#include "nrf.h"

#define K        55
#define B_START  65
#define B_MAX    120
#define B_MIN    10
#define C        1.41f

#define ITERATIONS (K / 2)
#define B_RANGE (B_MAX - B_MIN + 1)

static const int E[] = {4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 10, 10, 10, 9, 9, 8, 8, 7, 6, 5};

typedef struct task {
    int8_t id;
    int8_t cost;
    int8_t quality;
} task_t;

static task_t tasks[] = {
    {6, 1, 1},
    {2, 3, 5},
    {5, 2, 3},
    {1, 4, 6},
    {4, 8, 10},
    {3, 5, 7}
};

#define NUM_TASKS (sizeof(tasks) / sizeof(task_t))

// visits and qualities per (timeslot, battery)
static uint16_t visits[K + 1][B_RANGE]    = { 0 };
static int16_t  qualities[K + 1][B_RANGE] = { 0 };

// For each node (t, b), bitmask of tasks not yet expanded
static uint8_t possible_mask[K + 1][B_RANGE] = { 0 };
// For each node (t, b), bitmask of tasks that have been expanded (children exist)
static uint8_t child_mask[K + 1][B_RANGE]    = { 0 };

// Lookup table for exp(-x) from x=0..10
static const float EXP_TABLE[11] PROGMEM = {
    1.0000000f,   // exp(-0)
    0.3678794f,   // exp(-1)
    0.1353353f,   // exp(-2)
    0.0497871f,   // exp(-3)
    0.0183156f,   // exp(-4)
    0.0067379f,   // exp(-5)
    0.0024788f,   // exp(-6)
    0.0009119f,   // exp(-7)
    0.0003355f,   // exp(-8)
    0.0001234f,   // exp(-9)
    0.0000454f    // exp(-10)
};

static inline float fast_exp_neg(float x) {
    if (x >= 10.0f) return 0.0f;
    if (x <= 0.0f) return 1.0f;

    int idx = (int)x;
    float frac = x - (float)idx;

    float y0 = pgm_read_float(&EXP_TABLE[idx]);
    float y1 = pgm_read_float(&EXP_TABLE[idx + 1]);

    return y0 + (y1 - y0) * frac;
}

static int penalize_quality(int sim_quality, int sim_battery) {
    int k = 1;
    int diff = B_START - sim_battery;
    float scale = (float)diff / (float)B_MIN;
    float x = (float)k * scale;
    float expv = fast_exp_neg(x);
    float penalty_f = (float)sim_quality * (1.0f - expv);
    int penalty = (int)roundf(penalty_f);
    return sim_quality - penalty;
}

static void create_node(int timeslot, int battery_lvl, int parent_task_idx) {
    int bidx = battery_lvl - B_MIN;
    // parent_task_idx is not needed structurally anymore, but kept for compatibility
    (void)parent_task_idx;

    // Initialize possible_mask for this node: tasks that are feasible from here
    uint8_t mask = 0;
    if (timeslot != K) {
        for (int i = 0; i < NUM_TASKS; i++) {
            if (battery_lvl + E[timeslot] - tasks[i].cost >= B_MIN) {
                mask |= (1 << i);
            }
        }
    }
    possible_mask[timeslot][bidx] = mask;
    // child_mask starts empty
    child_mask[timeslot][bidx] = 0;
}

static bool is_fully_expanded(int timeslot, int battery_lvl) {
    int bidx = battery_lvl - B_MIN;
    return possible_mask[timeslot][bidx] == 0;
}

static bool is_terminal(int timeslot, int battery_lvl) {
    if (timeslot == K) {
        return true;
    }
    for (int i = 0; i < NUM_TASKS; i++) {
        if (battery_lvl + E[timeslot] - tasks[i].cost >= B_MIN) {
            return false;
        }
    }
    return true;
}

static bool expand(int timeslot, int battery_lvl, bool ret[NUM_TASKS]) {
    int bidx = battery_lvl - B_MIN;
    uint8_t mask = possible_mask[timeslot][bidx];
    bool new_child = false;

    for (int i = 0; i < NUM_TASKS; i++) {
        if (mask & (1 << i)) {
            // consume this possible task
            mask &= ~(1 << i);
            child_mask[timeslot][bidx] |= (1 << i);

            int new_battery = battery_lvl + E[timeslot] - tasks[i].cost;
            if (new_battery > B_MAX) {
                new_battery = B_MAX;
            }
            int nbidx = new_battery - B_MIN;

            if (visits[timeslot + 1][nbidx] == 0) {
                new_child = true;
                ret[i] = true;
                create_node(timeslot + 1, new_battery, i);
            }
        }
    }

    possible_mask[timeslot][bidx] = mask;
    return new_child;
}

static int get_best_move(int timeslot, int battery_lvl) {
    int bidx = battery_lvl - B_MIN;
    uint8_t c_mask = child_mask[timeslot][bidx];

    float max_val = -1.0f;
    int max_task_idx = -1;

    for (int i = NUM_TASKS - 1; i >= 0; i--) {
        if (c_mask & (1 << i)) {
            int new_battery = battery_lvl + E[timeslot] - tasks[i].cost;
            if (new_battery > B_MAX) {
                new_battery = B_MAX;
            }
            int nbidx = new_battery - B_MIN;

            uint16_t v = visits[timeslot + 1][nbidx];
            if (v == 0) continue;

            float val = (float)qualities[timeslot + 1][nbidx] / (float)v;
            if (val > max_val) {
                max_val = val;
                max_task_idx = i;
            }
        }
    }
    return max_task_idx;
}

static int simulate(int timeslot, int battery_lvl, int qual, int res[K], int *sim_battery) {
    int sim_timeslot = timeslot;
    int sim_quality = qual;
    *sim_battery = battery_lvl;

    while (true) {
        if (sim_timeslot == K) {
            if (*sim_battery < B_START) {
                sim_quality = penalize_quality(sim_quality, *sim_battery);
            }
            return sim_quality;
        }

        int available_tasks[NUM_TASKS] = { 0 };
        int count = 0;
        for (int i = 0; i < NUM_TASKS; i++) {
            if (*sim_battery + E[sim_timeslot] - tasks[i].cost >= B_MIN) {
                available_tasks[count++] = i;
            }
        }

        if (count == 0) {
            memset(res, 0, K * sizeof(int));
            return 0;
        }

        int random_idx = random(count);
        int chosen_task_idx = available_tasks[random_idx];

        sim_quality += tasks[chosen_task_idx].quality;
        *sim_battery = *sim_battery + E[sim_timeslot] - tasks[chosen_task_idx].cost;
        if (*sim_battery > B_MAX) {
            *sim_battery = B_MAX;
        }
        res[sim_timeslot] = chosen_task_idx;
        sim_timeslot += 1;
    }
}

static void backpropagate(int result, int path[K + 1], int path_len, int edges_count) {
    for (int i = 0; i < path_len; i++) {
        int bidx = path[i] - B_MIN;
        visits[i][bidx]   += edges_count;
        qualities[i][bidx] += result;
    }
}

static int mcts(int root_timeslot, int root_battery, int iterations, int8_t best_path[K], int *best_solution_battery) {
    int best_quality = 0;

    for (int it = 0; it < iterations; it++) {
        int timeslot = root_timeslot;
        int battery_lvl = root_battery;

        int path[K + 1] = { 0 };
        path[0] = root_battery;
        int path_len = 1;

        int task_path[K + 1];
        memset(task_path, -1, sizeof(task_path));
        int path_qual = 0;

        bool result[NUM_TASKS] = { false };
        bool new_child = false;

        while (!new_child) {
            while (!is_terminal(timeslot, battery_lvl) && is_fully_expanded(timeslot, battery_lvl)) {
                int best_move = get_best_move(timeslot, battery_lvl);
                if (best_move < 0) break;

                battery_lvl = battery_lvl + E[timeslot] - tasks[best_move].cost;
                if (battery_lvl > B_MAX) {
                    battery_lvl = B_MAX;
                }
                timeslot++;
                path[path_len] = battery_lvl;
                task_path[path_len - 1] = best_move;
                path_len++;
                path_qual += tasks[best_move].quality;
            }

            if (!is_terminal(timeslot, battery_lvl)) {
                memset(result, false, sizeof(result));
                new_child = expand(timeslot, battery_lvl, result);
            } else {
                break;
            }
        }

        if (new_child) {
            int summed_up_res = 0;
            int edge_count = 0;

            for (int j = 0; j < NUM_TASKS; j++) {
                if (result[j]) {
                    edge_count++;
                    int new_battery = battery_lvl + E[timeslot] - tasks[j].cost;
                    if (new_battery > B_MAX) {
                        new_battery = B_MAX;
                    }
                    int res[K];
                    memset(res, -1, sizeof(res));
                    int sim_battery = 0;
                    int sim_quality = simulate(timeslot + 1, new_battery,
                                               path_qual + tasks[j].quality,
                                               res, &sim_battery);
                    summed_up_res += sim_quality;

                    int nbidx = new_battery - B_MIN;
                    visits[timeslot + 1][nbidx]   += 1;
                    qualities[timeslot + 1][nbidx] += sim_quality;

                    if (sim_quality > best_quality && sim_battery >= B_START) {
                        best_quality = sim_quality;
                        *best_solution_battery = sim_battery;
                        for (int k = 0; k < K; k++) {
                            if (task_path[k] != -1) {
                                best_path[k] = task_path[k];
                            } else {
                                best_path[k] = res[k];
                            }
                        }
                        best_path[timeslot] = j;
                    }
                }
            }
            backpropagate(summed_up_res, path, path_len, edge_count);
        } else {
            int res[K];
            memset(res, -1, sizeof(res));
            int sim_battery = 0;
            int sim_quality = simulate(timeslot, battery_lvl, path_qual, res, &sim_battery);

            if (sim_quality > best_quality && sim_battery >= B_START) {
                best_quality = sim_quality;
                *best_solution_battery = sim_battery;
                for (int k = 0; k < K; k++) {
                    if (task_path[k] != -1) {
                        best_path[k] = task_path[k];
                    } else {
                        best_path[k] = res[k];
                    }
                }
            }
            backpropagate(sim_quality, path, path_len, 1);
        }
    }

    return best_quality;
}

int comp(const void *a, const void *b) {
    const task_t *ta = (const task_t *)a;
    const task_t *tb = (const task_t *)b;
    return tb->quality - ta->quality;
}

void setup() {
    Serial.begin(115200);
    randomSeed(analogRead(0));
    qsort(tasks, NUM_TASKS, sizeof(task_t), comp);

    while (!Serial) { }

    int8_t best_path[K];
    memset(visits, 0, sizeof(visits));
    memset(qualities, 0, sizeof(qualities));
    memset(possible_mask, 0, sizeof(possible_mask));
    memset(child_mask, 0, sizeof(child_mask));
    memset(best_path, -1, sizeof(best_path));

    create_node(0, B_START, -1);

    int best_solution_battery = B_START;
    unsigned long start = micros();
    int ret = mcts(0, B_START, ITERATIONS, best_path, &best_solution_battery);
    unsigned long end = micros();

    Serial.print("Quality: ");
    Serial.println(ret);

    int q = 0;
    Serial.println("Path (task indices):");
    for (int i = 0; i < K; i++) {
        Serial.println(best_path[i]);
        if (best_path[i] >= 0 && best_path[i] < NUM_TASKS) {
            q += tasks[best_path[i]].quality;
        }
    }

    Serial.print("Final Battery: ");
    Serial.print(best_solution_battery);
    Serial.print(" Verified Quality: ");
    Serial.println(q);
    Serial.print("Time: ");
    Serial.print(end - start);
    Serial.println(" us");

    int total_size =
        sizeof(best_path) +
        sizeof(visits) +
        sizeof(qualities) +
        sizeof(possible_mask) +
        sizeof(child_mask);

    Serial.println();
    Serial.print(total_size);
    Serial.println(" bytes");
}

void loop() {
}
