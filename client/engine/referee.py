# client/engine/referee.py
import sys
import json
import subprocess
import time
from .game import Snake, Board

# --- Configurable Game Constants ---
BOARD_WIDTH = 30
BOARD_HEIGHT = 20
TIME_LIMIT_MS = 500
# -----------------------------------

def get_game_state_json(turn, board, p1, p2):
    """Builds the JSON game state object for a specific player."""
    grid_str = ["".join(map(str, [board.grid[x][y] for x in range(board.width)])) for y in range(board.height)]
    
    state = {
        "turn": turn,
        "board": {
            "height": board.height,
            "width": board.width,
            "grid": grid_str
        },
        "you": {
            "id": p1.id,
            "head": {"x": p1.head[0], "y": p1.head[1]},
            "body": [{"x": pos[0], "y": pos[1]} for pos in p1.body],
            "length": p1.length
        },
        "opponent": {
            "id": p2.id,
            "head": {"x": p2.head[0], "y": p2.head[1]},
            "body": [{"x": pos[0], "y": pos[1]} for pos in p2.body],
            "length": p2.length
        }
    }
    return json.dumps(state)

def main():
    if len(sys.argv) < 3:
        print("Usage: python referee.py <path_to_bot1_run.sh> <path_to_bot2_run.sh>")
        sys.exit(1)

    bot1_cmd = sys.argv[1]
    bot2_cmd = sys.argv[2]

    p1 = subprocess.Popen(bot1_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    p2 = subprocess.Popen(bot2_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    # Starting positions
    p1_start_pos = (BOARD_WIDTH // 4, BOARD_HEIGHT // 2)
    p2_start_pos = (BOARD_WIDTH * 3 // 4, BOARD_HEIGHT // 2)
    snakes = [
        Snake("p1", p1_start_pos, (1, 0)), # Start moving right
        Snake("p2", p2_start_pos, (-1, 0)) # Start moving left
    ]
    board = Board(BOARD_WIDTH, BOARD_HEIGHT)
    board.update(snakes)

    turn = 0
    while all(s.is_alive for s in snakes):
        # Send state to Player 1
        p1_state = get_game_state_json(turn, board, snakes[0], snakes[1])
        p1.stdin.write(p1_state + "\n")
        p1.stdin.flush()

        # Send state to Player 2 (swap you/opponent)
        p2_state = get_game_state_json(turn, board, snakes[1], snakes[0])
        p2.stdin.write(p2_state + "\n")
        p2.stdin.flush()

        # Get moves
        try:
            p1_move = json.loads(p1.stdout.readline().strip())["move"]
            p2_move = json.loads(p2.stdout.readline().strip())["move"]
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading bot output: {e}")
            break

        snakes[0].move(p1_move)
        snakes[1].move(p2_move)

        board.update(snakes)
        turn += 1

    # --- Determine Winner ---
    p1_alive = snakes[0].is_alive
    p2_alive = snakes[1].is_alive

    if p1_alive and not p2_alive:
        print("Result: Player 1 Wins!")
    elif not p1_alive and p2_alive:
        print("Result: Player 2 Wins!")
    else:
        print("Result: Draw!")

    p1.kill()
    p2.kill()

if __name__ == "__main__":
    main()