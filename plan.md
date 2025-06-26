### **1. Project Scaffolding & Environment Setup (First 30 Minutes)**

This initial phase focuses on getting the core environment ready. A solid foundation is crucial.

*   **1.1. Create the Project Structure:**
    *   Initialize a new Git repository.
    *   Create a clear directory structure:
        *   `/agent`: For the core agent logic (Python/TypeScript).
        *   `/api`: For the web server exposing control endpoints.
        *   `/docker`: To house the Dockerfile and related scripts.
        *   `/tasks`: A directory to store scheduled task definitions and logs.
        *   `README.md`: To document the architecture and setup instructions.

*   **1.2. Build the Base Docker Image:**
    *   Create a `Dockerfile` in the `/docker` directory.
    *   **1.2.1. Choose a Base Image:** Start with a lightweight Linux distribution like `ubuntu:22.04`.
    *   **1.2.2. Install Core Dependencies:**
        *   System tools: `curl`, `git`, `sudo`, `vim`.
        *   Python/TypeScript runtimes: `python3`, `pip`, `nodejs`, `npm`.
        *   GUI and VNC tools: `xvfb`, `x11vnc`, `novnc`, `xfce4` (a lightweight desktop environment), and `xdotool`.
        *   Jupyter: `jupyterlab`.
    *   **1.2.3. Configure the Environment:**
        *   Set up a non-root user for better security.
        *   Create a startup script (`start.sh`) that will be the container's `ENTRYPOINT`. This script will launch `Xvfb`, `x11vnc`, and `Jupyter Lab` in the background.

*   **1.3. Validate the Docker Environment:**
    *   Build the Docker image: `docker build -t coding-agent .`
    *   Run the container, mapping the necessary ports (e.g., 8080 for noVNC, 8888 for Jupyter).
    *   Connect to the noVNC instance via a web browser to confirm the GUI desktop is running.
    *   Access Jupyter Lab to ensure it's operational.

### **2. Developing the Core Agent Logic (Next 60 Minutes)**

This is the heart of the challenge. Focus on modularity and secure execution.

*   **2.1. Design the `Agent` Class (in `/agent/agent.py`):**
    *   This class will manage the state and capabilities of a single task.
    *   **2.1.1. Initialization (`__init__`):**
        *   Accept a `task_id`.
        *   Initialize a dedicated working directory (e.g., `/tasks/{task_id}`).
        *   Set up logging to a file within its working directory (`/tasks/{task_id}/agent.log`).
        *   Initialize a simple file-based memory (`/tasks/{task_id}/memory.json`) to store context/history.
    *   **2.1.2. Implement Core Capabilities as Methods:**
        *   `run_shell(command: str)`: Executes a shell command using `subprocess.run`.
            *   **Security:** Run as the non-root user. Capture `stdout` and `stderr`. Implement a timeout to prevent long-running processes. Do not use `shell=True` with untrusted input.
        *   `run_python(code: str)`: Writes the code to a temporary file (`script.py`) and executes it using `python3 script.py`.
        *   `read_file(path: str)`: Reads the content of a file within the sandboxed working directory.
        *   `write_file(path: str, content: str)`: Writes content to a file.
        *   `simulate_gui_action(xdotool_command: str)`: Uses `subprocess` to execute `xdotool` commands. Ensure the `DISPLAY` environment variable is correctly set to point to the Xvfb server.

*   **2.2. Implement Task Execution Logic:**
    *   The agent needs a way to interpret a sequence of commands.
    *   **2.2.1. Task Definition:** Define a simple JSON structure for a task (e.g., `{"steps": [{"tool": "shell", "command": "ls -l"}, {"tool": "python", "code": "print('hello')"}]}`).
    *   **2.2.2. Create an Execution Loop:**
        *   A function `execute_task(task_definition)` will parse the JSON.
        *   It will iterate through the steps, calling the appropriate `Agent` method for each.
        *   Log the output of each step to the agent's log file.
        *   Update the task status (e.g., `running`, `completed`, `failed`) in a status file (`/tasks/{task_id}/status.json`).

### **3. Building the Control API (Next 30 Minutes)**

This component allows for interaction with the agent system.

*   **3.1. Set up a Simple Web Server (`/api/server.py`):**
    *   Use a lightweight framework like Flask or FastAPI.
    *   **3.1.1. Implement the `/schedule` Endpoint (POST):**
        *   Accepts a JSON payload containing the task definition.
        *   Generates a unique `task_id`.
        *   Creates the task directory structure (`/tasks/{task_id}`).
        *   Saves the task definition to `/tasks/{task_id}/task.json`.
        *   Initializes the status file: `{"status": "scheduled"}`.
        *   **Crucially:** This endpoint should not block. It should trigger the task execution asynchronously (e.g., by spawning a new process or, for this prototype, simply starting it in the background).
        *   Returns the `task_id` to the user.
    *   **3.1.2. Implement the `/status` Endpoint (GET):**
        *   Accepts a `task_id` as a query parameter (`/status?task_id=...`).
        *   Reads the status from `/tasks/{task_id}/status.json`.
        *   Optionally, it can also return the path to the log file for more detailed inspection.

*   **3.2. Integrate the API into the Docker Container:**
    *   Modify the `start.sh` script to launch the API server alongside the other services.

### **4. System Integration and Documentation (Final 30 Minutes)**

Bring everything together and explain your work.

*   **4.1. Firecracker Integration (Conceptual):**
    *   Since a full Firecracker implementation is complex for a 2-3 hour window, focus on the architectural explanation.
    *   **4.1.1. Update the `README.md`:** Create a new section called "Architecture" with a subsection for "Scalability with Firecracker."
    *   **4.1.2. Explain the Design:**
        *   The `/schedule` endpoint would not run the task directly. Instead, it would use the Firecracker API to boot a new microVM.
        *   The microVM would be configured with a minimal kernel and a root filesystem containing our `coding-agent` Docker image (or just the necessary agent files).
        *   The task definition would be passed to the microVM upon startup.
        *   The microVM executes the task in complete isolation and then shuts down.
        *   Status updates would be pushed from the microVM to a central location (like an S3 bucket or a database) that the `/status` endpoint can query.
        *   This approach provides superior security and resource isolation compared to just using Docker containers.

*   **4.2. Bonus: Kubernetes/Nomad (Conceptual):**
    *   In the `README.md`, add another subsection for "Horizontal Scalability with Kubernetes."
    *   **4.2.1. Explain the Design:**
        *   The entire system (API server, agent containers) would be packaged as a Helm chart.
        *   The `/schedule` endpoint would create a Kubernetes `Job` for each task.
        *   The `Job` spec would define a pod running the `coding-agent` Docker image.
        *   The task definition would be passed to the pod via a `ConfigMap` or environment variables.
        *   Kubernetes handles the scheduling, execution, and resource management of these jobs across a cluster of nodes, providing horizontal scalability.
        *   Logs and artifacts could be persisted using Persistent Volumes.

*   **4.3. Finalize Documentation (`README.md`):**
    *   **Project Overview:** Briefly describe what the project is.
    *   **Architecture:** Include the diagrams/explanations for Docker, Firecracker, and Kubernetes.
    *   **Security Considerations:** Mention the steps taken (non-root user, `subprocess` best practices, sandboxed directories) and what future steps would be (e.g., stricter seccomp profiles, AppArmor).
    *   **How to Run:** Provide clear, concise instructions on how to build the Docker image and run the container.
    *   **API Usage:** Show `curl` examples for hitting the `/schedule` and `/status` endpoints.