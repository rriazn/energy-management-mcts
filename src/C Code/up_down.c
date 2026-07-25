#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>

#define MIN(X, Y) (((X) < (Y)) ? (X) : (Y))
#define MAX(X, Y) (((X) > (Y)) ? (X) : (Y))

#define K 24
#define B_START 20
#define B_MAX 30
#define B_MIN 10

#define NUM_TASKS 5

#define SUNRISE 15
#define SUNSET 0

static const int E [] = {3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4};

typedef struct task {
    int id;
    int cost;
    int quality;
} task_t;

static task_t tasks[] = {
    {.id = 1, .cost = 3, .quality = 5},
    {.id = 2, .cost = 2, .quality = 3},
    {.id = 3, .cost = 4, .quality = 6},
    {.id = 4, .cost = 8, .quality = 10},
    {.id = 5, .cost = 1, .quality = 1}
};

int t_copy_size = NUM_TASKS;
int t_copy_2_size = NUM_TASKS;

int comp(const void *a, const void *b) {
    const task_t *ta = a;
    const task_t *tb = b;

    double ra = (double)ta->quality / ta->cost;
    double rb = (double)tb->quality / tb->cost;

    if (ra > rb) return -1;
    if (ra < rb) return 1;

    // tie-break by quality
    if (ta->quality > tb->quality) return -1;
    if (ta->quality < tb->quality) return 1;

    return 0;
}

static void sort_plans() {
    qsort(tasks, NUM_TASKS, sizeof(task_t), comp);
}

static int get_idx_by_id(int id) {
    for(int i = 0; i < NUM_TASKS; i ++) {
        if(tasks[i].id == id) {
            return i;
        }
    }
    return -1;
}

static int battery_end(int plan[K]) {
    int battery = B_START;
    for(int i = 0; i < K; i++) {
        int idx = get_idx_by_id(plan[i]);
        battery = MIN(B_MAX, battery + E[i] - tasks[idx].cost);
    }
    return battery;
}

static bool check_battery_min(int plan[K]) {
    int battery = B_START;
    for(int i = 0; i < K; i++) {
        int idx = get_idx_by_id(plan[i]);
        battery = MIN(B_MAX, battery + E[i] - tasks[idx].cost);
        if(battery < B_MIN) {
            return false;
        }
    }
    return true;
}

static void eliminate_worse_tasks(int q_1, task_t tasks_copy[NUM_TASKS]) {
    for(int i = 0; i < t_copy_2_size; i++) {
        if(tasks[get_idx_by_id(q_1)].quality >= tasks_copy[i].quality) {
            for(int j = i; j < t_copy_2_size - 1; j++) {
                tasks_copy[j] = tasks_copy[j + 1];      // override, move rest forward
            }
            t_copy_2_size--;
            i--;
        }
    }
}

static void eliminate_better_tasks(int q_1, task_t tasks_copy[NUM_TASKS]) {
    for(int i = 0; i < t_copy_2_size; i++) {
        if(tasks[get_idx_by_id(q_1)].quality <= tasks_copy[i].quality) {
            for(int j = i; j < t_copy_2_size - 1; j++) {
                tasks_copy[j] = tasks_copy[j + 1];      // override, move rest forward
            }
            t_copy_2_size--;
            i--;
        }
    }
}

static void upgrade(int plan[K], task_t task) {
    int s = SUNRISE;
    int j = 1;
    while(battery_end(plan) - B_START >= task.cost - tasks[get_idx_by_id(plan[s])].cost && j <= K) {
        int H = plan[s];
        plan[s] = task.id;
        if(!check_battery_min(plan)) {
            plan[s] = H;
            return;
        }
        s = (s + 1) % K;
        j++;
    }
}

static void downgrade(int plan[K], task_t task) {
    int s = SUNSET;
    int j = 1;
    while((battery_end(plan) - B_START < 0 || !check_battery_min(plan)) && j <= K) {
        plan[s] = task.id;
        s = (s + 1) % K;
        j++;
    }
}

static int get_quality(int plan[K]) {
    int qual = 0;
    for(int i = 0; i < K; i++) {
        qual += tasks[get_idx_by_id(plan[i])].quality;
    }
    return qual;
}

static int initial_assignment(int S[K], int size) {
    sort_plans();
    for (int i = 0; i < K; i++) {
        S[i] = tasks[0].id;
    }
    int q_1 = tasks[0].id;
    int B_end = battery_end(S);
    task_t tasks_copy[NUM_TASKS], tasks_copy_2[NUM_TASKS];
    memcpy(tasks_copy, tasks, sizeof(tasks));
    memcpy(tasks_copy_2, tasks, sizeof(tasks));
    while(1){
        q_1 = tasks[0].id;
        if(B_end >= B_START && check_battery_min(S)) {
            memcpy(tasks_copy_2, tasks, sizeof(tasks));
            t_copy_2_size = NUM_TASKS;
            while(1) {
                eliminate_worse_tasks(q_1, tasks_copy_2);
                B_end = battery_end(S);
                if(B_end == B_START || t_copy_2_size == 0) {
                    return get_quality(S);
                }
                q_1 = tasks_copy_2[0].id;
                upgrade(S, tasks_copy_2[0]);
                memcpy(tasks_copy, tasks_copy_2, sizeof(tasks_copy_2));
                t_copy_size = t_copy_2_size;
            }
        }
        while(B_end < B_START || !check_battery_min(S)) {
            eliminate_better_tasks(q_1, tasks_copy_2);
            if(t_copy_2_size == 0) {
                return 0; // no solution
            }
            q_1 = tasks_copy_2[0].id;
            downgrade(S, tasks_copy_2[0]);
            B_end = battery_end(S);
        }
    } 
}

int main(int argc, char **argv) {
    int S[K] = { 0 };
    int qual = initial_assignment(S, sizeof(S));
    printf("Quality: %d\n", qual);
    printf("Path:\n");
    for(int i = 0; i < K; i++) {
        printf("%d, ", S[i]);
    }
    printf("\n");
}