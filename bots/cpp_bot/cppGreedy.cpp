#include <iostream>
#include <string>
#include <vector>
#include <map>

// This is the header-only JSON library we downloaded in our Dockerfile.
#include <json.hpp> 

using json = nlohmann::json;

int main() {
    std::string line;
    
    // Preferred move order
    std::vector<std::string> move_order = {"UP", "RIGHT", "DOWN", "LEFT"};
    std::map<std::string, std::pair<int, int>> moves = {
        {"UP", {0, -1}}, {"DOWN", {0, 1}}, {"LEFT", {-1, 0}}, {"RIGHT", {1, 0}}
    };

    // Main game loop
    while (std::getline(std::cin, line)) {
        try {
            auto state = json::parse(line);

            int width = state["board"]["width"];
            int height = state["board"]["height"];
            auto grid = state["board"]["grid"];
            auto head = state["you"]["head"];
            int hx = head["x"];
            int hy = head["y"];

            std::string chosen_move = move_order[0]; // Default move if trapped

            // Find the first safe move in the preferred order
            for (const auto& move_name : move_order) {
                int dx = moves[move_name].first;
                int dy = moves[move_name].second;
                int nx = hx + dx;
                int ny = hy + dy;

                if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                    if (grid[ny][nx] == '0') {
                        chosen_move = move_name;
                        break; // Found a safe move, stop searching
                    }
                }
            }
            
            // Prepare and print the JSON response
            json response;
            response["move"] = chosen_move;
            std::cout << response.dump() << std::endl;

        } catch (json::parse_error& e) {
            // If JSON is invalid, do nothing and let the referee handle it.
        }
    }
    
    return 0;
}