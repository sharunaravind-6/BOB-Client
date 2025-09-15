# run_local_test.py
import subprocess
import sys

def run_test():
    """Runs a local match between two bots and prints the result."""
    print("--- Starting Local Tron Match ---")
    
    bot1_path = "bots/random_bot/run.sh"
    bot2_path = "bots/random_bot/run.sh" 

    # --- THIS IS THE FIX ---
    # Instead of running the file directly, we run it as a module (-m)
    # This allows the relative imports (like ".game") to work correctly.
    referee_command = [
        sys.executable,
        "-m", "client.engine.referee", # Changed from "client/engine/referee.py"
        bot1_path,
        bot2_path
    ]
    
    try:
        process = subprocess.run(referee_command, capture_output=True, text=True, check=True, timeout=10)
        print("--- Match Finished ---")
        print(process.stdout.strip())
        if process.stderr:
            print("Errors:\n", process.stderr)

    except subprocess.CalledProcessError as e:
        print("--- Match Failed to Run ---")
        print("Return Code:", e.returncode)
        print("Output:\n", e.stdout)
        print("Error Output:\n", e.stderr)
    except subprocess.TimeoutExpired:
        print("--- Match Timed Out ---")
        print("The game took longer than 10 seconds and was terminated.")
    except FileNotFoundError:
        print("Error: Could not find the python interpreter. Make sure you are in the ClientApp directory.")

if __name__ == "__main__":
    run_test()