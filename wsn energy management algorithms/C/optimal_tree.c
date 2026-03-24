#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>
#include <stdint.h>

#define K       40
#define B_MAX   90
#define B_MIN   10
#define B_START 50
#define B_RANGE (B_MAX - B_MIN + 1)

#define TASK_COUNT 6

// Maximum number of nodes we expect to allocate
#define MAX_NODES (K * B_RANGE)

// Energy per timeslot
static const int E[] = {4, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 4, 5, 6, 8, 9, 9, 10, 10, 10, 9, 8, 7, 6, 5};

typedef struct {
    int8_t id;
    int8_t cost;
    int8_t quality;
} Task;

static const Task Tasks[TASK_COUNT] = {
    {1, 4, 6},
    {2, 3, 5},
    {3, 5, 7},
    {4, 8, 10},
    {5, 2, 3},
    {6, 1, 1}
};

typedef struct Edge_t {
    int8_t task_id;
    int8_t task_quality;
    struct Node_t *child;
} Edge;

typedef struct Node_t {
    int8_t  battery;
    int8_t  timeslot;
    int16_t best_quality;
    int8_t  parent_battery;
    int8_t  parent_task;

    Edge edges[TASK_COUNT];
    int8_t num_edges;
} Node;

static Node node_pool[MAX_NODES];
static uint16_t node_pool_index = 0;
static uint16_t allocated_nodes = 0;
static Node* nodes[K + 1][B_RANGE];

// Topological order
static Node* topo_order[MAX_NODES];
static uint16_t topo_count = 0;

static Node* allocate_node(void) {
    if (node_pool_index >= MAX_NODES) {
        return NULL;
    }
    allocated_nodes++;
    return &node_pool[node_pool_index++];
}

static void reset_node_pool(void) {
    node_pool_index = 0;
    allocated_nodes = 0;
    topo_count = 0;
}

// Add visited tracking
static bool visited[K + 1][B_RANGE];

static void dfs_topo(Node *node) {
    if (node == NULL) return;

    int t = node->timeslot;
    int b_idx = node->battery - B_MIN;

    // Already visited - skip
    if (visited[t][b_idx]) return;
    visited[t][b_idx] = true;

    // Process children first (post-order)
    for (int i = 0; i < node->num_edges; i++) {
        if (node->edges[i].child != NULL) {
            dfs_topo(node->edges[i].child);
        }
    }

    // Add to topological order
    topo_order[topo_count++] = node;
}

void generate_graph_and_topological_sort(void) {
    // Clear arrays
    for (int t = 0; t <= K; t++) {
        for (int b = 0; b < B_RANGE; b++) {
            nodes[t][b] = NULL;
            visited[t][b] = false;
        }
    }

    reset_node_pool();

    // Create root node
    Node *root = allocate_node();
    if (!root) {
        return;
    }
    root->battery = B_START;
    root->timeslot = 0;
    root->best_quality = -32768;  // Initialize to -infinity
    root->parent_battery = -1;
    root->parent_task = -1;
    root->num_edges = 0;
    nodes[0][B_START - B_MIN] = root;

    // Build graph layer by layer
    for (int t = 0; t < K; t++) {
        for (int b = 0; b < B_RANGE; b++) {
            Node *parent = nodes[t][b];
            if (parent == NULL) continue;

            // Try each task
            for (int ti = 0; ti < TASK_COUNT; ti++) {
                const Task *task = &Tasks[ti];

                int8_t new_batt = parent->battery + E[t] - task->cost;
                if (new_batt < B_MIN || new_batt > B_MAX) continue;

                int8_t child_idx = new_batt - B_MIN;
                Node *child = nodes[t + 1][child_idx];

                // Create child if doesn't exist
                if (child == NULL) {
                    child = allocate_node();
                    if (!child) {
                        return;
                    }
                    child->battery = new_batt;
                    child->timeslot = t + 1;
                    child->best_quality = -32768;  // -infinity
                    child->parent_battery = -1;
                    child->parent_task = -1;
                    child->num_edges = 0;
                    nodes[t + 1][child_idx] = child;
                }

                // Add edge from parent to child
                if (parent->num_edges < TASK_COUNT) {
                    parent->edges[parent->num_edges].task_id = task->id;
                    parent->edges[parent->num_edges].task_quality = task->quality;
                    parent->edges[parent->num_edges].child = child;
                    parent->num_edges++;
                }
            }
        }
    }

    // Perform DFS from root to get topological order
    dfs_topo(root);
}

static void find_best_path_topological(void) {
    if (topo_count == 0) {
        return;
    }

    // Initialize: root has quality 0
    Node *root = topo_order[topo_count - 1];  // Last in topo order = source
    root->best_quality = 0;

    // Process nodes in reverse topological order (root to leaves)
    for (int i = topo_count - 1; i >= 0; i--) {
        Node *u = topo_order[i];

        // Skip if unreachable
        if (u->best_quality == -32768) continue;

        // Relax all outgoing edges
        for (int j = 0; j < u->num_edges; j++) {
            Edge *e = &u->edges[j];
            Node *v = e->child;

            if (v == NULL) continue;

            int16_t new_quality = u->best_quality + e->task_quality;

            if (new_quality > v->best_quality) {
                v->best_quality = new_quality;
                v->parent_battery = u->battery;
                v->parent_task = e->task_id;
            }
        }
    }

    // Find best leaf node (timeslot = K, battery >= B_START)
    int8_t best_batt = -1;
    int16_t best_q = -32768;

    for (int b = 0; b < B_RANGE; b++) {
        Node *n = nodes[K][b];
        if (n != NULL && n->best_quality > best_q && (b + B_MIN) >= B_START) {
            best_q = n->best_quality;
            best_batt = b + B_MIN;
        }
    }

    if (best_batt < 0) {
        return;
    }

    // Reconstruct path
    int8_t tasks_seq[K];
    int idx = 0;
    int8_t batt = best_batt;
    int t = K;

    while (t > 0) {
        Node *n = nodes[t][batt - B_MIN];
        if (n == NULL || n->parent_task <= 0) break;

        tasks_seq[idx++] = n->parent_task;
        batt = n->parent_battery;
        t--;
    }
}


int main(int argc, char **argv) {
    generate_graph_and_topological_sort();
    find_best_path_topological();
}
