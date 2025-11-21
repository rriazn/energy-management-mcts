#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>

#define K 24
#define B_START 20
#define B_MAX 30
#define B_MIN 10
#define C 1.41

#define ITERATIONS 500

static const int E [] = {3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4};

typedef struct task {
    int id;
    int cost;
    int quality;
} task_t;

static const task_t tasks[] = {
    {.id = 1, .cost = 3, .quality = 5},
    {.id = 2, .cost = 2, .quality = 3},
    {.id = 3, .cost = 4, .quality = 6},
    {.id = 4, .cost = 8, .quality = 10},
    {.id = 5, .cost = 1, .quality = 1}
};

#define NUM_TASKS sizeof(tasks) / sizeof(task_t)

static int visits[K][B_MAX - B_MIN + 1] = { 0 };
static int qualities[K][B_MAX - B_MIN + 1] = { 0 };
static bool possible_tasks[K + 1][B_MAX - B_MIN + 1][NUM_TASKS] = { 0 };

static bool adj[K + 1][B_MAX - B_MIN + 1][NUM_TASKS][2] = { 0 };     //last value: 0: outgoing edge (child); 1: incoming edge (parent)

static int penalize_quality(int sim_quality, int sim_battery) {
    return sim_quality - 2 * (B_START - sim_battery);
}

static void get_possible_tasks(int timeslot, int battery_lvl, bool possible_tasks[NUM_TASKS]) {
    if(K != timeslot) {
        for(int i = 0; i < NUM_TASKS; i++) {
            if(battery_lvl + E[timeslot] - tasks[i].cost >= B_MIN) {
                possible_tasks[i] = true;
            }
        }
    }
}

static void create_node(int timeslot, int battery_lvl, int parent_task_idx) {
    if(parent_task_idx != -1) {
        adj[timeslot][battery_lvl - B_MIN][parent_task_idx][1] = true;
    }
    get_possible_tasks(timeslot, battery_lvl, possible_tasks[timeslot][battery_lvl - B_MIN]);
}

static bool is_fully_expanded(int timeslot, int battery_lvl) {
    for(int i = 0; i < NUM_TASKS; i++) {
        if(possible_tasks[timeslot][battery_lvl - B_MIN][i]) {
            return false;
        }
    }
    return true;
}

static bool is_terminal(int timeslot, int battery_lvl) {
    if(K == timeslot) {
        return true;
    }
    for(int i = 0; i < NUM_TASKS; i++) {
        if(battery_lvl + E[timeslot] - tasks[i].cost >= B_MIN) {
            return false;
        }
    }
    return true;
}

static int expand(int timeslot, int battery_lvl) {
    int new_battery;
    int ret = -1;

    for(int i = 0; i < NUM_TASKS; i++) {
        if(possible_tasks[timeslot][battery_lvl - B_MIN][i]) {
            possible_tasks[timeslot][battery_lvl - B_MIN][i] = false;
            adj[timeslot][battery_lvl - B_MIN][i][0] = true;
            new_battery = battery_lvl + E[timeslot] - tasks[i].cost;
            if(new_battery > B_MAX) {
                new_battery = B_MAX;
            }
            adj[timeslot + 1][new_battery - B_MIN][i][1] = true;
            // if node doesnt exist yet: go forward with it
            if(visits[timeslot + 1][new_battery - B_MIN] == 0) {
                ret = i;
                create_node(timeslot + 1, new_battery, i);
                break;
            }
        }
    }
    return ret;
}

static int get_best_move(int timeslot, int battery_lvl) {
    float max_val = -1;
    int max_task_idx = -1;
    int new_battery;
    for(int i = 0; i < NUM_TASKS; i++) {
        if(adj[timeslot][battery_lvl - B_MIN][i][0]) {
            new_battery = battery_lvl + E[timeslot] - tasks[i].cost;
            if(new_battery > B_MAX) {
                new_battery = B_MAX;
            }
            float val = ((float) qualities[timeslot + 1][new_battery - B_MIN] / visits[timeslot + 1][new_battery - B_MIN] + \
                            C * sqrt(log(visits[timeslot][battery_lvl - B_MIN]) / visits[timeslot + 1][new_battery - B_MIN]));
            if(val > max_val) {
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
    while(true) {
        if(K == sim_timeslot) {
            if(*sim_battery < B_MIN) {
                sim_quality = penalize_quality(sim_quality, *sim_battery);
            }
            return sim_quality;
        }
        // get random task
        int available_tasks[NUM_TASKS] = { 0 };
        int count = 0;
        for(int i = 0; i < NUM_TASKS; i++) {
            if(*sim_battery + E[sim_timeslot] - tasks[i].cost >= B_MIN) {
                available_tasks[count] = i;
                count++;
            }
        }
        if(0 == count) {
            memset(res, 0, K * sizeof(int));
            return 0;
        }
        int random_idx = rand() % count;
        int chosen_task_idx = available_tasks[random_idx];
        // update simulation
        sim_quality += tasks[chosen_task_idx].quality;
        *sim_battery = *sim_battery + E[sim_timeslot] - tasks[chosen_task_idx].cost;
        if(*sim_battery > B_MAX) {
            *sim_battery = B_MAX;
        }
        res[sim_timeslot] = tasks[chosen_task_idx].id;
        sim_timeslot += 1;
    }
}

static void backpropagate(int result, int path[K + 1], int path_len) {
    for(int i = 0; i < path_len; i++) {
        visits[i][path[i] - B_MIN] += 1;
        qualities[i][path[i] - B_MIN] += result;
    }
}

static int mcts(int root_timeslot, int root_battery, int iterations, int best_path[K], int *best_solution_battery) {
    int best_quality = 0;
    for(int i = 0; i < iterations; i++) {
        int timeslot = root_timeslot;
        int battery_lvl = root_battery;

        int path[K + 1] = { 0 };
        path[0] = root_battery;
        int path_len = 1;

        int task_path[K + 1] = { 0 };
        int path_qual = 0;

        int result = -1;
        while(-1 == result) {
            // select
            while(!is_terminal(timeslot, battery_lvl) && is_fully_expanded(timeslot, battery_lvl)) {
                int best_move = get_best_move(timeslot, battery_lvl);
                battery_lvl = battery_lvl + E[timeslot] - tasks[best_move].cost;
                if(battery_lvl > B_MAX) {
                    battery_lvl = B_MAX;
                }
                timeslot++;
                path[path_len] = battery_lvl;
                task_path[path_len - 1] = tasks[best_move].id;
                path_len++;
                path_qual += tasks[best_move].quality;
            }

            // expand
            if(!is_terminal(timeslot, battery_lvl)) {
                result = expand(timeslot, battery_lvl);
            } else {
                break;
            }
        }
        if(-1 != result) {
            fflush(stdout);
            battery_lvl = battery_lvl + E[timeslot] - tasks[result].cost;
            if(battery_lvl > B_MAX) {
                battery_lvl = B_MAX;
            }
            fflush(stdout);
            timeslot++;
            path[path_len] = battery_lvl;
            task_path[path_len - 1] = tasks[result].id;
            path_len++;
            path_qual += tasks[result].quality;
        }
        int res[K] = { 0 };
        int sim_battery = 0;
        int sim_quality = simulate(timeslot, battery_lvl, path_qual, res, &sim_battery);
        if(sim_quality > best_quality && sim_battery >= B_START) {
            best_quality = sim_quality;
            *best_solution_battery = sim_battery;
            // concatenate paths to get full path
            for(int j = 0; j < K; j++) {
                if(task_path[j] != 0) {
                    best_path[j] = task_path[j];
                } else {
                    best_path[j] = res[j];
                }
            }
        }
        backpropagate(sim_quality, path, path_len);
    }
    return best_quality;
}

int main(int argc, char **argv) {
    srand(time(NULL));
    int best_path[K] = { 0 };
    create_node(0, B_START, -1);
    int best_solution_battery;
    int ret = mcts(0, 20, ITERATIONS, best_path, &best_solution_battery);
    int q = 0;
    printf("%d\n", ret);
    printf("%d\n", best_solution_battery);
    for(int i = 0; i < K; i++) {
        printf("%d\n", best_path[i]);
        q += tasks[best_path[i] - 1].quality;
    }
    
    
        
    return 0;
}