/*
 * ============================================================================
 * Project: University Examination Scheduling Using Graphs
 * Module:  c_engine/scheduler.c
 * 
 * Description:
 *   Standalone C11 implementation of the Greedy Graph Coloring algorithm
 *   using a 2D Adjacency Matrix to schedule university examinations without
 *   time slot conflicts.
 *
 * Algorithm Overview:
 *   1. Graph Representation:
 *      - Vertices: Examination subjects (0 to N - 1 internally).
 *      - Edges: Conflicts between subjects (at least one student enrolled in both).
 *      - Data Structure: Fixed-size 2D Adjacency Matrix graph[MAX_SUBJECTS][MAX_SUBJECTS].
 *   2. Greedy Graph Coloring:
 *      - Assign time slots (colors) one subject at a time.
 *      - For the current subject, examine all neighbors in the adjacency matrix.
 *      - Mark slots used by already-scheduled conflicting neighbors as unavailable.
 *      - Pick the lowest available slot number (starting from 0 internally).
 *      - Repeat for all subjects.
 *   3. Complexity:
 *      - Time Complexity: O(N^2) where N is the number of subjects.
 *      - Space Complexity: O(MAX_SUBJECTS^2) for the adjacency matrix.
 *
 * Input Protocol (stdin):
 *   Line 1: N (number of subjects, 1 <= N <= 20)
 *   Line 2: E (number of conflicts, 0 <= E <= N * (N - 1) / 2)
 *   Next E lines: a b (two 1-based subject indices per line)
 *
 * Output Protocol (stdout):
 *   Line 1: K (total number of time slots used)
 *   Next N lines: assigned 1-based time slot for each subject in order
 *
 * Error Handling (stderr):
 *   Prints descriptive diagnostic messages to stderr and exits with status 1.
 * ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_SUBJECTS 20
#define BUFFER_SIZE 256

/* Function Prototypes */
static int read_trimmed_line(char *buffer, size_t size);
static int parse_single_integer(const char *buffer, int *out_value);
static int parse_two_integers(const char *buffer, int *out_a, int *out_b);
static void greedy_graph_coloring(int n, const int graph[MAX_SUBJECTS][MAX_SUBJECTS], int slots[MAX_SUBJECTS], int *out_total_slots);

int main(void) {
    char line[BUFFER_SIZE];
    int num_subjects = 0;
    int num_conflicts = 0;
    int graph[MAX_SUBJECTS][MAX_SUBJECTS];
    int slots[MAX_SUBJECTS];
    int total_slots = 0;

    /* Initialize the adjacency matrix to 0 (no conflicts) */
    for (int i = 0; i < MAX_SUBJECTS; i++) {
        for (int j = 0; j < MAX_SUBJECTS; j++) {
            graph[i][j] = 0;
        }
    }

    /* ------------------------------------------------------------------------
     * Step 1: Read and validate the number of subjects (N)
     * ------------------------------------------------------------------------ */
    if (!read_trimmed_line(line, sizeof(line))) {
        fprintf(stderr, "Error: Missing input for number of subjects.\n");
        return 1;
    }

    if (!parse_single_integer(line, &num_subjects)) {
        fprintf(stderr, "Error: Number of subjects must be an integer.\n");
        return 1;
    }

    if (num_subjects < 1 || num_subjects > MAX_SUBJECTS) {
        fprintf(stderr, "Error: Number of subjects must be between 1 and %d (received %d).\n",
                MAX_SUBJECTS, num_subjects);
        return 1;
    }

    /* ------------------------------------------------------------------------
     * Step 2: Read and validate the number of conflicts (E)
     * ------------------------------------------------------------------------ */
    if (!read_trimmed_line(line, sizeof(line))) {
        fprintf(stderr, "Error: Missing input for number of conflicts.\n");
        return 1;
    }

    if (!parse_single_integer(line, &num_conflicts)) {
        fprintf(stderr, "Error: Number of conflicts must be an integer.\n");
        return 1;
    }

    int max_possible_edges = (num_subjects * (num_subjects - 1)) / 2;
    if (num_conflicts < 0 || num_conflicts > max_possible_edges) {
        fprintf(stderr, "Error: Number of conflicts must be between 0 and %d for %d subjects (received %d).\n",
                max_possible_edges, num_subjects, num_conflicts);
        return 1;
    }

    /* ------------------------------------------------------------------------
     * Step 3: Read and validate each conflict pair (a, b)
     * ------------------------------------------------------------------------ */
    for (int e = 0; e < num_conflicts; e++) {
        if (!read_trimmed_line(line, sizeof(line))) {
            fprintf(stderr, "Error: Premature end of input while reading conflict %d of %d.\n",
                    e + 1, num_conflicts);
            return 1;
        }

        int u_1based = 0;
        int v_1based = 0;
        if (!parse_two_integers(line, &u_1based, &v_1based)) {
            fprintf(stderr, "Error: Invalid conflict format at line %d. Expected two integers 'a b'.\n",
                    e + 1);
            return 1;
        }

        /* Validate subject index boundaries */
        if (u_1based < 1 || u_1based > num_subjects) {
            fprintf(stderr, "Error: Subject index %d out of bounds (valid range: 1 to %d).\n",
                    u_1based, num_subjects);
            return 1;
        }
        if (v_1based < 1 || v_1based > num_subjects) {
            fprintf(stderr, "Error: Subject index %d out of bounds (valid range: 1 to %d).\n",
                    v_1based, num_subjects);
            return 1;
        }

        /* A subject cannot conflict with itself */
        if (u_1based == v_1based) {
            fprintf(stderr, "Error: Self-conflict detected for subject %d. A subject cannot conflict with itself.\n",
                    u_1based);
            return 1;
        }

        /* Convert 1-based indices to 0-based indices for internal matrix access */
        int u = u_1based - 1;
        int v = v_1based - 1;

        /* Update adjacency matrix (undirected graph: symmetric entries) */
        graph[u][v] = 1;
        graph[v][u] = 1;
    }

    /* ------------------------------------------------------------------------
     * Step 4: Execute Greedy Graph Coloring
     * ------------------------------------------------------------------------ */
    greedy_graph_coloring(num_subjects, graph, slots, &total_slots);

    /* ------------------------------------------------------------------------
     * Step 5: Output results in machine-readable protocol
     * Line 1: K (total slots)
     * Next N lines: 1-based slot assignment per subject
     * ------------------------------------------------------------------------ */
    printf("%d\n", total_slots);
    for (int i = 0; i < num_subjects; i++) {
        /* Convert 0-based internal slot to 1-based output slot */
        printf("%d\n", slots[i] + 1);
    }

    return 0;
}

/*
 * Reads a line from stdin, removes leading/trailing whitespace and newline.
 * Returns 1 on success, 0 on EOF or error.
 */
static int read_trimmed_line(char *buffer, size_t size) {
    if (fgets(buffer, (int)size, stdin) == NULL) {
        return 0;
    }

    /* Remove trailing newline / carriage return */
    size_t len = strlen(buffer);
    while (len > 0 && (buffer[len - 1] == '\n' || buffer[len - 1] == '\r')) {
        buffer[len - 1] = '\0';
        len--;
    }

    /* Trim leading whitespace */
    char *start = buffer;
    while (*start && isspace((unsigned char)*start)) {
        start++;
    }

    /* Trim trailing whitespace */
    char *end = start + strlen(start);
    while (end > start && isspace((unsigned char)*(end - 1))) {
        end--;
        *end = '\0';
    }

    /* Shift trimmed string to buffer start if needed */
    if (start != buffer) {
        memmove(buffer, start, strlen(start) + 1);
    }

    return 1;
}

/*
 * Parses exactly one integer from the string buffer.
 * Rejects trailing non-whitespace characters.
 * Returns 1 on success, 0 on failure.
 */
static int parse_single_integer(const char *buffer, int *out_value) {
    char extra = '\0';
    int val = 0;
    if (sscanf(buffer, "%d %c", &val, &extra) == 1) {
        *out_value = val;
        return 1;
    }
    return 0;
}

/*
 * Parses exactly two integers from the string buffer.
 * Rejects trailing non-whitespace characters.
 * Returns 1 on success, 0 on failure.
 */
static int parse_two_integers(const char *buffer, int *out_a, int *out_b) {
    char extra = '\0';
    int a = 0;
    int b = 0;
    if (sscanf(buffer, "%d %d %c", &a, &b, &extra) == 2) {
        *out_a = a;
        *out_b = b;
        return 1;
    }
    return 0;
}

/*
 * Implements Greedy Graph Coloring.
 *
 * Parameters:
 *   n               - Number of vertices (subjects)
 *   graph           - Adjacency matrix of conflicts
 *   slots           - Array to store assigned slot per subject (0-based)
 *   out_total_slots - Output pointer for total number of slots used
 */
static void greedy_graph_coloring(int n, const int graph[MAX_SUBJECTS][MAX_SUBJECTS], int slots[MAX_SUBJECTS], int *out_total_slots) {
    /* Initialize all subjects with unassigned slot (-1) */
    for (int i = 0; i < n; i++) {
        slots[i] = -1;
    }

    /*
     * Array to keep track of available time slots.
     * available[c] == 1 means slot 'c' is available.
     * available[c] == 0 means slot 'c' is already occupied by a conflicting subject.
     */
    int available[MAX_SUBJECTS];

    /* Assign time slots to subjects sequentially */
    for (int u = 0; u < n; u++) {
        /* Initially, mark all slots as available for subject u */
        for (int c = 0; c < MAX_SUBJECTS; c++) {
            available[c] = 1;
        }

        /* Check all neighbors of subject u in the adjacency matrix */
        for (int v = 0; v < n; v++) {
            if (graph[u][v] == 1 && slots[v] != -1) {
                /* Subject v is conflicting and already assigned a slot.
                 * Mark that slot as unavailable for subject u. */
                available[slots[v]] = 0;
            }
        }

        /* Find the first (smallest index) available slot */
        int chosen_slot = -1;
        for (int c = 0; c < MAX_SUBJECTS; c++) {
            if (available[c] == 1) {
                chosen_slot = c;
                break;
            }
        }

        slots[u] = chosen_slot;
    }

    /* Determine total number of slots used (max assigned slot index + 1) */
    int max_slot = 0;
    for (int i = 0; i < n; i++) {
        if (slots[i] > max_slot) {
            max_slot = slots[i];
        }
    }
    *out_total_slots = max_slot + 1;
}

