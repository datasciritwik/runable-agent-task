# 1.2.1: Choose a Base Image
FROM ubuntu:22.04

# Set environment variable to allow installations without prompts
ENV DEBIAN_FRONTEND=noninteractive

# 1.2.2: Install Core Dependencies
RUN apt-get update && apt-get install -y \
    # System Tools
    curl \
    git \
    sudo \
    vim \
    # Python/NodeJS Runtimes
    python3 \
    python3-pip \
    nodejs \
    npm \
    # GUI and VNC Tools
    xvfb \
    x11vnc \
    novnc \
    websockify \
    xfce4 \
    xdotool \
    --no-install-recommends && \
    # Clean up apt cache
    rm -rf /var/lib/apt/lists/*

# Install Jupyter
RUN pip3 install jupyterlab

# 1.2.3: Configure the Environment
# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash --groups sudo agentuser
# Allow the user to run sudo commands without a password
RUN echo "agentuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set up the application directory
WORKDIR /app

# Copy all your project files into the container's /app directory
# This includes /agent, /api, etc.
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Grant ownership of the app directory to the new user
RUN chown -R agentuser:agentuser /app

# Switch to the non-root user
USER agentuser

# Expose the ports for the API, noVNC, and Jupyter
EXPOSE 8000 8080 8888

# Define the entrypoint script that will start all services
ENTRYPOINT ["/app/docker/start.sh"]