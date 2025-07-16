#!/bin/bash

# Start mitmproxy script for 2FA authentication capture
echo "Starting mitmproxy for 2FA authentication capture..."
echo "Proxy server will be available on port 8080"
echo "Web interface will be available on port 8081"

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Start mitmweb for web interface
mitmweb \
    --web-host 0.0.0.0 \
    --web-port 8081 \
    --listen-port 8080 \
    --set confdir=/root/.mitmproxy \
    --set web_open_browser=false \
    --set flow_detail=3 \
    --set anticomp=true \
    --set stream_large_bodies=1m \
    --script /app/mitm_config.py \
    --verbose