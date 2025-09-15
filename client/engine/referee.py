# client/engine/referee.py
import sys
import json
import subprocess
import shlex
from .game import Snake, Board

# --- Configurable Game Constants ---
BOARD_WIDTH = 30
BOARD_HEIGHT = 20
TIME_LIMIT_MS = 500
MAX_TURNS = 500
# -----------------------------------

def get_game_state(turn, board, p1, p2):
    """Creates a dictionary representing the current game state for logging."""
    return {
        "turn": turn,
        "board": { "width": board.width, "height": board.height },
        "p1": {
            "head": {"x": p1.head[0], "y": p1.head[1]},
            "body": [{"x": pos[0], "y": pos[1]} for pos in p1.body],
            "alive": p1.is_alive
        },
        "p2": {
            "head": {"x": p2.head[0], "y": p2.head[1]},
            "body": [{"x": pos[0], "y": pos[1]} for pos in p2.body],
            "alive": p2.is_alive
        }
    }

def get_json_for_bot(turn_state, player_key, opponent_key):
    """Builds the specific JSON string that a bot receives."""
    you = turn_state[player_key]
    opponent = turn_state[opponent_key]

    grid = [[0 for _ in range(turn_state["board"]["height"])] for _ in range(turn_state["board"]["width"])]
    for part in you["body"]:
        grid[part["x"]][part["y"]] = 1
    for part in opponent["body"]:
        grid[part["x"]][part["y"]] = 2

    grid_str = ["".join(map(str, [grid[x][y] for x in range(turn_state["board"]["width"])])) for y in range(turn_state["board"]["height"])]
    
    # --- THIS IS THE FIX ---
    # Create a new board object for the bot and put the grid inside it.
    board_for_bot = turn_state["board"].copy()
    board_for_bot["grid"] = grid_str

    bot_view = {
        "turn": turn_state["turn"],
        "board": board_for_bot, # Use the corrected board object
        # "grid" is no longer a top-level key
        "you": { "id": player_key, "head": you["head"], "body": you["body"], "length": len(you["body"]) },
        "opponent": { "id": opponent_key, "head": opponent["head"], "body": opponent["body"], "length": len(opponent["body"]) },
    }
    return json.dumps(bot_view)
# -----------------------

def main():
    bot1_cmd_str, bot2_cmd_str = sys.argv[1], sys.argv[2]
    bot1_args, bot2_args = shlex.split(bot1_cmd_str), shlex.split(bot2_cmd_str)
    p1_proc = subprocess.Popen(bot1_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    p2_proc = subprocess.Popen(bot2_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    snakes = [Snake("p1", (BOARD_WIDTH//4, BOARD_HEIGHT//2), (1,0)), Snake("p2", (BOARD_WIDTH*3//4, BOARD_HEIGHT//2), (-1,0))]
    board = Board(BOARD_WIDTH, BOARD_HEIGHT)
    
    game_log = {"frames": [], "result": {}}
    turn = 0
    
    while all(s.is_alive for s in snakes) and turn < MAX_TURNS:
        current_state = get_game_state(turn, board, snakes[0], snakes[1])
        game_log["frames"].append(current_state)

        p1_json = get_json_for_bot(current_state, "p1", "p2")
        p2_json = get_json_for_bot(current_state, "p2", "p1")

        p1_proc.stdin.write(p1_json + "\n"); p1_proc.stdin.flush()
        p2_proc.stdin.write(p2_json + "\n"); p2_proc.stdin.flush()

        try:
            p1_move = json.loads(p1_proc.stdout.readline().strip())["move"]
            p2_move = json.loads(p2_proc.stdout.readline().strip())["move"]
        except (IOError, json.JSONDecodeError):
            snakes[0].is_alive = False; snakes[1].is_alive = False
            break

        snakes[0].move(p1_move); snakes[1].move(p2_move)
        board.update(snakes)
        turn += 1

    game_log["frames"].append(get_game_state(turn, board, snakes[0], snakes[1]))

    p1_alive, p2_alive = snakes[0].is_alive, snakes[1].is_alive
    winner = "Draw"
    if p1_alive and not p2_alive: winner = "Player 1 Wins!"
    elif not p1_alive and p2_alive: winner = "Player 2 Wins!"
    elif turn >= MAX_TURNS: winner = "Draw (Max turns reached)"
    
    game_log["result"] = {"winner": winner, "p1_length": snakes[0].length, "p2_length": snakes[1].length}
    print(json.dumps(game_log))

    p1_proc.kill(); p2_proc.kill()

if __name__ == "__main__":
    main()