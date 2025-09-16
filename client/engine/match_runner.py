# client/engine/match_runner.py
import docker # type: ignore
import os
import sys
import subprocess
import json

def get_base_image_for_language(language):
    """Maps a language to its corresponding Docker base image."""
    lang_map = {
        "python": "python:3.11-slim",  # We can use the official python image directly
        "java": "competition/base-java"
        # Add more languages here later, e.g., "javascript": "node:18-slim"
    }
    return lang_map.get(language.lower())

def run_docker_match(user_bot_path, user_language, opponent_image_name):
    """
    Runs a Tron match inside Docker containers by mounting user code.
    """
    client = docker.from_env()
    
    user_base_image = get_base_image_for_language(user_language)
    if not user_base_image:
        return f"Error: Language '{user_language}' is not supported."
    
    print(f"INFO: Preparing match: {user_language.capitalize()} Bot vs {opponent_image_name}")

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
        # --- 1. Start user container from base image, mounting their code ---
        print(f"INFO: Starting user container from '{user_base_image}'...")
        user_container = client.containers.run(
            image=user_base_image,
            detach=True,
            network=network_name,
            volumes={os.path.abspath(user_bot_path): {'bind': '/app', 'mode': 'rw'}},
            working_dir='/app',
            tty=True # Keeps container alive
        )

        # --- 2. Start opponent container ---
        print(f"INFO: Starting opponent container from '{opponent_image_name}'...")
        opponent_container = client.containers.run(
            opponent_image_name, 
            detach=True, 
            network=network_name,
            tty=True
        )

        # --- 3. Run the Referee on the Host ---
        print("INFO: Starting referee...")
        bot1_cmd = f"docker exec -i {user_container.id} ./run.sh"
        bot2_cmd = f"docker exec -i {opponent_container.id} ./run.sh"

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
        # print("INFO: Capturing container logs and cleaning up...")
        # user_logs = ""
        # opponent_logs = ""
        # # Get logs before we stop the containers
        # if user_container:
        #     user_logs = user_container.logs().decode('utf-8', errors='ignore')
        # if opponent_container:
        #     opponent_logs = opponent_container.logs().decode('utf-8', errors='ignore')

        # # Now stop and remove the containers
        # if user_container:
        #     user_container.stop()
        #     user_container.remove()
        # if opponent_container:
        #     opponent_container.stop()
        #     opponent_container.remove()

        # # Now, add the captured logs to the final result
        # try:
        #     # Parse the JSON log we got from the referee
        #     log_data = json.loads(result)
        # except (json.JSONDecodeError, TypeError):
        #     # If referee failed, create a placeholder log
        #     log_data = {"result": {}, "frames": [], "error": result}

        # # Add the new, non-breaking debug_info section
        # log_data["debug_info"] = {
        #     "p1_stderr": user_logs,
        #     "p2_stderr": opponent_logs
        # }

        # # Convert the final object back to a JSON string to return
        # result = json.dumps(log_data)

        # print("INFO: Match finished.")



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