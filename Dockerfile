# Railway-optimized Dockerfile with reverse proxy
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=8000

# Install dependencies including nginx
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    nodejs \
    npm \
    xvfb \
    x11vnc \
    websockify \
    xdotool \
    fluxbox \
    nginx \
    supervisor \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install noVNC
RUN git clone https://github.com/novnc/noVNC.git /opt/novnc && \
    git clone https://github.com/novnc/websockify /opt/novnc/utils/websockify

# Create non-root user
RUN useradd -m -s /bin/bash agent && \
    usermod -aG sudo agent

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt jupyterlab Flask flask-cors

# Copy application code
COPY --chown=agent:agent . .

# Create necessary directories
RUN mkdir -p /app/tasks /var/log/supervisor && \
    chown -R agent:agent /app/tasks

# Configure Nginx as reverse proxy
COPY nginx.conf /etc/nginx/nginx.conf

# Configure Supervisor to manage all services
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Switch to non-root user for application files
USER agent

USER root

# Expose the main port (Railway will use this)
EXPOSE $PORT

# Start supervisor to manage all services
# CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
# ENTRYPOINT ["/app/docker/start.sh"]
# COPY nginx.conf.template /etc/nginx/nginx.conf.template

CMD envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && \
    /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

