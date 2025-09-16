import sys
import json
import random
from collections import deque

# A value of 1.0 means the bot is completely deterministic (always picks the best).
# A value of 0.0 means it's a random non-suicidal bot.
# 0.8 means it will randomly choose from any move that leads to an area
# at least 80% as large as the best possible area.
RANDOMNESS_FACTOR = 0.8

def flood_fill(start_node, width, height, grid_str):
    """Calculates the size of a contiguous area of empty cells."""
    q = deque([start_node])
    visited = {start_node}
    count = 0
    while q:
        x, y = q.popleft()
        count += 1
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited and grid_str[ny][nx] == '0':
                visited.add((nx, ny))
                q.append((nx, ny))
    return count

def main():
    """
    A bot that calculates the available space for each possible move and
    chooses randomly from the best options.
    """
    for line in sys.stdin:
        state = json.loads(line)
        
        board = state["board"]
        width, height, grid = board["width"], board["height"], board["grid"]
        head = state["you"]["head"]
        hx, hy = head["x"], head["y"]
        
        moves = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
        safe_moves = {}

        # First, find all safe moves and calculate the area they lead to
        for move, (dx, dy) in moves.items():
            nx, ny = hx + dx, hy + dy
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == '0':
                area_size = flood_fill((nx, ny), width, height, grid)
                safe_moves[move] = area_size
        
        # Now, decide which move to make
        if safe_moves:
            # Find the size of the best possible area
            max_area = max(safe_moves.values())
            
            # Create a list of all moves that are "good enough" based on the randomness factor
            good_enough_moves = []
            for move, area in safe_moves.items():
                if area >= max_area * RANDOMNESS_FACTOR:
                    good_enough_moves.append(move)
            
            # Choose randomly from the list of good moves
            best_move = random.choice(good_enough_moves)
        else:
            best_move = "UP" # If trapped, just default to UP and accept fate

        response = {"move": best_move}
        print(json.dumps(response))
        sys.stdout.flush()

if __name__ == "__main__":
    main()