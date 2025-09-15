# client/api/server.py
import os
import sys
import json
import uuid
import threading
from flask import Flask, request, jsonify, render_template # type: ignore

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from engine.match_runner import run_docker_match

app = Flask(__name__, template_folder='../ui/templates', static_folder='../ui/static')

# A simple in-memory dictionary to store the results of finished matches
match_results = {}

def run_match_in_background(match_id, bot_path, language, opponent_image):
    """The function that will run in a separate thread."""
    result_json_str = run_docker_match(bot_path, language, opponent_image)
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
    language = data.get('language')
    bot_path = data.get('bot_path')
    
    if not language or not bot_path:
        return jsonify({"error": "Missing 'language' or 'bot_path'"}), 400

    match_id = str(uuid.uuid4())
    opponent_image = "competition/random-bot"
    
    # Set initial status
    match_results[match_id] = {"status": "running"}

    # Start the long-running task in a background thread
    thread = threading.Thread(
        target=run_match_in_background,
        args=(match_id, bot_path, language, opponent_image)
    )
    thread.daemon = True
    thread.start()

    # Return immediately with the match ID
    return jsonify({"status": "started", "match_id": match_id})

@app.route('/match-status/<match_id>', methods=['GET'])
def get_match_status(match_id):
    """Endpoint for the frontend to poll for results."""
    result = match_results.get(match_id, {"status": "not_found"})
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)