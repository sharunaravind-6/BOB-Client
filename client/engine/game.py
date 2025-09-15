# client/engine/game.py
from collections import deque

class Snake:
    """Represents a snake in the Tron game."""
    def __init__(self, id, start_pos, start_dir):
        self.id = id
        self.body = deque([start_pos])
        self.direction = start_dir  # e.g., (0, 1) for DOWN
        self.is_alive = True
        self.length = 1

    @property
    def head(self):
        return self.body[0]

    def move(self, move_str):
        # Prevent moving directly backward
        if move_str == "UP" and self.direction == (0, 1): return
        if move_str == "DOWN" and self.direction == (0, -1): return
        if move_str == "LEFT" and self.direction == (1, 0): return
        if move_str == "RIGHT" and self.direction == (-1, 0): return

        move_map = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
        if move_str in move_map:
            self.direction = move_map[move_str]

        new_head = (self.head[0] + self.direction[0], self.head[1] + self.direction[1])
        self.body.appendleft(new_head)
        # In Tron, snakes don't shrink, they just leave a trail.
        # We don't pop the tail.
        self.length += 1

class Board:
    """Manages the game board and collision detection."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # 0: empty, 1: player 1, 2: player 2
        self.grid = [[0 for _ in range(height)] for _ in range(width)]

    # def update(self, snakes):
    #     for snake in snakes:
    #         if snake.is_alive:
    #             head_x, head_y = snake.head
    #             # Wall collision
    #             if not (0 <= head_x < self.width and 0 <= head_y < self.height):
    #                 snake.is_alive = False
    #                 continue
    #             # Self collision (check all but the new head)
    #             if snake.head in list(snake.body)[1:]:
    #                 snake.is_alive = False
    #                 continue

    #     # Opponent collision
    #     if snakes[0].is_alive and snakes[1].is_alive:
    #         if snakes[0].head == snakes[1].head: # Head-on collision
    #             snakes[0].is_alive = False
    #             snakes[1].is_alive = False
    #         else:
    #             if snakes[0].head in list(snakes[1].body):
    #                 snakes[0].is_alive = False
    #             if snakes[1].head in list(snakes[0].body):
    #                 snakes[1].is_alive = False

    #     # Update grid with new snake positions for the next turn's state
    #     self.grid = [[0 for _ in range(self.height)] for _ in range(self.width)]
    #     for i, snake in enumerate(snakes, 1):
    #         for part in snake.body:
    #             if 0 <= part[0] < self.width and 0 <= part[1] < self.height:
    #                 self.grid[part[0]][part[1]] = i
    # # Add this new method to the Board class in game.py

    # Replace the old update method in the Board class with this one
    def update(self, snakes):
        """
        Now only checks for the special case of a head-on collision,
        as other collisions are checked by the referee beforehand.
        """
        if snakes[0].is_alive and snakes[1].is_alive:
            if snakes[0].head == snakes[1].head: # Head-on collision
                snakes[0].is_alive = False
                snakes[1].is_alive = False

    def is_fatal_move(self, snake, opponent):
        """
        Checks if a snake's next move will result in death.
        """
        # Calculate the hypothetical next position of the head
        next_head = (snake.head[0] + snake.direction[0], snake.head[1] + snake.direction[1])

        # 1. Wall collision check
        if not (0 <= next_head[0] < self.width and 0 <= next_head[1] < self.height):
            return True
        # 2. Self collision check
        if next_head in list(snake.body):
            return True
        # 3. Opponent body collision check
        if next_head in list(opponent.body):
            return True

        return False