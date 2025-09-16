# client/engine/match_runner.py
import docker # type: ignore
import os
import sys
import subprocess
import json

def get_base_image_for_language(language):
    """Maps a language to its corresponding Docker base image."""
    lang_map = {
        # "python": "python:3.11-slim",  # We can use the official python image directly
        "python" : "competition/base-python",
        "java" : "competition/base-java"
        # Add more languages here later, e.g., "javascript": "node:18-slim"
    }
    return lang_map.get(language.lower())

def run_docker_match(p1_dir, p1_filename, p1_lang, p2_dir, p2_filename, p2_lang, cpu_bot_name):
    """
    Runs a Tron match between two opponents, who can be user bots or a CPU.
    """
    client = docker.from_env()
    
    # Create a Docker network if it doesn't exist
    network_name = "tron-battle"
    try:
        client.networks.get(network_name)
    except docker.errors.NotFound:
        client.networks.create(network_name, driver="bridge")

    user_container = None
    opponent_container = None
    result = "Referee Error"

    try:
        # --- 1. Player 1 Setup (always a user bot) ---
        p1_base_image = get_base_image_for_language(p1_lang)
        if not p1_base_image:
            return json.dumps({"error": f"P1: Language '{p1_lang}' not supported."})

        print(f"INFO: Starting P1 container from '{p1_base_image}'...")
        user_container = client.containers.run(
            image=p1_base_image,
            detach=True,
            network=network_name,
            volumes={os.path.abspath(p1_dir): {'bind': '/app', 'mode': 'rw'}},
            working_dir='/app',
            tty=True # Keeps container alive
        )
        # bot1_cmd = f"docker exec -i {user_container.id} ./run.sh {p1_filename}"
        bot1_cmd = f"docker exec -i {user_container.id} run_bot.sh {p1_filename}"

        # --- 2. Player 2 Setup (can be CPU or another user bot) ---
        if cpu_bot_name:
            # --- Scenario: Player vs. CPU ---
            print(f"INFO: Starting P2 (CPU) container from '{cpu_bot_name}'...")
            opponent_container = client.containers.run(
                cpu_bot_name, 
                detach=True, 
                network=network_name,
                tty=True
            )
            # The CPU bot's filename is always bot.py inside its image
            # bot2_cmd = f"docker exec -i {opponent_container.id} ./run.sh bot.py"
            bot2_cmd = f"docker exec -i {opponent_container.id} run_bot.sh bot.py"
        else:
            # --- Scenario: Player vs. Player ---
            p2_base_image = get_base_image_for_language(p2_lang)
            if not p2_base_image:
                return json.dumps({"error": f"P2: Language '{p2_lang}' not supported."})

            print(f"INFO: Starting P2 container from '{p2_base_image}'...")
            opponent_container = client.containers.run(
                image=p2_base_image,
                detach=True,
                network=network_name,
                volumes={os.path.abspath(p2_dir): {'bind': '/app', 'mode': 'rw'}},
                working_dir='/app',
                tty=True
            )
            # bot2_cmd = f"docker exec -i {opponent_container.id} ./run.sh {p2_filename}"
            bot2_cmd = f"docker exec -i {opponent_container.id} run_bot.sh {p2_filename}"

        # --- 3. Run the Referee on the Host ---
        print("INFO: Starting referee...")
        referee_process = subprocess.run(
            [sys.executable, "-m", "client.engine.referee", bot1_cmd, bot2_cmd],
            capture_output=True, text=True
        )
        result = referee_process.stdout.strip()
        if referee_process.stderr:
            print("REFEREE STDERR:", referee_process.stderr)


    except Exception as e:
        print(f"AN ERROR OCCURRED: {e}")
        result = f"Error: {e}"
    finally:
        # --- 4. Cleanup ---
        print("INFO: Cleaning up containers...")
        if user_container:
            user_container.stop()
            user_container.remove()
        if opponent_container:
            opponent_container.stop()
            opponent_container.remove()
        print("INFO: Match finished.")
        
    return result

if __name__ == '__main__':
    # Updated to simulate the frontend providing language and code path
    import subprocess
    if len(sys.argv) < 3:
        print("Usage: python -m client.engine.match_runner <language> <path_to_user_bot_dir>")
        sys.exit(1)
    
    user_lang = sys.argv[1] # e.g., "java" or "python"
    user_bot_dir = sys.argv[2]
    opponent_img = "competition/random-bot" # This bot is written in python
    
    match_result = run_docker_match(user_bot_dir, user_lang, opponent_img)
    print("\n--- FINAL MATCH RESULT ---")
    print(match_result)