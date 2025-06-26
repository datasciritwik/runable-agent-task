# /api/server.py

from flask import Flask, request, jsonify
import uuid
import json
import os
from multiprocessing import Process
import sys

# Add the parent directory to the Python path to allow importing from 'agent'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.executor import execute_task

# Initialize the Flask application
app = Flask(__name__)

# Define the base directory for tasks
TASKS_DIR = "/app/tasks"

@app.route('/schedule', methods=['POST'])
def schedule_task():
    """
    Endpoint to schedule a new task.
    Accepts a JSON payload with task steps.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    task_definition = request.get_json()
    if 'steps' not in task_definition:
        return jsonify({"error": "Task definition must include 'steps'"}), 400

    # 1. Generate a unique ID for the task
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(TASKS_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    # 2. Save the task definition to a file
    task_file_path = os.path.join(task_dir, "task.json")
    with open(task_file_path, 'w') as f:
        json.dump(task_definition, f)

    # 3. Initialize the task status
    status_file_path = os.path.join(task_dir, "status.json")
    with open(status_file_path, 'w') as f:
        json.dump({"status": "scheduled"}, f)

    # 4. CRUCIAL: Start the task in a new, separate process
    # This ensures the API can return a response immediately without waiting
    # for the task to finish.
    process = Process(target=execute_task, args=(task_id,))
    process.start()

    print(f"Scheduled task {task_id} and started in process {process.pid}")

    # 5. Return the task ID to the user
    return jsonify({"message": "Task scheduled successfully", "task_id": task_id}), 202

@app.route('/status', methods=['GET'])
def get_status():
    """
    Endpoint to get the status of a task.
    Accepts a task_id as a query parameter.
    """
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"error": "task_id parameter is required"}), 400

    status_file_path = os.path.join(TASKS_DIR, task_id, "status.json")
    log_file_path = os.path.join(TASKS_DIR, task_id, "agent.log")

    if not os.path.exists(status_file_path):
        return jsonify({"error": "Task not found"}), 404

    try:
        with open(status_file_path, 'r') as f:
            status_data = json.load(f)
        
        response = {
            "task_id": task_id,
            "status": status_data.get("status"),
            "message": status_data.get("message"),
            "log_file": log_file_path
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Start the Flask server, making it accessible from outside the container
    app.run(host='0.0.0.0', port=8000)