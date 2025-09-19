#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <json.hpp> 

using json = nlohmann::json;

int main() {
    json state;
    
    const std::vector<std::string> move_order = {"UP", "RIGHT", "DOWN", "LEFT"};
    const std::map<std::string, std::pair<int, int>> moves = {
        {"UP", {0, -1}}, {"DOWN", {0, 1}}, {"LEFT", {-1, 0}}, {"RIGHT", {1, 0}}
    };

    while (std::cin >> state) {
        try {
            int width = state["board"]["width"];
            int height = state["board"]["height"];
            auto grid = state["board"]["grid"];
            int hx = state["you"]["head"]["x"];
            int hy = state["you"]["head"]["y"];

            std::string chosen_move = move_order[0];

            for (const auto& move_name : move_order) {
                int dx = moves.at(move_name).first;
                int dy = moves.at(move_name).second;
                int nx = hx + dx;
                int ny = hy + dy;

                if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                    // --- THIS IS THE FIX ---
                    // First, get the row as a C++ string.
                    std::string row = grid[ny].get<std::string>();
                    // Then, access the character at the correct index.
                    if (row[nx] == '0') {
                        chosen_move = move_name;
                        break;
                    }
                }
            }
            
            json response;
            response["move"] = chosen_move;
            std::cout << response.dump() << std::endl;

        } catch (json::exception& e) {
            std::cerr << "JSON parsing error: " << e.what() << std::endl;
        }
    }
    
    return 0;
}