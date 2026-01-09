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
#define BEAM_WIDTH 6

static const int E [] = {3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4};

typedef struct task {
    int id;
    int cost;
    int quality;
} task_t;

static const task_t tasks[] = {
    {.id = 6, .cost = 1, .quality = 1},
    {.id = 2, .cost = 3, .quality = 5},
    {.id = 5, .cost = 2, .quality = 3},
    {.id = 1, .cost = 4, .quality = 6},
    {.id = 4, .cost = 8, .quality = 10},
    {.id = 3, .cost = 5, .quality = 7}
};

#define NUM_TASKS sizeof(tasks) / sizeof(task_t)

static bool visited[K + 1][B_MAX - B_MIN + 1] = { 0 };
static bool chosen[K + 1][B_MAX - B_MIN + 1] = { 0 };               // chosen for beam search path
static bool adj[K + 1][B_MAX - B_MIN + 1][NUM_TASKS][2] = { 0 };    //last value: 0: outgoing edge (child); 1: incoming edge (parent) 
static int qualities[2][B_MAX - B_MIN + 1] = { 0 };                 // 2nd value: 0: last timeslot, 1: this timeslot
static int paths[2][B_MAX - B_MIN + 1][K] = { 0 };                  // same


static double penalize(int quality, int battery) {
    if(battery >= B_START) {
        return (double) quality;
    } else if (battery == B_MIN) {
        return 0;
    }
    int difference = B_START - battery;
    int k = 10;
    double scale = (double)difference / (double)B_MIN;
    double penalty = quality * (1 - exp(-k * scale));
    return (double)(quality) - penalty;
}


static void evaluate(int timeslot, int battery, int ret[BEAM_WIDTH]) {
    double values[BEAM_WIDTH] = { 0 };
    for(int t = 0; t < NUM_TASKS; t++) {
        if(adj[timeslot][battery - B_MIN][t][0]) {
            
            int new_battery = MIN(B_MAX, battery - tasks[t].cost + E[timeslot]);
            double edge_val = penalize(tasks[t].quality, new_battery);
            int min_idx = -1;
            double min_val = DBL_MAX;
            for(int i = 0; i < BEAM_WIDTH; i++) {
                if(values[i] < min_val) {
                    min_idx = i;
                    min_val = values[i];
                }
            }
            
            if(values[min_idx] < edge_val) {
                values[min_idx] = edge_val;
                ret[min_idx] = t + 1;
            }
        }
    }
}


static void expand(int timeslot, int battery) {
    for(int t = 0; t < NUM_TASKS; t++) {
        int new_battery = MIN(B_MAX, battery - tasks[t].cost + E[timeslot]);
        if(new_battery >= B_MIN) {
            if(visited[timeslot + 1][new_battery - B_MIN]) {
                adj[timeslot][battery - B_MIN][t][0] = true;
                adj[timeslot + 1][new_battery - B_MIN][t][1] = true;
                if(qualities[1][new_battery - B_MIN] < qualities[0][battery - B_MIN] + tasks[t].quality) {
                    qualities[1][new_battery - B_MIN] = qualities[0][battery - B_MIN] + tasks[t].quality; 
                    memcpy(paths[1][new_battery - B_MIN], paths[0][battery - B_MIN], sizeof(paths[0][0]));
                    paths[1][new_battery - B_MIN][timeslot] = t + 1;
                }
            } else {
                visited[timeslot + 1][new_battery - B_MIN] = true;
                adj[timeslot][battery - B_MIN][t][0] = true;
                adj[timeslot + 1][new_battery - B_MIN][t][1] = true;
                qualities[1][new_battery - B_MIN] = qualities[0][battery - B_MIN] + tasks[t].quality;
                memcpy(paths[1][new_battery - B_MIN], paths[0][battery - B_MIN], sizeof(paths[0][0]));
                paths[1][new_battery - B_MIN][timeslot] = t + 1;
            }
        }
    }
}

static void beam_search() {
    visited[0][B_START - B_MIN] = true;
    chosen[0][B_START - B_MIN] = true;
    for(int i = 0; i < K; i++) {
        for(int b = 0; b <= B_MAX - B_MIN; b++) {
            if(chosen[i][b]) {
                expand(i, b + B_MIN);
                int best_children[BEAM_WIDTH] = { 0 };
                evaluate(i, b + B_MIN, best_children);
                for(int j = 0; j < BEAM_WIDTH; j++) {
                    if(best_children[j] != 0) {
                        int new_battery = MIN(B_MAX - B_MIN, b + E[i] - tasks[best_children[j] - 1].cost);
                        chosen[i + 1][new_battery] = true;
                    }
                }
            }
        }
        //update qualities and paths
        memcpy(qualities[0], qualities[1], sizeof(qualities[0]));
        memset(qualities[1], 0, sizeof(qualities[1]));
        memcpy(paths[0], paths[1], sizeof(paths[0]));
        memset(paths[1], 0, sizeof(paths[1]));
    }
}

int main(int argc, char **argv) {
    beam_search();
    int max_qual = 0;
    int max_idx = 0;
    for(int b = B_START - B_MIN; b <= B_MAX - B_MIN; b++) {
        if(qualities[0][b] != 0 && chosen[24][b]) {
            printf("%d\n", qualities[0][b]);
            if(max_qual < qualities[0][b]) {
                max_idx = b;
                max_qual = qualities[0][b];
            }
        }
    }

    for(int i = 0; i < K; i++) {
        printf("%d, ", tasks[paths[0][max_idx][i] - 1].id);
    }
    printf("\n");
}