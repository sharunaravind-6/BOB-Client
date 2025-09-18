# client/engine/match_runner.py
import os
import sys
import subprocess
import json

def get_script_for_language(language):
    """Maps a language to its corresponding Windows .bat script."""
    # This now points to our new Windows scripts
    script_map = {
        "python": "scripts_windows\\python.bat",
        "java": "scripts_windows\\java.bat",
        "c": "scripts_windows\\c.bat",
    }
    return script_map.get(language.lower())

def run_native_match(p1_dir, p1_filename, p1_lang, p2_dir, p2_filename, p2_lang, cpu_bot_name):
    """
    Runs a Tron match natively on the host OS without Docker.
    """
    result = "Referee Error"

    try:
        # --- 1. Player 1 Setup ---
        p1_script = get_script_for_language(p1_lang)
        if not p1_script:
            return json.dumps({"error": f"P1: Language '{p1_lang}' not supported."})
        # The command now directly calls the .bat script with the bot's file
        bot1_cmd = f"{p1_script} {os.path.join(p1_dir, p1_filename)}"
        
        # --- 2. Player 2 Setup ---
        if cpu_bot_name:
            # For the fallback, we'll assume the CPU is a Python bot
            p2_script = get_script_for_language("python")
            # We need the full path to the CPU bot's source file
            cpu_bot_path = os.path.abspath(f"bots/{cpu_bot_name.replace('competition/', '')}/bot.py")
            bot2_cmd = f"{p2_script} {cpu_bot_path}"
        else:
            p2_script = get_script_for_language(p2_lang)
            if not p2_script:
                return json.dumps({"error": f"P2: Language '{p2_lang}' not supported."})
            bot2_cmd = f"{p2_script} {os.path.join(p2_dir, p2_filename)}"

        # --- 3. Run the Referee ---
        print("INFO: Starting referee for a native match...")
        referee_process = subprocess.run(
            [sys.executable, "-m", "client.engine.referee", bot1_cmd, bot2_cmd],
            capture_output=True, text=True
        )
        result = referee_process.stdout.strip()
        if referee_process.stderr:
            print("REFEREE STDERR:", referee_process.stderr)

    except Exception as e:
        print(f"AN ERROR OCCURRED: {e}")
        result = json.dumps({"error": f"An unexpected error occurred: {e}"})

    return result