#include <stdlib.h>
#include <stdio.h>

#define K 24
#define B_START 20
#define B_MAX 30
#define B_MIN 10

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

static const int num_tasks = sizeof(tasks) / sizeof(task_t);

static const int E [] = {3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4};


static void die(const char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}


static void solve(int schedule[K][B_MAX + 1], int opt[K][B_MAX + 1]) {
    for(int i = K - 1; i >= 0; i--) {
        for(int B = 0; B <= B_MAX; B++) {
            int qmax = -100;
            int idmax = -1;
            for(int t = 0; t < num_tasks; t++) {
                if(i == K - 1) {
                    if(B - tasks[t].cost + E[i] >= B_START && tasks[t].quality > qmax) {
                        qmax = tasks[t].quality;
                        idmax = t;
                    }
                } else {
                    int Br = B - tasks[t].cost + E[i];
                    if(Br > B_MAX) {
                        Br = B_MAX;
                    }
                    if(Br >= B_MIN) {
                        int q = opt[i + 1][Br];
                        if(q != 0 && q + tasks[t].quality > qmax) {
                            qmax = q + tasks[t].quality;
                            idmax = t;
                        }
                    }
                }
            }
            opt[i][B] = qmax;
            schedule[i][B] = idmax;
        }
    }
    int battery = B_START;
    for(int i = 0; i < K; i++) {
        task_schedule[i] = tasks[schedule[i][battery]].id;
        battery = battery + E[i] - tasks[task_schedule[i]].cost;
        if(B_MAX < battery) {
            battery = B_MAX;
        }
    }
    return opt[0][B_START];

}



int main(int argc, char **argv) {
    int task_schedule[K] = { 0 };
    int quality = solve(task_schedule);

    printf("Schedule: \n");
    printf("[");
    for(int i = 0; i < K; i++) {
        printf("%d ", task_schedule[i]);
    }
    printf("]\n");

    printf("Quality: %d\n", quality);
    
    return 0;
}