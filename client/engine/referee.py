# client/engine/referee.py
import sys
import json
import subprocess
import shlex
from .game import Snake, Board
import config
import threading
import time
import random


# --- Configurable Game Constants ---
BOARD_WIDTH = config.BOARD_WIDTH
BOARD_HEIGHT = config.BOARD_HEIGHT
TIME_LIMIT_MS = config.TIME_LIMIT_MS
FIRST_MOVE_TIME_LIMIT_MS = config.FIRST_MOVE_TIME_LIMIT_MS
MAX_TURNS = config.MAX_TURNS
# -----------------------------------

# ... (get_game_state and get_json_for_bot functions are unchanged) ...
# def get_game_state(turn, board, p1, p2):
#     return {
#         "turn": turn,
#         "board": { "width": board.width, "height": board.height },
#         "p1": { "id": "p1", "head": {"x": p1.head[0], "y": p1.head[1]}, "body": [{"x": pos[0], "y": pos[1]} for pos in p1.body], "direction": p1.direction, "alive": p1.is_alive },
#         "p2": { "id": "p2", "head": {"x": p2.head[0], "y": p2.head[1]}, "body": [{"x": pos[0], "y": pos[1]} for pos in p2.body], "direction": p2.direction, "alive": p2.is_alive }
#     }

def get_game_state(turn, board, p1, p2):
    # Create a grid representation for the log
    grid = [[0 for _ in range(board.height)] for _ in range(board.width)]
    for part in p1.body: grid[part[0]][part[1]] = 1
    for part in p2.body: grid[part[0]][part[1]] = 2
    grid_str = ["".join(map(str, [grid[x][y] for x in range(board.width)])) for y in range(board.height)]

    return {
        "turn": turn,
        "board": { 
            "width": board.width, 
            "height": board.height,
            "grid": grid_str  # The grid is now included
        },
        "p1": { "id": "p1", "head": {"x": p1.head[0], "y": p1.head[1]}, "body": [{"x": pos[0], "y": pos[1]} for pos in p1.body], "direction": p1.direction, "alive": p1.is_alive },
        "p2": { "id": "p2", "head": {"x": p2.head[0], "y": p2.head[1]}, "body": [{"x": pos[0], "y": pos[1]} for pos in p2.body], "direction": p2.direction, "alive": p2.is_alive }
    }

def get_json_for_bot(turn_state, player_key, opponent_key):
    you = turn_state[player_key]
    opponent = turn_state[opponent_key]
    grid = [[0 for _ in range(turn_state["board"]["height"])] for _ in range(turn_state["board"]["width"])]
    for part in you["body"]: grid[part["x"]][part["y"]] = 1
    for part in opponent["body"]: grid[part["x"]][part["y"]] = 2
    grid_str = ["".join(map(str, [grid[x][y] for x in range(turn_state["board"]["width"])])) for y in range(turn_state["board"]["height"])]
    board_for_bot = turn_state["board"].copy()
    board_for_bot["grid"] = grid_str
    bot_view = {
        "turn": turn_state["turn"],
        "board": board_for_bot,
        "you": { "id": player_key, "head": you["head"], "body": you["body"], "length": len(you["body"]) },
        "opponent": { "id": opponent_key, "head": opponent["head"], "body": opponent["body"], "length": len(opponent["body"]) },
    }
    return json.dumps(bot_view)

# Add this new function after get_json_for_bot in referee.py
def get_bot_response_with_timeout(bot_proc, json_data, timeout_ms):
    """
    Gets a bot's move with a strict time limit and returns detailed results.
    """
    result = {"move": None, "raw_output": "", "time_ms": 0, "error": None}
    
    def target():
        try:
            bot_proc.stdin.write(json_data + "\n")
            bot_proc.stdin.flush()
            line = bot_proc.stdout.readline().strip()
            result["raw_output"] = line
            if line:
                result["move"] = json.loads(line)["move"]
            else:
                result["error"] = "Bot exited or sent empty response."
        except (IOError, json.JSONDecodeError) as e:
            result["error"] = f"Invalid JSON or I/O Error: {e}"

    start_time = time.perf_counter()
    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=timeout_ms / 1000.0)
    end_time = time.perf_counter()
    result["time_ms"] = round((end_time - start_time) * 1000, 2)

    if thread.is_alive():
        result["error"] = f"Timeout: Move took longer than {timeout_ms}ms."
    
    return result

def generate_start_positions(width, height):
    """
    Generates symmetrically random start positions and directions for two snakes.
    """
    padding = 3 # How far from the edge the snakes can spawn
    
    # P1 spawns on the left half of the board
    p1_x = random.randint(padding, (width // 2) - padding)
    p1_y = random.randint(padding, height - 1 - padding)
    
    # P2 spawns in a symmetrically opposite position on the right half
    p2_x = width - 1 - p1_x
    p2_y = p1_y

    # Snakes always start facing each other
    p1_dir = (1, 0) # Right
    p2_dir = (-1, 0) # Left

    return (p1_x, p1_y), p1_dir, (p2_x, p2_y), p2_dir


def main():
    bot1_cmd_str, bot2_cmd_str = sys.argv[1], sys.argv[2]
    bot1_args, bot2_args = shlex.split(bot1_cmd_str), shlex.split(bot2_cmd_str)
    p1_proc = subprocess.Popen(bot1_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    p2_proc = subprocess.Popen(bot2_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    
    # snakes = [Snake("p1", (BOARD_WIDTH//4, BOARD_HEIGHT//2), (1,0)), Snake("p2", (BOARD_WIDTH*3//4, BOARD_HEIGHT//2), (-1,0))]
    
    p1_pos, p1_dir, p2_pos, p2_dir = generate_start_positions(BOARD_WIDTH, BOARD_HEIGHT)
    snakes = [Snake("p1", p1_pos, p1_dir), Snake("p2", p2_pos, p2_dir)]
    board = Board(BOARD_WIDTH, BOARD_HEIGHT)
    
    game_log = {"frames": [], "result": {}}
    turn = 0
    move_details_log = []
    
    # --- BUG FIX: Corrected Game Loop Logic ---
    # Log the initial state (Frame 0)
    game_log["frames"].append(get_game_state(turn, board, snakes[0], snakes[1]))

    while all(s.is_alive for s in snakes) and turn < MAX_TURNS:
        turn += 1
        current_state_for_bots = get_game_state(turn, board, snakes[0], snakes[1])
        # this code had no time limit so we are setting that and getting the time for each move the commented out code is the old block
        # p1_json = get_json_for_bot(current_state_for_bots, "p1", "p2")
        # p2_json = get_json_for_bot(current_state_for_bots, "p2", "p1")

        # p1_proc.stdin.write(p1_json + "\n"); p1_proc.stdin.flush()
        # p2_proc.stdin.write(p2_json + "\n"); p2_proc.stdin.flush()

        # try:
        #     p1_move = json.loads(p1_proc.stdout.readline().strip())["move"]
        #     p2_move = json.loads(p2_proc.stdout.readline().strip())["move"]
        # except (IOError, json.JSONDecodeError):
        #     snakes[0].is_alive = False; snakes[1].is_alive = False
        #     # Log the final state after the error
        #     game_log["frames"].append(get_game_state(turn, board, snakes[0], snakes[1]))
        #     break
        
        # # 1. Move the snakes
        # snakes[0].move(p1_move)
        # snakes[1].move(p2_move)

        # # 2. Log the state AFTER they move but BEFORE checking for death
        # game_log["frames"].append(get_game_state(turn, board, snakes[0], snakes[1]))

        # # 3. Now, check for collisions
        # board.update(snakes)

        # # If a snake died, the final state is already logged. We just need to update it
        # # with the 'alive: false' status for the next frame's info panel
        # if not all(s.is_alive for s in snakes):
        #      game_log["frames"].append(get_game_state(turn, board, snakes[0], snakes[1]))

        # 1. First, update each snake's intended direction based on its move.
        #    We do this before checking if the move is fatal.

        if turn == 1:
            timeout_for_this_turn = FIRST_MOVE_TIME_LIMIT_MS
        else:
            timeout_for_this_turn = TIME_LIMIT_MS

        p1_json = get_json_for_bot(current_state_for_bots, "p1", "p2")
        p1_response = get_bot_response_with_timeout(p1_proc, p1_json, timeout_for_this_turn)

        p2_json = get_json_for_bot(current_state_for_bots, "p2", "p1")
        p2_response = get_bot_response_with_timeout(p2_proc, p2_json, timeout_for_this_turn)

        p1_move, p2_move = p1_response["move"], p2_response["move"]

        # Record the detailed actions for this turn
        # move_details_log.append({
        #     "turn": turn,
        #     "board_state_for_this_turn": current_state_for_bots,
        #     "p1_response": p1_response,
        #     "p2_response": p2_response
        # })

        move_details_log.append({
            "turn": turn,
            "board_state": current_state_for_bots,
            "responses": {
                "p1": p1_response,
                "p2": p2_response
            }
        })


        # Disqualify bots that timed out or gave bad output (fairer penalty)
        if p1_response["error"]:
            snakes[0].is_alive = False
        if p2_response["error"]:
            snakes[1].is_alive = False

        # Also disqualify for invalid move strings
        if p1_move not in {"UP", "DOWN", "LEFT", "RIGHT"}:
            snakes[0].is_alive = False
        if p2_move not in {"UP", "DOWN", "LEFT", "RIGHT"}:
            snakes[1].is_alive = False

        if snakes[0].is_alive:
            # This is an example of strict move validation we can add later
            if p1_move in {"UP", "DOWN", "LEFT", "RIGHT"}:
                snakes[0].direction = {"UP":(0,-1), "DOWN":(0,1), "LEFT":(-1,0), "RIGHT":(1,0)}[p1_move]

        if snakes[1].is_alive:
            if p2_move in {"UP", "DOWN", "LEFT", "RIGHT"}:
                snakes[1].direction = {"UP":(0,-1), "DOWN":(0,1), "LEFT":(-1,0), "RIGHT":(1,0)}[p2_move]

        # 2. Now, use our new function to check if the move leads to death.
        #    This happens BEFORE the snake actually moves.
        if snakes[0].is_alive and board.is_fatal_move(snakes[0], snakes[1]):
            snakes[0].is_alive = False
        
        if snakes[1].is_alive and board.is_fatal_move(snakes[1], snakes[0]):
            snakes[1].is_alive = False

        # 3. Only move the snakes that are still alive after the checks.
        if snakes[0].is_alive:
            snakes[0].move(p1_move)
        
        if snakes[1].is_alive:
            snakes[1].move(p2_move)

        # 4. Do a final check for head-on collisions.
        board.update(snakes)

        # 5. Log the final state of this turn.
        game_log["frames"].append(get_game_state(turn, board, snakes[0], snakes[1]))
    # --- End of Loop ---

    p1_alive, p2_alive = snakes[0].is_alive, snakes[1].is_alive
    winner = "Draw"
    if p1_alive and not p2_alive: winner = "Player 1 Wins!"
    elif not p1_alive and p2_alive: winner = "Player 2 Wins!"
    elif turn >= MAX_TURNS: winner = "Draw (Max turns reached)"
    
    # old log files are commented out. the new ones are replaced
    game_log["result"] = {"winner": winner, "p1_length": snakes[0].length, "p2_length": snakes[1].length}
    game_log["debug_info"] = {"move_details": move_details_log}
    print(json.dumps(game_log))

    p1_proc.kill(); p2_proc.kill()


    # After winner determination, before printing
    # p1_stderr = p1_proc.stderr.read()
    # p2_stderr = p2_proc.stderr.read()
    
    # game_log["result"] = {"winner": winner, "p1_length": snakes[0].length, "p2_length": snakes[1].length}
    
    # # Add the new, non-breaking debug info section
    # game_log["debug_info"] = {
    #     "p1_stderr": p1_stderr,
    #     "p2_stderr": p2_stderr,
    #     "move_details": move_details_log
    # }

    # print(json.dumps(game_log, indent=2)) # Using indent for easier reading in console

    # p1_proc.kill(); p2_proc.kill()


if __name__ == "__main__":
    main()