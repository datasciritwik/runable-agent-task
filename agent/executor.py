# /agent/executor.py

import json
from agent import Agent # Imports the Agent class from agent.py
import os

def set_task_status(task_id: str, status: str, message: str = ""):
    """Updates the status of the task in a status.json file."""
    status_file = f"/app/tasks/{task_id}/status.json"
    os.makedirs(os.path.dirname(status_file), exist_ok=True)
    with open(status_file, "w") as f:
        json.dump({"status": status, "message": message}, f)

def execute_task(task_id: str):
    """
    Executes a task defined in a JSON file.
    """
    task_file = f"/app/tasks/{task_id}/task.json"
    
    try:
        # Update status to "running"
        set_task_status(task_id, "running", "Task execution started.")
        
        # Initialize the agent for this specific task
        agent = Agent(task_id)

        # Read the task definition
        with open(task_file, 'r') as f:
            task_definition = json.load(f)

        agent.log(f"Starting execution for task {task_id}")

        # Loop through each step in the task definition
        for step in task_definition['steps']:
            tool = step.get('tool')
            agent.log(f"Executing step with tool: {tool}")

            if tool == 'shell':
                agent.run_shell(step.get('command'))
            elif tool == 'python':
                agent.run_python(step.get('code'))
            elif tool == 'write_file':
                agent.write_file(step.get('path'), step.get('content'))
            elif tool == 'read_file':
                agent.read_file(step.get('path'))
            elif tool == 'simulate_gui':
                agent.simulate_gui_action(step.get('command'))
            else:
                agent.log(f"Unknown tool: {tool}")
        
        agent.log("Task execution completed successfully.")
        set_task_status(task_id, "completed", "Task finished successfully.")

    except Exception as e:
        print(f"Error executing task {task_id}: {e}")
        set_task_status(task_id, "failed", str(e))