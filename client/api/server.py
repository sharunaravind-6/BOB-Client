# client/api/server.py
import base64
import os
import sys
import json
import uuid
import threading
import requests
import config
from flask import Flask, request, jsonify, render_template # type: ignore

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from engine.match_runner import run_docker_match

app = Flask(__name__, template_folder='../ui/templates', static_folder='../ui/static')

# A simple in-memory dictionary to store the results of finished matches
match_results = {}

CPU_BOTS = {
    "cpu_easy": "competition/random-bot",
    "cpu_medium": "competition/space-filler-bot",
    # When you add a new CPU bot, you'll just add a line here.
    # "cpu_medium": "competition/greedy-bot", 
}

def run_match_in_background(match_id, p1_path, p2_path, opponent_selection):
    """The function that will run in a separate thread."""

    # --- Player 1 Setup ---
    p1_dir = os.path.dirname(p1_path)
    p1_filename = os.path.basename(p1_path)
    _, p1_ext = os.path.splitext(p1_filename)
    p1_lang = {".py": "python", ".java": "java"}.get(p1_ext)

    if not p1_lang:
        match_results[match_id] = {"status": "error", "log": {"error": f"P1: Unsupported file type: {p1_ext}"}}
        return

    # --- Player 2 Setup ---
    cpu_bot_name = CPU_BOTS.get(opponent_selection) # Look up the image name
    p2_dir, p2_filename, p2_lang = None, None, None

    if not cpu_bot_name: # If it's not a CPU bot, it must be a human/local bot
        if not p2_path or "No file selected" in p2_path:
            match_results[match_id] = {"status": "error", "log": {"error": "P2: No bot file selected for Player 2."}}
            return

        p2_dir = os.path.dirname(p2_path)
        p2_filename = os.path.basename(p2_path)
        _, p2_ext = os.path.splitext(p2_filename)
        p2_lang = {".py": "python", ".java": "java"}.get(p2_ext)
        if not p2_lang:
            match_results[match_id] = {"status": "error", "log": {"error": f"P2: Unsupported file type: {p2_ext}"}}
            return

    # Call the match runner with all the prepared info
    result_json_str = run_docker_match(
        p1_dir, p1_filename, p1_lang,
        p2_dir, p2_filename, p2_lang,
        cpu_bot_name
    )

    try:
        game_log = json.loads(result_json_str)
        match_results[match_id] = {"status": "complete", "log": game_log}
    except json.JSONDecodeError:
        error_log = {"error": "Failed to parse game log", "raw_output": result_json_str}
        match_results[match_id] = {"status": "error", "log": error_log}



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-match', methods=['POST'])
def handle_run_match():
    data = request.get_json()
    p1_path = data.get('p1_path')
    p2_path = data.get('p2_path')
    opponent_selection = data.get('opponent_selection')


    # New, smarter validation
    if not p1_path or "No file selected" in p1_path:
        return jsonify({"error": "Missing bot file for Player 1"}), 400
    
    if opponent_selection == "human" and (not p2_path or "No file selected" in p2_path):
        return jsonify({"error": "Missing bot file for Player 2"}), 400


    match_id = str(uuid.uuid4())
    match_results[match_id] = {"status": "running"}

    thread = threading.Thread(
        target=run_match_in_background,
        args=(match_id, p1_path, p2_path, data.get('opponent_selection'))
    )
    thread.daemon = True
    thread.start()
    return jsonify({"status": "started", "match_id": match_id})

@app.route('/match-status/<match_id>', methods=['GET'])
def get_match_status(match_id):
    """Endpoint for the frontend to poll for results."""
    result = match_results.get(match_id, {"status": "not_found"})
    return jsonify(result)

@app.route('/submit-to-server', methods=['POST'])
def forward_submission():
    """Receives data from our UI and forwards it to the main competition server."""
    data = request.get_json()

    team_name = data.get('team_name')
    password = data.get('password')
    zip_data_b64 = data.get('zip_data')

    if not all([team_name, password, zip_data_b64]):
        return jsonify({"error": "Missing data for submission."}), 400

    # The URL of your friend's server
    # COMPETITION_SERVER_URL = "http://FRIENDS_IP_ADDRESS:5000/submit"

    COMPETITION_SERVER_URL = config.COMPETITION_SERVER_URL


    # Decode the base64 string back into bytes
    zip_bytes = base64.b64decode(zip_data_b64)

    # Prepare the multipart/form-data payload
    form_payload = {
        'team_name': (None, team_name),
        'password': (None, password),
    }
    files_payload = {
        'bot_zip_file': ('bot.zip', zip_bytes, 'application/zip')
    }

    try:
        response = requests.post(COMPETITION_SERVER_URL, data=form_payload, files=files_payload, timeout=30)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to connect to competition server: {e}"}), 500
# if __name__ == '__main__':
#     app.run(debug=True, port=5000)