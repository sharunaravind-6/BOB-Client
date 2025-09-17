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

# config.py

# ... (other constants like BOARD_WIDTH are here) ...

# Central dictionary for language definitions
LANGUAGES = {
    "python": {
        "extension": ".py",
        "base_image": "competition/base-python",
        "script_path": "scripts/python.sh"
    },
    "java": {
        "extension": ".java",
        "base_image": "competition/base-java",
        "script_path": "scripts/java.sh"
    },
    # To add a new language, you'll just add a new entry here
}