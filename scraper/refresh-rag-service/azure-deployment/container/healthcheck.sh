#!/bin/bash
# Health check script for Docker container

# Check if health endpoint responds
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health || echo "000")

if [ "$response" = "200" ]; then
    exit 0
else
    echo "Health check failed with response code: $response"
    exit 1
fi