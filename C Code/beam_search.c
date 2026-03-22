#include <stdio.h>
#include <stdint.h>


#define K       10
#define B_MAX   30
#define B_MIN   10
#define B_START 20
#define B_RANGE (B_MAX - B_MIN + 1)

#define TASK_COUNT 6
#define BEAM_WIDTH (TASK_COUNT / 3)   // same as Python: len(Tasks)/3 = 2

// Energy per timeslot
static const int8_t E[K] = {
    2, 0, 0, 0, 0, 0, 3, 8, 10, 7
};

typedef struct {
    int8_t id;
    int8_t cost;
    int8_t quality;
} Task;

static const Task Tasks[TASK_COUNT] = {
    {1,4,6},
    {2,3,5},
    {3,5,7},
    {4,8,10},
    {5,2,3},
    {6,1,1}
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

static inline float fast_exp_neg(float x) {
    if (x >= 10.0f) return 0.0f;
    if (x <= 0.0f) return 1.0f;

    int idx = (int)x;
    float frac = x - (float)idx;

    float y0 = EXP_TABLE[idx];
    float y1 = EXP_TABLE[idx + 1];

    return y0 + (y1 - y0) * frac;
}

// Node stored per (timeslot, battery)
typedef struct {
    uint8_t valid;
    int8_t  battery;        // absolute battery level
    int8_t  timeslot;       // 0..K
    int16_t best_quality;   // cumulative quality
    int8_t  parent_battery; // parent's battery level
    int8_t  parent_task;    // task id that led here
} Node;

static Node nodes[K + 1][B_RANGE];

// penalty(edge) equivalent: uses child battery and task quality
static inline float penalize(int8_t child_batt, int8_t task_quality) {
    if (child_batt == B_MIN) return 0.0f;

    float difference = (float)(B_START - child_batt);
    float scale = difference / (float)B_MIN;   // difference/B_min
    float x = 10.0f * scale;                   // k * scale, k=10
    float exp_term = fast_exp_neg(x);
    float penalty = (float)task_quality * (1.0f - exp_term);
    return (float)task_quality - penalty;
}

void beam_search(void) {
    // Clear all nodes
    for (int t = 0; t <= K; t++) {
        for (int b = 0; b < B_RANGE; b++) {
            nodes[t][b].valid = 0;
        }
    }

    // Beam holds battery levels (absolute) of current layer
    int8_t beam[B_RANGE];
    uint8_t beam_count = 1;
    beam[0] = B_START;  // root battery, timeslot 0, quality 0 (not stored in nodes)

    // Timeslots 0..K-1 produce children at t+1
    for (int t = 0; t < K; t++) {
        // Clear next layer nodes (t+1)
        for (int b = 0; b < B_RANGE; b++) {
            nodes[t + 1][b].valid = 0;
        }

        int8_t next_beam[B_RANGE];
        uint8_t next_count = 0;

        for (uint8_t i = 0; i < beam_count; i++) {
            int8_t parent_batt = beam[i];
            int16_t parent_quality;

            if (t == 0) {
                parent_quality = 0;  // root
            } else {
                int8_t pb_idx = parent_batt - B_MIN;
                parent_quality = nodes[t][pb_idx].best_quality;
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

                float edge_val;
                if (new_batt >= B_START) {
                    edge_val = (float)tk->quality;
                } else {
                    edge_val = penalize(new_batt, tk->quality);
                }

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

                Node *child = &nodes[t + 1][idx];
                if (!child->valid || new_quality > child->best_quality) {
                    child->valid         = 1;
                    child->battery       = nb;
                    child->timeslot      = t + 1;
                    child->best_quality  = new_quality;
                    child->parent_battery= parent_batt;
                    child->parent_task   = cand_task[c];
                }
            }
        }

        // Build next beam: all valid nodes at t+1
        for (int b = 0; b < B_RANGE; b++) {
            if (nodes[t + 1][b].valid) {
                next_beam[next_count++] = b + B_MIN;
            }
        }

        beam_count = next_count;
        for (uint8_t i = 0; i < beam_count; i++) {
            beam[i] = next_beam[i];
        }

        if (beam_count == 0) break; // no more nodes
    }
}

void reconstruct_path(void) {
    // Find best node at timeslot K
    int8_t best_batt = -1;
    int16_t best_q = -32768;

    for (int b = 0; b < B_RANGE; b++) {
        if (nodes[K][b].valid && nodes[K][b].best_quality > best_q) {
            best_q = nodes[K][b].best_quality;
            best_batt = b + B_MIN;
        }
    }

    if (best_batt < 0) {
        printf("No valid path\n");
        return;
    }

    // Backtrack
    int8_t tasks_seq[K];
    int idx = 0;
    int8_t batt = best_batt;
    int t = K;

    while (t > 0) {
        Node *n = &nodes[t][batt - B_MIN];
        if (!n->valid || n->parent_task <= 0) break;

        tasks_seq[idx++] = n->parent_task;
        batt = n->parent_battery;
        t--;
    }

    // Print reversed
    printf("Best quality: %d\n", best_q);
    printf("Tasks: ");
    for (int i = idx - 1; i >= 0; i--) {
        printf("%d ", tasks_seq[i]);
    }
    printf("\n");
}

int main(void) {
    beam_search();
    reconstruct_path();
    return 0;
}
