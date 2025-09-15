import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;
import java.util.ArrayList;
import org.json.JSONObject;
import org.json.JSONArray;

public class GreedyBot {
    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line;

        // This bot has a preferred order of moves. It will try them sequentially.
        String[] moveOrder = {"UP", "RIGHT", "DOWN", "LEFT"};

        while ((line = reader.readLine()) != null) {
            JSONObject state = new JSONObject(line);
            
            JSONObject board = state.getJSONObject("board");
            int width = board.getInt("width");
            int height = board.getInt("height");
            JSONArray grid = board.getJSONArray("grid");

            JSONObject head = state.getJSONObject("you").getJSONObject("head");
            int hx = head.getInt("x");
            int hy = head.getInt("y");
            
            String chosenMove = null;

            // Check each preferred move in order
            for (String move : moveOrder) {
                int nextX = hx;
                int nextY = hy;
                if (move.equals("UP")) nextY--;
                if (move.equals("DOWN")) nextY++;
                if (move.equals("LEFT")) nextX--;
                if (move.equals("RIGHT")) nextX++;

                // Check if the move is safe (not a wall or body)
                if (nextX >= 0 && nextX < width && nextY >= 0 && nextY < height) {
                    if (grid.getString(nextY).charAt(nextX) == '0') {
                        chosenMove = move;
                        break; // Found a safe move, stop searching
                    }
                }
            }

            // If no moves are safe, just pick the first preference and accept fate
            if (chosenMove == null) {
                chosenMove = moveOrder[0];
            }
            
            JSONObject response = new JSONObject();
            response.put("move", chosenMove);
            System.out.println(response.toString());
        }
    }
}