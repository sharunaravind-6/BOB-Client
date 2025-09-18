#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <jansson.h>

// Simple helper to get an integer from a JSON object
int get_int(json_t *obj, const char *key) {
    return json_integer_value(json_object_get(obj, key));
}

int main() {
    char *line = NULL;
    size_t len = 0;
    ssize_t read;
    
    // Preferred move order
    const char *move_order[] = {"UP", "RIGHT", "DOWN", "LEFT"};
    const int dx[] = {0, 1, 0, -1};
    const int dy[] = {-1, 0, 1, 0};

    // Main game loop: read one line of JSON from stdin
    while ((read = getline(&line, &len, stdin)) != -1) {
        json_error_t error;
        json_t *root = json_loads(line, 0, &error);

        if (!root) {
            continue;
        }

        // Parse JSON
        json_t *board = json_object_get(root, "board");
        int width = get_int(board, "width");
        int height = get_int(board, "height");
        json_t *grid_arr = json_object_get(board, "grid");

        json_t *you = json_object_get(root, "you");
        json_t *head = json_object_get(you, "head");
        int hx = get_int(head, "x");
        int hy = get_int(head, "y");
        
        char *chosen_move = (char*)move_order[0]; // Default move if trapped

        // Find the first safe move in the preferred order
        for (int i = 0; i < 4; i++) {
            int nx = hx + dx[i];
            int ny = hy + dy[i];

            if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                const char *row = json_string_value(json_array_get(grid_arr, ny));
                if (row[nx] == '0') {
                    chosen_move = (char*)move_order[i];
                    break;
                }
            }
        }
        
        // Prepare and print the JSON response
        json_t *response = json_object();
        json_object_set_new(response, "move", json_string(chosen_move));
        char *response_str = json_dumps(response, 0);
        printf("%s\n", response_str);
        fflush(stdout);

        // Free memory
        free(response_str);
        json_decref(root);
        json_decref(response);
    }
    
    if (line) free(line);
    return 0;
}