# Azure Container for Copilot Studio Knowledge Refresh
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV DOTNET_ROOT=/opt/dotnet
ENV PATH="$PATH:/opt/dotnet:/opt/dotnet/tools"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    apt-transport-https \
    lsb-release \
    gnupg \
    python3 \
    python3-pip \
    python3-venv \
    inotify-tools \
    cron \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install .NET 8.0 Runtime (optional - for future CLI use)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg && \
    echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/microsoft.gpg] https://packages.microsoft.com/repos/microsoft-ubuntu-jammy-prod jammy main" > /etc/apt/sources.list.d/microsoft-prod.list && \
    apt-get update && \
    apt-get install -y dotnet-runtime-8.0 aspnetcore-runtime-8.0 dotnet-sdk-8.0 && \
    rm -rf /var/lib/apt/lists/*

# Note: Power Platform CLI installation skipped due to package issues
# Using direct REST API calls instead

# Create application directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY app/requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/config

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set up health check script
COPY healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh

# Expose health check port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/healthcheck.sh

# Use supervisor to manage multiple processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]