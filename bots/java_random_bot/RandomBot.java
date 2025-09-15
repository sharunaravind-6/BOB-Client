// bots/java_random_bot/RandomBot.java
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Random;
import org.json.JSONObject;
import org.json.JSONArray;

public class RandomBot {
    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        Random random = new Random();
        String line;

        // Need to download a simple JSON library.
        // The run.sh script will handle this.
        while ((line = reader.readLine()) != null) {
            JSONObject state = new JSONObject(line);
            
            JSONObject board = state.getJSONObject("board");
            int width = board.getInt("width");
            int height = board.getInt("height");
            JSONArray grid = board.getJSONArray("grid");

            JSONObject head = state.getJSONObject("you").getJSONObject("head");
            int hx = head.getInt("x");
            int hy = head.getInt("y");
            
            String[] possibleMoves = {"UP", "DOWN", "LEFT", "RIGHT"};
            ArrayList<String> safeMoves = new ArrayList<>();

            for (String move : possibleMoves) {
                int nextX = hx;
                int nextY = hy;
                if (move.equals("UP")) nextY--;
                if (move.equals("DOWN")) nextY++;
                if (move.equals("LEFT")) nextX--;
                if (move.equals("RIGHT")) nextX++;

                if (nextX < 0 || nextX >= width || nextY < 0 || nextY >= height) {
                    continue; // Wall collision
                }
                if (grid.getString(nextY).charAt(nextX) != '0') {
                    continue; // Body collision
                }
                safeMoves.add(move);
            }

            String chosenMove;
            if (!safeMoves.isEmpty()) {
                chosenMove = safeMoves.get(random.nextInt(safeMoves.size()));
            } else {
                chosenMove = possibleMoves[random.nextInt(possibleMoves.length)];
            }
            
            JSONObject response = new JSONObject();
            response.put("move", chosenMove);
            System.out.println(response.toString());
        }
    }
}