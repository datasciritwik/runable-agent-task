#!/bin/bash
set -e

# Set the display environment variable for GUI applications
export DISPLAY=:1

# Start Xvfb (the virtual display) in the background
# The -screen option sets the resolution and color depth
Xvfb :1 -screen 0 1024x768x16 &

# Start the window manager (XFCE) in the background
startxfce4 &

# Start the VNC server, connecting it to our virtual display
# -forever keeps it running
x11vnc -display :1 -forever &

# Start noVNC, which provides the web interface to the VNC server
# It listens on port 8080 and forwards to the VNC port (5900)
/usr/share/novnc/utils/launch.sh --listen 8080 --vnc localhost:5900 &

# Start Jupyter Lab in the background
# --ip=0.0.0.0 makes it accessible from outside the container
# --allow-root is needed because of how Docker environments work
# We disable the token for easy access in this prototype
jupyter lab --port=8888 --ip=0.0.0.0 --allow-root --NotebookApp.token='' --NotebookApp.password='' &

# Start the API Server (we will create this in Step 3)
# This will be the main process that keeps the container running.
echo "Starting API server on port 8000..."
# Use gunicorn for production
exec gunicorn --bind 0.0.0.0:8000 --chdir /app/api server:app