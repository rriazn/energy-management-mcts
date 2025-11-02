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
#define C sqrt(2)




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

typedef struct edge {
    int task_idx;
    struct node *parent;
    struct node *child;
} edge_t;

typedef struct node {
    int battery_level;
    int timeslot;
    struct edge_list *parents;
    struct edge_list *children;
    int visits;
    int win_quality;
    bool possible_tasks[NUM_TASKS];
} node_t;

typedef struct edge_list {
    edge_t **list;
    int size;
} edge_list_t;

static node_t *nodes[K][B_MAX - B_MIN + 1] = { NULL };

static void die(char *msg) {
    perror(msg);
    exit(EXIT_FAILURE);
}

static void append_edge(edge_list_t **list, edge_t *element) {
    if(*list == NULL) {
        *list = (edge_list_t *) malloc(sizeof(edge_list_t));
        if(NULL == *list) {
            die("malloc");
        }
        (*list)->list = (edge_t **) malloc(sizeof(edge_t *));
        if(NULL == (*list)->list) {
            die("malloc");
        }
        (*list)->list[0] = element;
        (*list)->size = 1;
    } else {
        edge_t **new_list = (edge_t **) realloc((*list)->list, ((*list)->size + 1) * sizeof(edge_t *));
        if(NULL == new_list) {
            die("realloc");
        }
        (*list)->list = new_list;
        (*list)->list[(*list)->size] = element;
        (*list)->size++;
    }
}

static void get_possible_tasks(node_t *node, bool possible_tasks[NUM_TASKS]);

static node_t *create_node(int battery_level, int timeslot, edge_t *parent) {
    node_t *node = (node_t *) malloc(sizeof(node_t));
    if(NULL == node) {
        die("malloc");
    }
    node->battery_level = battery_level;
    node->timeslot = timeslot;
    node->visits = 0;
    node->win_quality = 0;
    node->children = NULL;
    node->parents = NULL;
    bool pos_tasks[NUM_TASKS];
    memset(pos_tasks, false, sizeof(pos_tasks)); 
    get_possible_tasks(node, pos_tasks);
    memcpy(node->possible_tasks, pos_tasks, sizeof(pos_tasks));
    if(NULL != parent) {
        append_edge(&node->parents, parent);
    }
    return node;
}

static edge_t *create_edge(int task, node_t *parent, node_t *child) {
    edge_t *edge = (edge_t *) malloc(sizeof(edge_t));
    if(NULL == edge) {
        die("malloc");
    }
    edge->task_idx = task;
    edge->parent = parent;
    edge->child = child;
    return edge;
}

// Node functions

static void get_possible_tasks(node_t *node, bool possible_tasks[NUM_TASKS]) {
    if(node->timeslot == K) {
        return;
    }
    for(int i = 0; i < NUM_TASKS; i++) {
        if(node->battery_level + E[node->timeslot] - tasks[i].cost >= B_MIN) {
            possible_tasks[i] = true;
        }
    }
}

static bool is_fully_expanded(node_t *node) {
    for(int i = 0; i < NUM_TASKS; i++) {
        if(node->possible_tasks[i]) {
            return false;
        }
    }
    return true;
}

static bool is_terminal(node_t *node) {
    if(node->timeslot == K) {
        return true;
    }
    bool pos_tasks[NUM_TASKS];
    memset(pos_tasks, false, sizeof(pos_tasks)); 
    get_possible_tasks(node, pos_tasks);
    for(int i = 0; i < NUM_TASKS; i++) {
        if(pos_tasks[i]) {
            return false;
        }
    }
    return true;
}

static edge_t *expand(node_t *node) {
    int next_task_idx = -1;
    int new_battery = 0;
    bool new_child = false;

    // look for unexplored children
    while (!is_fully_expanded(node)) {
        for(int i = 0; i < NUM_TASKS; i++) {
            if(node->possible_tasks[i]) {
                node->possible_tasks[i] = false;
                next_task_idx = i;
                break;
            }
        }
        new_battery = node->battery_level + E[node->timeslot] - tasks[next_task_idx].cost;
        if(new_battery > B_MAX) {
            new_battery = B_MAX;
        }
        if(NULL != nodes[node->timeslot][new_battery - B_MIN]) {
            edge_t *edge = create_edge(next_task_idx, node, nodes[node->timeslot][new_battery - B_MIN]);
            append_edge(&(node->children), edge);
            append_edge(&(nodes[node->timeslot][new_battery - B_MIN]->parents), edge);
        } else {
            new_child = true;
            break;
        }
    }

    if(is_fully_expanded(node) && !new_child) {
        return NULL;
    }
    
    edge_t *edge = create_edge(next_task_idx, node, NULL);
    edge->child = create_node(new_battery, node->timeslot + 1, edge);
    nodes[node->timeslot][new_battery - B_MIN] = edge->child;
    append_edge(&(node->children), edge);
    return edge;
}

static edge_t *get_best_move(node_t *node) {
    float max_val = -1;
    edge_t *max_edge = NULL;
    for(int i = 0; i < node->children->size; i++) {
        node_t *child = node->children->list[i]->child;
        float val = ((float) child->win_quality / child->visits) + C * sqrt(log(node->visits) / child->visits);
        if(val > max_val) {
            max_val = val;
            max_edge = node->children->list[i];
        }
    }
    return max_edge;
}

static int simulate(node_t *node, int qual, int res[K]) {
    int sim_timeslot = node->timeslot;
    int sim_quality = qual;
    int sim_state_battery = node->battery_level;
    
    while(true) {
        if(K == sim_timeslot) {
            if(sim_state_battery < B_MIN) {
                sim_quality = 0;
            }
            return sim_quality;
        }

        // get random task
        int available_tasks[NUM_TASKS] = { 0 };
        int count = 0;
        for(int i = 0; i < NUM_TASKS; i++) {
            if(sim_state_battery + E[sim_timeslot] - tasks[i].cost >= B_MIN) {
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
        sim_state_battery = sim_state_battery + E[sim_timeslot] - tasks[chosen_task_idx].cost;
        if(sim_state_battery > B_MAX) {
            sim_state_battery = B_MAX;
        }
        res[sim_timeslot] = tasks[chosen_task_idx].id;
        sim_timeslot += 1;
    }
}

static void backpropagate(int result, node_t **path, int path_length) {
    for(int i = 0; i < path_length; i++) {
        path[i]->visits += 1;
        path[i]->win_quality += result;
    }
}

static int mcts(node_t *root, int iterations, int best_path[K]) {
    int best_quality = 0;

    for(int i = 0; i < iterations; i++) {
        node_t *node = root;
        edge_t *result = NULL;

        node_t *path[K + 1] = { NULL };
        path[0] = root;
        int path_length = 1;

        int task_path[K] = { 0 };
        int path_quality = 0;
        
        while (NULL == result) {
            // select
            while(!is_terminal(node) && is_fully_expanded(node)) {
                edge_t *best_move = get_best_move(node);
                node = best_move->child;
                path[path_length] = node;
                task_path[path_length - 1] = tasks[best_move->task_idx].id;
                path_length++;
                path_quality += tasks[best_move->task_idx].quality;
            }

            // expand
            if(!is_terminal(node)) {
                result = expand(node);
            } else {
                break;
            }
        }
        if(NULL != result) {
            node = result->child;
            path[path_length] = node;
            task_path[path_length - 1] = tasks[result->task_idx].id;
            
            path_length++;
            path_quality += tasks[result->task_idx].quality;
        }
        // simulate
        int res[K] = { 0 };
        int sim_quality = simulate(node, path_quality, res);
        if(sim_quality > best_quality) {
            best_quality = sim_quality;
            // concatenate paths to get full path
            for(int j = 0; j < K; j++) {
                if(task_path[j] != 0) {
                    best_path[j] = task_path[j];
                } else {
                    best_path[j] = res[j];
                }
            }
        }
        backpropagate(sim_quality, path, path_length);
    }
    return best_quality;
}

int main(int argc, char **argv) {
    srand(time(NULL));
    int best_path[K] = { 0 };
    node_t *root = create_node(B_START, 0, NULL);
    
    
    int ret = mcts(root, 500, best_path);
    int q = 0;
    printf("%d\n", ret);
    for(int i = 0; i < K; i++) {
        printf("%d\n", best_path[i]);
        q += tasks[best_path[i] - 1].quality;
    }
    return 0;
}