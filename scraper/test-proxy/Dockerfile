FROM python:3.9-slim

# Install mitmproxy and dependencies
RUN pip install mitmproxy

# Create directory for certificates and logs
RUN mkdir -p /root/.mitmproxy /app/logs

# Copy configuration files
COPY mitm_config.py /app/
COPY start_proxy.sh /app/

# Make start script executable
RUN chmod +x /app/start_proxy.sh

# Expose ports
# 8080 - Proxy server
# 8081 - Web interface
EXPOSE 8080 8081

# Set working directory
WORKDIR /app

# Start mitmproxy with web interface
CMD ["./start_proxy.sh"]