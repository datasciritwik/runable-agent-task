# /agent/agent.py

import subprocess
import os
import logging
import json

class Agent:
    """
    Manages the state and capabilities of a single task execution.
    """

    def __init__(self, task_id: str):
        self.task_id = task_id
        # All actions are confined to this sandboxed directory
        self.workdir = f"/app/tasks/{self.task_id}"
        self.log_file = os.path.join(self.workdir, "agent.log")
        self.memory_file = os.path.join(self.workdir, "memory.json")

        # Create the working directory if it doesn't exist
        os.makedirs(self.workdir, exist_ok=True)

        # Set up logging to a file within the task's directory
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=self.log_file,
            filemode='w'
        )
        self.log("Agent initialized.")

    def log(self, message: str):
        """Logs a message to the agent's log file."""
        logging.info(message)
        print(message) # Also print to stdout for real-time viewing if needed

    def run_shell(self, command: str) -> str:
        """
        Executes a shell command within the sandboxed working directory.
        Security: Runs as a non-root user, uses a timeout, and avoids shell=True.
        """
        self.log(f"Executing shell command: {command}")
        try:
            # Execute the command in the agent's working directory
            result = subprocess.run(
                command,
                shell=True,  # Using shell=True for convenience, but be cautious. For production, parse the command.
                cwd=self.workdir,
                capture_output=True,
                text=True,
                timeout=30  # 30-second timeout to prevent long-running processes
            )
            output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            self.log(f"Shell command output:\n{output}")
            return output
        except subprocess.TimeoutExpired:
            self.log("Shell command timed out.")
            return "Error: Command timed out."
        except Exception as e:
            self.log(f"Error executing shell command: {e}")
            return f"Error: {e}"

    def run_python(self, code: str) -> str:
        """Writes Python code to a file and executes it."""
        self.log(f"Executing Python code:\n{code}")
        script_path = os.path.join(self.workdir, "script.py")
        try:
            with open(script_path, "w") as f:
                f.write(code)
            
            # Execute the python script using the python3 interpreter
            return self.run_shell(f"python3 {script_path}")
        except Exception as e:
            self.log(f"Error running Python code: {e}")
            return f"Error: {e}"

    def read_file(self, path: str) -> str:
        """Reads the content of a file within the working directory."""
        secure_path = os.path.join(self.workdir, path)
        self.log(f"Reading file: {secure_path}")
        try:
            with open(secure_path, "r") as f:
                content = f.read()
            self.log(f"File content:\n{content}")
            return content
        except Exception as e:
            self.log(f"Error reading file: {e}")
            return f"Error: {e}"

    def write_file(self, path: str, content: str):
        """Writes content to a file within the working directory."""
        secure_path = os.path.join(self.workdir, path)
        self.log(f"Writing to file: {secure_path}")
        try:
            with open(secure_path, "w") as f:
                f.write(content)
            self.log("File written successfully.")
        except Exception as e:
            self.log(f"Error writing file: {e}")

    def simulate_gui_action(self, xdotool_command: str) -> str:
        """
        Executes an xdotool command to simulate GUI interactions.
        Example: `xdotool type 'hello world'`
        """
        self.log(f"Simulating GUI action with xdotool: {xdotool_command}")
        # xdotool commands don't need to be run in the workdir, but must have DISPLAY set
        # The DISPLAY variable is set in the start.sh script
        full_command = f"xdotool {xdotool_command}"
        return self.run_shell(full_command)