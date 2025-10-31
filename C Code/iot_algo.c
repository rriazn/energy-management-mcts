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
                        idmax = tasks[t].id;
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
                            idmax = tasks[t].id;
                        }
                    }
                }
            }
            opt[i][B] = qmax;
            schedule[i][B] = idmax;
        }
    }
}



int main(int argc, char **argv) {
    int schedule[K][B_MAX + 1] = { 0 };
    int opt[K][B_MAX + 1] = { 0 };
    solve(schedule, opt);

    printf("Schedule: \n");
    for(int i = 0; i < K; i++) {
        printf("[");
        for(int j = 0; j <= B_MAX; j++) {
            printf("%d ", schedule[i][j]);
        }
        printf("]\n");
    }

    printf("Quality: \n");
    for(int i = 0; i < K; i++) {
        printf("[");
        for(int j = 0; j <= B_MAX; j++) {
            printf("%d ", opt[i][j]);
        }
        printf("]\n");
    }
    return 0;
}