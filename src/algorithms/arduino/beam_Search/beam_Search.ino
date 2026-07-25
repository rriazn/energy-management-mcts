#include "nrf.h"

#define K       55
#define B_MAX   120
#define B_MIN   10
#define B_START 80
#define B_RANGE (B_MAX - B_MIN + 1)

#define TASK_COUNT 6
#define BEAM_WIDTH 2  

// Maximum number of nodes we expect to allocate
#define MAX_NODES (BEAM_WIDTH * K * 10)

// Energy per timeslot
static const int E[] = {4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 10, 10, 10, 9, 9, 8, 8, 7, 6, 5};

// Dynamic thresholds
static int8_t thresholds[K];

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

// Lookup table for exp(-x) from x=0..10
static const float EXP_TABLE[11] = {
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

typedef struct Node_t {
    int8_t  battery;
    int8_t  timeslot;
    int16_t best_quality;
    int8_t  parent_battery;
    int8_t  parent_task;
} Node;

static Node node_pool[MAX_NODES];
static uint16_t node_pool_index = 0;
static uint16_t allocated_nodes = 0;
static Node* nodes[K + 1][B_RANGE];

static inline float fast_exp_neg(float x) {
    if (x >= 10.0f) return 0.0f;
    if (x <= 0.0f) return 1.0f;

    int idx = (int)x;
    float frac = x - (float)idx;

    float y0 = EXP_TABLE[idx];
    float y1 = EXP_TABLE[idx + 1];

    return y0 + (y1 - y0) * frac;
}

static inline Node* allocate_node(void) {
    if (node_pool_index >= MAX_NODES) {
        return NULL;
    }
    allocated_nodes++;
    return &node_pool[node_pool_index++];
}

static inline void reset_node_pool(void) {
    node_pool_index = 0;
    allocated_nodes = 0;
}

// Calculate dynamic thresholds based on energy pattern
void calculate_thresholds(void) {
    // Find drought region
    int8_t drought_start = 0;
    int8_t drought_end = K - 1;
    
    for (int i = 1; i < K; i++) {
        if (E[i] == 0 && E[i-1] > 0) {
            drought_start = i;
            break;
        }
    }
    
    for (int i = K - 2; i >= 0; i--) {
        if (E[i] == 0 && E[i+1] > 0) {
            drought_end = i;
            break;
        }
    }
    
    int8_t peak = B_MAX;  // How high we hoard before drought
    
    if (drought_end < drought_start) {
        // Drought wraps around year
        for (int k = 0; k < drought_end; k++) {
            thresholds[k] = B_START;
        }
        for (int k = drought_end; k < drought_start; k++) {
            thresholds[k] = B_START + ((peak - B_START) * k) / drought_start;
        }
        int length = K - drought_start;
        for (int i = 0, k = drought_start; k < K - 1; i++, k++) {
            thresholds[k] = peak - ((peak - B_START) * i) / length;
        }
        thresholds[K - 1] = B_START;
    } else {
        // Rising phase (harvest region)
        for (int k = 0; k < drought_start; k++) {
            thresholds[k] = B_START + ((peak - B_START) * k) / drought_start;
        }
        
        // Falling phase (drought)
        int drought_len = drought_end - drought_start + 1;
        for (int i = 0, k = drought_start; k <= drought_end; i++, k++) {
            thresholds[k] = peak - ((peak - B_START) * i) / drought_len;
        }
        
        // After drought → fixed
        for (int k = drought_end + 1; k < K; k++) {
            thresholds[k] = B_START;
        }
    }
}

static inline float penalize(int8_t child_batt, int8_t child_timeslot, int8_t task_quality) {
    int8_t threshold = thresholds[child_timeslot - 1];
    
    if (child_batt >= threshold) {
        return (float)task_quality;
    }
    
    if (child_batt == B_MIN) {
        return 0.0f;
    }

    float difference = (float)(B_START - child_batt);
    float scale = difference / 10;  // 0.0 to 1.0
    float x = 10.0f * scale;
    float exp_term = fast_exp_neg(x);
    float penalty = (float)task_quality * (1.0f - exp_term);
    return (float)task_quality - penalty;
}

void beam_search(void) {
    // Clear pointer array
    for (int t = 0; t <= K; t++) {
        for (int b = 0; b < B_RANGE; b++) {
            nodes[t][b] = NULL;
        }
    }
    
    reset_node_pool();
    
    // Calculate thresholds before search
    calculate_thresholds();

    // Beam holds battery levels (absolute) of current layer
    int8_t beam[B_RANGE];
    uint8_t beam_count = 1;
    beam[0] = B_START;

    // Timeslots 0..K-1 produce children at t+1
    for (int t = 0; t < K; t++) {
        int8_t next_beam[B_RANGE];
        uint8_t next_count = 0;

        for (uint8_t i = 0; i < beam_count; i++) {
            int8_t parent_batt = beam[i];
            int16_t parent_quality;

            if (t == 0) {
                parent_quality = 0;
            } else {
                int8_t pb_idx = parent_batt - B_MIN;
                if (nodes[t][pb_idx] == NULL) continue;
                parent_quality = nodes[t][pb_idx]->best_quality;
            }

            // Per-parent beam: keep best BEAM_WIDTH children by edge value
            int8_t  cand_batt[BEAM_WIDTH];
            int8_t  cand_task[BEAM_WIDTH];
            float   cand_val[BEAM_WIDTH];
            uint8_t cand_count = 0;

            for (uint8_t ti = 0; ti < TASK_COUNT; ti++) {
                const Task *tk = &Tasks[ti];

                int8_t new_batt = parent_batt + E[t] - tk->cost;
                if (new_batt < B_MIN || new_batt > B_MAX) continue;

                // Use threshold-based penalty
                float edge_val = penalize(new_batt, t + 1, tk->quality);

                if (cand_count < BEAM_WIDTH) {
                    cand_batt[cand_count] = new_batt;
                    cand_task[cand_count] = tk->id;
                    cand_val[cand_count]  = edge_val;
                    cand_count++;
                } else {
                    // find worst candidate
                    uint8_t worst = 0;
                    for (uint8_t k = 1; k < cand_count; k++) {
                        if (cand_val[k] < cand_val[worst]) worst = k;
                    }
                    if (edge_val > cand_val[worst]) {
                        cand_batt[worst] = new_batt;
                        cand_task[worst] = tk->id;
                        cand_val[worst]  = edge_val;
                    }
                }
            }

            // Apply selected candidates to nodes[t+1]
            for (uint8_t c = 0; c < cand_count; c++) {
                int8_t nb = cand_batt[c];
                int8_t idx = nb - B_MIN;
                int16_t new_quality = parent_quality;

                // find task quality
                int8_t tq = 0;
                for (uint8_t ti = 0; ti < TASK_COUNT; ti++) {
                    if (Tasks[ti].id == cand_task[c]) {
                        tq = Tasks[ti].quality;
                        break;
                    }
                }
                new_quality += tq;

                Node *child = nodes[t + 1][idx];
                if (child == NULL) {
                    child = allocate_node();
                    if (child == NULL) {
                        Serial.println("ERROR: Out of node memory!");
                        return;
                    }
                    nodes[t + 1][idx] = child;
                    child->battery       = nb;
                    child->timeslot      = t + 1;
                    child->best_quality  = new_quality;
                    child->parent_battery= parent_batt;
                    child->parent_task   = cand_task[c];
                } else if (new_quality > child->best_quality) {
                    child->best_quality  = new_quality;
                    child->parent_battery= parent_batt;
                    child->parent_task   = cand_task[c];
                }
            }
        }

        // Build next beam: all valid nodes at t+1
        for (int b = 0; b < B_RANGE; b++) {
            if (nodes[t + 1][b] != NULL) {
                next_beam[next_count++] = b + B_MIN;
            }
        }

        beam_count = next_count;
        for (uint8_t i = 0; i < beam_count; i++) {
            beam[i] = next_beam[i];
        }

        if (beam_count == 0) break;
    }
}

void print_thresholds(void) {
    Serial.println("\n=== Thresholds ===");
    for (int t = 0; t < K; t++) {
        Serial.print("T");
        Serial.print(t);
        Serial.print(": ");
        Serial.println(thresholds[t]);
    }
}

void reconstruct_path(void) {
    // Find best node at timeslot K
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
        Serial.println("No valid path");
        return;
    }

    // Backtrack
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

    // Print reversed
    Serial.print("Best quality: ");
    Serial.println(best_q);
    Serial.print("Tasks: ");
    for (int i = idx - 1; i >= 0; i--) {
        Serial.print(tasks_seq[i]);
        Serial.print(" ");
    }
    Serial.println();
}

void print_memory_usage(void) {
    size_t pointer_array_size = sizeof(nodes);
    size_t node_pool_size = sizeof(node_pool);
    size_t allocated_node_size = allocated_nodes * sizeof(Node);
    size_t total_used = pointer_array_size + allocated_node_size;
    size_t total_reserved = pointer_array_size + node_pool_size;
    
    Serial.println("\n=== Memory Usage ===");
    Serial.print("Pointer array: ");
    Serial.print(pointer_array_size);
    Serial.println(" bytes");
    
    Serial.print("Node pool (reserved): ");
    Serial.print(node_pool_size);
    Serial.print(" bytes (");
    Serial.print(MAX_NODES);
    Serial.println(" nodes max)");
    
    Serial.print("Allocated nodes: ");
    Serial.print(allocated_nodes);
    Serial.print(" / ");
    Serial.print(MAX_NODES);
    Serial.print(" (");
    Serial.print((allocated_nodes * 100) / MAX_NODES);
    Serial.println("%)");
    
    Serial.print("Actual node memory used: ");
    Serial.print(allocated_node_size);
    Serial.println(" bytes");
    
    Serial.print("Total used: ");
    Serial.print(total_used);
    Serial.print(" bytes (");
    Serial.print(total_used / 1024.0, 2);
    Serial.println(" KB)");
    
    Serial.print("Total reserved: ");
    Serial.print(total_reserved);
    Serial.print(" bytes (");
    Serial.print(total_reserved / 1024.0, 2);
    Serial.println(" KB)");
}

void setup() {
    Serial.begin(115200);
    while (!Serial) {
        ;
    }

    Serial.println("Starting beam search with dynamic thresholds...");
    unsigned long start_time = micros();

    beam_search();

    unsigned long end_time = micros();
    Serial.print("Execution time: ");
    Serial.print(end_time - start_time);
    Serial.println(" us");

    reconstruct_path();
    print_thresholds();
    print_memory_usage();
}

void loop() {

}