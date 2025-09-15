# bots/random_bot/bot.py
import sys
import json
import random

def main():
    """
    A simple bot that parses the game state and chooses a random, non-suicidal move.
    """
    for line in sys.stdin:
        state = json.loads(line)
        
        width = state["board"]["width"]
        height = state["board"]["height"]
        grid = state["board"]["grid"]
        head = state["you"]["head"]
        
        possible_moves = ["UP", "DOWN", "LEFT", "RIGHT"]
        safe_moves = []

        # Check each possible move
        for move in possible_moves:
            hx, hy = head["x"], head["y"]
            if move == "UP": hy -= 1
            if move == "DOWN": hy += 1
            if move == "LEFT": hx -= 1
            if move == "RIGHT": hx += 1
            
            # Check for wall collisions
            if not (0 <= hx < width and 0 <= hy < height):
                continue
            
            # Check for body collisions (self or opponent)
            if grid[hy][hx] != '0':
                continue
            
            safe_moves.append(move)

        # Choose a move
        if safe_moves:
            chosen_move = random.choice(safe_moves)
        else:
            # If no move is safe, just move anywhere and accept fate
            chosen_move = random.choice(possible_moves)

        # Send the move back to the game engine
        response = {"move": chosen_move}
        print(json.dumps(response))
        sys.stdout.flush()

if __name__ == "__main__":
    main()