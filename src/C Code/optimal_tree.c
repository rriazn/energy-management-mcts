#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "uthash.h"

#define K 24
#define B_START 20
#define B_MAX 30
#define B_MIN 10


typedef struct task {
    int id;
    int cost;
    int quality;
} task_t;

typedef struct edge {
    int task;
    struct node *parent;
    struct node *child;
} edge_t;

typedef struct node {
    int battery_level;
    int timeslot;
    struct edge_list *parents;
    struct edge_list *children;
} node_t;

typedef struct edge_list {
    edge_t **list;
    int size;
} edge_list_t;

static const task_t tasks[] = {
    {.id = 1, .cost = 3, .quality = 5},
    {.id = 2, .cost = 2, .quality = 3},
    {.id = 3, .cost = 4, .quality = 6},
    {.id = 4, .cost = 8, .quality = 10},
    {.id = 5, .cost = 1, .quality = 1}
};

static const int num_tasks = sizeof(tasks) / sizeof(task_t);

static const int E [] = {3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 6, 6, 6, 6, 5, 5, 4};

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

static void get_possible_tasks(node_t *node, int possible_tasks[num_tasks]) {
    for(int i = 0; i < num_tasks; i++) {
        if(node->battery_level + E[node->timeslot] - tasks[i].cost >= B_MIN) {
            possible_tasks[i] = 1;
        }
    }
}

static node_t *create_node(int battery_level, int timeslot, edge_t *parent) {
    node_t *node = (node_t *) malloc(sizeof(node_t));
    if(NULL == node) {
        die("malloc");
    }
    node->battery_level = battery_level;
    node->timeslot = timeslot;
    node->children = NULL;
    node->parents = NULL;
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
    edge->task = task;
    edge->parent = parent;
    edge->child = child;
    return edge;
}

static node_t *generate_tree() {
    node_t *root = create_node(B_START, 0, NULL);
    node_t *last_timeslot [B_MAX - B_MIN + 1] = { NULL };
    last_timeslot[root->battery_level - B_MIN] = root;

    for(int i = 0; i < K; i++) {
        node_t *battery_level_nodes [B_MAX - B_MIN + 1] = { NULL };
        for(int j = 0; j < sizeof(battery_level_nodes) / sizeof(node_t*); j++) {
            if(NULL != last_timeslot[j]) {
                node_t *curr_node = last_timeslot[j];
                int possible_tasks[num_tasks];
                memset(possible_tasks, 0, sizeof(possible_tasks));
                get_possible_tasks(curr_node, possible_tasks); 
                for(int t = 0; t < num_tasks; t++) {
                    if(1 == possible_tasks[t]) {
                        int battery_level = curr_node->battery_level + E[curr_node->timeslot] - tasks[t].cost;
                        if(battery_level > B_MAX) {
                            battery_level = B_MAX;
                        }
                        edge_t *edge = NULL;
                        battery_level -= B_MIN;

                        // Node already exists, add edge
                        if(NULL != battery_level_nodes[battery_level]) {
                            edge = create_edge(t, curr_node, battery_level_nodes[battery_level]);
                            append_edge(&(battery_level_nodes[battery_level]->parents), edge);
                        } else {
                            edge = create_edge(t, curr_node, NULL);
                            battery_level_nodes[battery_level] = create_node(battery_level + B_MIN, curr_node->timeslot + 1, edge);
                            edge->child = battery_level_nodes[battery_level];
                        }
                        append_edge(&(curr_node->children), edge);
                    }
                    
                }
            }
        }
        memcpy(last_timeslot, battery_level_nodes, sizeof(last_timeslot));
    }
    return root;
}

// Hash map necessities

typedef struct result {
    int quality;
    int task_path[K];
} result_t;

typedef struct visited {
    node_t *key;
    result_t *value;
    UT_hash_handle hh;
} visited_t;

static visited_t *visited = NULL;

static result_t *visit_node(node_t *node, int quality, int task_path[K]) {
    visited_t *entry;
    HASH_FIND_PTR(visited, &node, entry);
    if(NULL == entry) {
        entry = (visited_t *) malloc(sizeof(visited_t));
        if(NULL == entry) {
            die("malloc");
        }
        entry->key = node;
        entry->value = (result_t *) malloc(sizeof(result_t));
        if(NULL == entry->value) {
            die("malloc");
        }
        entry->value->quality = quality;
        memcpy(entry->value->task_path, task_path, sizeof(entry->value->task_path));
        HASH_ADD_PTR(visited, key, entry);
    } else {
        if(entry->value->quality < quality) {
            entry->value->quality = quality;
            memcpy(entry->value->task_path, task_path, sizeof(entry->value->task_path));
        }
    }
    return entry->value;
}

int get_visited(node_t *node, result_t **out) {
    visited_t *entry;
    HASH_FIND_PTR(visited, &node, entry);
    if(NULL != entry) {
        *out = entry->value;
        return 1;
    }
    return 0;
}

result_t *find_best_path(node_t *root) {
    result_t *res;
    if(get_visited(root, &res)) {
        return res;
    }

    int best_task_id = 0;
    int best_quality = -1;

    // leaf
    if(NULL == root->children) {
        int task_path[K] = { 0 };
        if(root->timeslot != K || root->battery_level < B_START) {
            visit_node(root, -1, task_path);
        } else {
            visit_node(root, 0, task_path);
        }
        get_visited(root, &res);
        return res;
    }
    int best_path [K] = { 0 };
    // middle node
    for(int i = 0; i < root->children->size; i++) {
        result_t *child_res = find_best_path(root->children->list[i]->child);
        int qual = child_res->quality;
        if(qual != -1) {
            qual += tasks[root->children->list[i]->task].quality;
            if(qual > best_quality) {
                best_quality = qual;
                best_task_id = tasks[root->children->list[i]->task].id;
                memcpy(best_path, child_res->task_path, sizeof(best_path));
            }
        }
    }
    best_path[root->timeslot] = best_task_id;

    return visit_node(root, best_quality, best_path);
}

int main(int argc, char **argv) {
    node_t *root = generate_tree();
    result_t *res = find_best_path(root);
    printf("%d\n", res->quality);
    for(int i = 0; i < K; i++) {
        printf("%d\n", res->task_path[i]);
    }
    return 0;
}
