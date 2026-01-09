#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>
#include <limits.h>
#include <float.h>

#define MIN(X, Y) (((X) < (Y)) ? (X) : (Y))
#define MAX(X, Y) (((X) > (Y)) ? (X) : (Y))

#define K 24
#define B_START 30
#define B_MAX 50
#define B_MIN 10

static const int E [] = {3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4};

typedef struct task {
    int id;
    int cost;
    int quality;
} task_t;

typedef struct {
    int timeslot;
    int battery;
    int quality;        // g-value
    int f_value;        // f = g + h
} state_t;

static const task_t tasks[] = {
    {.id = 1, .cost = 4, .quality = 6},
    {.id = 2, .cost = 3, .quality = 5},
    {.id = 3, .cost = 5, .quality = 7},
    {.id = 4, .cost = 8, .quality = 10},
    {.id = 5, .cost = 2, .quality = 3},
    {.id = 6, .cost = 1, .quality = 1}
};

#define NUM_TASKS sizeof(tasks) / sizeof(task_t)

static int best_quality[K][B_MAX - B_MIN + 1];
static int best_parent[K][B_MAX - B_MIN + 1];

#define MAX_OPEN_SIZE 256
static state_t open_list[MAX_OPEN_SIZE];
static int open_size = 0;

static void pq_push(state_t state) {    
    if (open_size == MAX_OPEN_SIZE - 1) {
        fflush(stdout);
        int worst_idx = 0;
        int worst_f = open_list[0].f_value;
        for (int i = 1; i < open_size; i++) {
            if (open_list[i].f_value < worst_f) {
                worst_f = open_list[i].f_value;
                worst_idx = i;
            }
        }
        if (state.f_value > worst_f) {
            open_list[worst_idx] = state;
        }
        return;
    }
    open_list[open_size++] = state;
}

static state_t pq_pop_max() {
    int best_idx = 0;
    int best_f = open_list[0].f_value;
    
    for (int i = 1; i < open_size; i++) {
        if (open_list[i].f_value > best_f) {
            best_f = open_list[i].f_value;
            best_idx = i;
        }
    }
    
    state_t best = open_list[best_idx];
    // remove by moving last element to this position
    open_size--;
    open_list[best_idx] = open_list[open_size];
    return best;
}

static bool pq_empty() {
    return open_size == 0;
}

static int max_quality = 10;

static int calc_quality_at_end(int timeslot) {
    int remaining_slots = K - timeslot;
    return remaining_slots * max_quality;
}

static int reconstruct_path(int battery_level, int path[K]) {
    int quality = 0;
    for(int i = K - 1; i >= 0; i--) {
        path[i] = best_parent[i][battery_level - B_MIN];
        quality += tasks[path[i] - 2].quality;
        battery_level = MIN(B_MAX, battery_level + tasks[path[i] - 2].cost - E[i]);
    }
    return quality;
}

static int a_star(int path[K]) {
    memset(best_quality, -1, sizeof(best_quality));
    memset(best_parent, 0, sizeof(best_parent));
    open_size = 0;

    state_t start = {
        .timeslot = 0,
        .battery = B_START,
        .quality = 0,
        .f_value = calc_quality_at_end(0)
    };
    
    pq_push(start);
    best_quality[0][B_START - B_MIN] = 0;
    
    while (!pq_empty()) {
        state_t current = pq_pop_max();
        
        if (current.timeslot == K) {
            if (current.battery >= B_START) {
                return reconstruct_path(current.battery, path);
            }
            continue;
        }
        // expand
        for (int i = 0; i < NUM_TASKS; i++) {
            int new_battery = MIN(B_MAX, current.battery + E[current.timeslot] - tasks[i].cost);
            
            if (new_battery < B_MIN) {
                continue;
            }
            
            int new_quality = current.quality + tasks[i].quality;
            int next_t = current.timeslot + 1;
            
            // check if path is better
            if (best_quality[next_t - 1][new_battery - B_MIN] >= new_quality) {
                continue;
            }
            
            best_quality[next_t - 1][new_battery - B_MIN] = new_quality;
            best_parent[next_t - 1][new_battery - B_MIN] = tasks[i].id + 1;
            
            state_t next = {
                .timeslot = next_t,
                .battery = new_battery,
                .quality = new_quality,
                .f_value = new_quality + calc_quality_at_end(next_t)
            };
            
            pq_push(next);
        }
    }
    
    return -1;
}

int main() {
    int path[K] = { 0 };
    int quality = a_star(path);
    
    if (quality >= 0) {
        printf("Best quality: %d\n", quality);
        printf("Path: ");
        for (int i = 0; i < K; i++) {
            printf("%d ", path[i] - 1);
        }
        printf("\n");
    } else {
        printf("No solution found\n");
    }
    
    return 0;
}