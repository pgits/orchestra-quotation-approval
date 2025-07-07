FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome - Multi-architecture support
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
        echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
        apt-get update && \
        apt-get install -y google-chrome-stable; \
    else \
        # For ARM64 (like M1/M2 Macs), install Chromium instead
        apt-get update && \
        apt-get install -y chromium chromium-driver; \
    fi && \
    rm -rf /var/lib/apt/lists/*

# Install ChromeDriver for amd64 or use chromium-driver for arm64
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
        wget -N http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
        unzip chromedriver_linux64.zip && \
        rm chromedriver_linux64.zip && \
        mv chromedriver /usr/local/bin/chromedriver && \
        chmod +x /usr/local/bin/chromedriver; \
    else \
        # For ARM64, chromium-driver is already installed, create symlink
        ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver || \
        ln -sf /usr/bin/chromium-driver /usr/local/bin/chromedriver; \
    fi

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-minimal.txt

# Copy application code
COPY src/ ./src/
COPY copilot/ ./copilot/

# Create necessary directories
RUN mkdir -p /tmp/staging

# Set environment variables
ENV PYTHONPATH=/app
ENV DISPLAY=:99

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run the scraper
CMD ["python", "-m", "src.scraper.main"]