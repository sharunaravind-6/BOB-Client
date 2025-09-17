# config.py
# This file holds all the configurable settings for the Tron game.

# Board dimensions
BOARD_WIDTH = 30
BOARD_HEIGHT = 20

# Time limit for a bot to make a single move, in milliseconds
TIME_LIMIT_MS = 200

FIRST_MOVE_TIME_LIMIT_MS = 4000 # 3 seconds

# The maximum number of turns a game can last before it's declared a draw
MAX_TURNS = 500

# COMPETITION_SERVER_URL = "http://FRIENDS_IP_ADDRESS:5000/submit"

COMPETITION_SERVER_URL = "http://127.0.0.1:5000/submit"
