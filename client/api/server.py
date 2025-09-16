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

def run_match_in_background(match_id, p1_path, p2_path, cpu_bot_name):
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
    p2_is_cpu = (p2_path == 'cpu')
    p2_dir, p2_filename, p2_lang = None, None, None
    if not p2_is_cpu:
        p2_dir = os.path.dirname(p2_path)
        p2_filename = os.path.basename(p2_path)
        _, p2_ext = os.path.splitext(p2_filename)
        p2_lang = {".py": "python", ".java": "java"}.get(p2_ext)
        if not p2_lang:
            match_results[match_id] = {"status": "error", "log": {"error": f"P2: Unsupported file type: {p2_ext}"}}
            return

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
    cpu_bot_name = data.get('cpu_bot_name')

    if not p1_path or not p2_path:
        return jsonify({"error": "Missing bot path for P1 or P2"}), 400

    match_id = str(uuid.uuid4())
    match_results[match_id] = {"status": "running"}

    thread = threading.Thread(
        target=run_match_in_background,
        args=(match_id, p1_path, p2_path, cpu_bot_name)
    )
    thread.daemon = True
    thread.start()
    return jsonify({"status": "started", "match_id": match_id})

@app.route('/match-status/<match_id>', methods=['GET'])
def get_match_status(match_id):
    """Endpoint for the frontend to poll for results."""
    result = match_results.get(match_id, {"status": "not_found"})
    return jsonify(result)

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)