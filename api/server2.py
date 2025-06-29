#!/usr/bin/env python3
"""
Railway-compatible API server for the coding agent.
Runs on internal port 5000, proxied through Nginx on port 8000.
"""

import os
import json
import uuid
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Import your existing agent
from agent import Agent

app = Flask(__name__)
CORS(app)

# Run on internal port 5000 (proxied by Nginx)
INTERNAL_PORT = 5000

# Base directory for tasks
TASKS_DIR = Path('/app/tasks')
TASKS_DIR.mkdir(exist_ok=True)

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Coding Agent Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .service-links { margin-bottom: 20px; }
        .service-links a { 
            display: inline-block; 
            margin: 10px; 
            padding: 10px 20px; 
            background: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
        }
        .service-links a:hover { background: #0056b3; }
        .api-info { background: #f8f9fa; padding: 15px; border-radius: 5px; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>🤖 Coding Agent Dashboard</h1>
    
    <div class="service-links">
        <h2>Services</h2>
        <a href="/vnc/" target="_blank">🖥️ Virtual Desktop (noVNC)</a>
        <a href="/jupyter/" target="_blank">📓 Jupyter Lab</a>
    </div>

    <div class="api-info">
        <h2>API Usage</h2>
        <p>Schedule a task:</p>
        <pre>curl -X POST {{ base_url }}/schedule \\
-H "Content-Type: application/json" \\
-d '{
  "steps": [
    {
      "tool": "python",
      "code": "print(\\"Hello from Railway!\\")"
    }
  ]
}'</pre>

        <p>Check task status:</p>
        <pre>curl {{ base_url }}/status?task_id=YOUR_TASK_ID</pre>
    </div>

    <div class="api-info">
        <h2>Available Endpoints</h2>
        <ul>
            <li><strong>POST /schedule</strong> - Schedule a new task</li>
            <li><strong>GET /status</strong> - Get task status</li>
            <li><strong>GET /tasks</strong> - List all tasks</li>
            <li><strong>GET /logs/&lt;task_id&gt;</strong> - Get task logs</li>
        </ul>
    </div>
</body>
</html>
"""

def execute_task_async(task_id, task_definition):
    """Execute a task asynchronously in a separate thread."""
    task_dir = TASKS_DIR / task_id
    task_dir.mkdir(exist_ok=True)
    
    # Update status to running
    status_file = task_dir / 'status.json'
    with open(status_file, 'w') as f:
        json.dump({
            'status': 'running',
            'started_at': datetime.now().isoformat(),
            'task_id': task_id
        }, f)
    
    try:
        # Initialize agent for this task
        agent = Agent(str(task_dir))
        
        # Execute each step in the task
        results = []
        for step in task_definition.get('steps', []):
            tool = step.get('tool')
            
            if tool == 'shell':
                result = agent.run_shell(step.get('command', ''))
            elif tool == 'python':
                result = agent.run_python(step.get('code', ''))
            elif tool == 'typescript':
                # Save TypeScript code to file and run with node
                ts_file = task_dir / 'temp.js'
                with open(ts_file, 'w') as f:
                    f.write(step.get('code', ''))
                result = agent.run_shell(f'node {ts_file}')
            else:
                result = {'success': False, 'error': f'Unknown tool: {tool}'}
            
            results.append({
                'step': step,
                'result': result
            })
            
            # If a step fails and fail_fast is enabled, stop execution
            if not result.get('success', True) and task_definition.get('fail_fast', False):
                break
        
        # Update status to completed
        with open(status_file, 'w') as f:
            json.dump({
                'status': 'completed',
                'started_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat(),
                'task_id': task_id,
                'results': results
            }, f)
            
    except Exception as e:
        # Update status to failed
        with open(status_file, 'w') as f:
            json.dump({
                'status': 'failed',
                'started_at': datetime.now().isoformat(),
                'failed_at': datetime.now().isoformat(),
                'task_id': task_id,
                'error': str(e)
            }, f)

@app.route('/')
def dashboard():
    """Main dashboard showing service links and API usage."""
    base_url = request.host_url.rstrip('/')
    return render_template_string(DASHBOARD_HTML, base_url=base_url)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'coding-agent-api'})

@app.route('/schedule', methods=['POST'])
def schedule_task():
    """Schedule a new task for execution."""
    try:
        task_definition = request.get_json()
        
        if not task_definition or 'steps' not in task_definition:
            return jsonify({'error': 'Invalid task definition. Must include "steps" array.'}), 400
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())[:8]
        
        # Create task directory
        task_dir = TASKS_DIR / task_id
        task_dir.mkdir(exist_ok=True)
        
        # Save task definition
        with open(task_dir / 'task.json', 'w') as f:
            json.dump(task_definition, f, indent=2)
        
        # Initialize status
        with open(task_dir / 'status.json', 'w') as f:
            json.dump({
                'status': 'scheduled',
                'created_at': datetime.now().isoformat(),
                'task_id': task_id
            }, f)
        
        # Start task execution in background thread
        thread = threading.Thread(
            target=execute_task_async,
            args=(task_id, task_definition),
            daemon=True
        )
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'status': 'scheduled',
            'message': f'Task {task_id} has been scheduled for execution.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_task_status():
    """Get the status of a specific task."""
    task_id = request.args.get('task_id')
    
    if not task_id:
        return jsonify({'error': 'task_id parameter is required'}), 400
    
    task_dir = TASKS_DIR / task_id
    status_file = task_dir / 'status.json'
    
    if not status_file.exists():
        return jsonify({'error': f'Task {task_id} not found'}), 404
    
    try:
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        # Add log file path if it exists
        log_file = task_dir / 'agent.log'
        if log_file.exists():
            status['log_file'] = str(log_file)
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': f'Failed to read task status: {str(e)}'}), 500

@app.route('/tasks', methods=['GET'])
def list_tasks():
    """List all tasks."""
    try:
        tasks = []
        for task_dir in TASKS_DIR.iterdir():
            if task_dir.is_dir():
                status_file = task_dir / 'status.json'
                if status_file.exists():
                    with open(status_file, 'r') as f:
                        status = json.load(f)
                    tasks.append(status)
        
        # Sort by creation time (newest first)
        tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({'tasks': tasks})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logs/<task_id>', methods=['GET'])
def get_task_logs(task_id):
    """Get logs for a specific task."""
    task_dir = TASKS_DIR / task_id
    log_file = task_dir / 'agent.log'
    
    if not log_file.exists():
        return jsonify({'error': f'No logs found for task {task_id}'}), 404
    
    try:
        with open(log_file, 'r') as f:
            logs = f.read()
        
        return jsonify({'task_id': task_id, 'logs': logs})
        
    except Exception as e:
        return jsonify({'error': f'Failed to read logs: {str(e)}'}), 500

if __name__ == '__main__':
    print(f"Starting Coding Agent API server on internal port {INTERNAL_PORT}")
    print("This will be proxied through Nginx on the public port")
    
    # Run the Flask app on internal port
    app.run(host='0.0.0.0', port=INTERNAL_PORT, debug=False)