# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    dbus-x11 \
    xterm \
    firefox-esr \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libgconf-2-4 \
    libgtk-3-0 \
    libnss3 \
    libxss1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs pids chrome_data /tmp/.X11-unix

# Set display environment
ENV DISPLAY=:99
ENV XAUTHORITY=/tmp/.Xauthority

# Expose ports
EXPOSE 5173 8000 8080 5900 9222

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Start Xvfb\n\
Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset &\n\
XVFB_PID=$!\n\
\n\
# Set display\nexport DISPLAY=:99\n\
\n\
# Start VNC server\n\
x11vnc -display :99 -rfbport 5900 -forever -shared &\n\
VNC_PID=$!\n\
\n\
# Start Chrome in background\n\
google-chrome --headless --remote-debugging-port=9222 --no-sandbox --disable-gpu --disable-web-security &\n\
CHROME_PID=$!\n\
\n\
# Start fluxbox\n\
fluxbox &\n\
\n\
# Start main application\n\
python run.py\n\
\n\
# Cleanup\n\
kill $XVFB_PID $VNC_PID $CHROME_PID 2>/dev/null || true\n\
wait' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]