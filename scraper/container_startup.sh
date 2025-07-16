#!/bin/bash

# Container startup script for TD SYNNEX scraper with 2FA support
set -euo pipefail

# Enable debugging
set -x

echo "🚀 Starting TD SYNNEX Scraper Container with 2FA Support"
echo "========================================================"

# Function to handle shutdown gracefully
cleanup() {
    echo "🛑 Shutting down services..."
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    if [ ! -z "$SCRAPER_PID" ]; then
        kill $SCRAPER_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Create logs directory
mkdir -p /app/logs

echo "🔧 Starting 2FA Verification API..."

# Check if required files exist
if [ ! -f "run_verification_api.py" ]; then
    echo "❌ run_verification_api.py not found"
    exit 1
fi

# Start the 2FA API server in background
python3 run_verification_api.py > /app/logs/2fa_api.log 2>&1 &
API_PID=$!

# Wait for API to start
sleep 3

# Check if API started successfully with retry
for i in {1..10}; do
    if ps -p $API_PID > /dev/null 2>&1; then
        # Wait for log file to contain startup message
        for j in {1..10}; do
            if [ -f "/app/logs/2fa_api.log" ] && grep -q "Running on" /app/logs/2fa_api.log; then
                PORT=$(grep "Running on http://127.0.0.1:" /app/logs/2fa_api.log | head -1 | sed 's/.*127.0.0.1:\([0-9]*\).*/\1/' || echo "5001")
                echo "✅ 2FA API started on port $PORT (PID: $API_PID)"
                echo "🌐 2FA API accessible at: http://container-ip:$PORT"
                echo ""
                echo "📧 When 2FA challenge appears, send verification code:"
                echo "curl -X POST http://container-ip:$PORT/2fa-challenge \\"
                echo "  -H 'Content-Type: application/json' \\"
                echo "  -d '{\"verificationId\": \"YOUR_CODE_HERE\"}'"
                echo ""
                break 2
            fi
            echo "Waiting for API to fully start... ($j/10)"
            sleep 2
        done
    fi
    echo "Checking API startup... ($i/10)"
    sleep 1
done

# Final check
if ! ps -p $API_PID > /dev/null 2>&1; then
    echo "❌ Failed to start 2FA API"
    echo "2FA API Log:"
    cat /app/logs/2fa_api.log || echo "No log file found"
    exit 1
fi

# Check if we should run in test mode or normal mode
if [ "$RUN_MODE" = "test" ]; then
    echo "🧪 Running in test mode - starting scraper with 2FA support..."
    python3 production_scraper_with_2fa.py > /app/logs/scraper.log 2>&1 &
    SCRAPER_PID=$!
    
    echo "✅ Scraper started in background (PID: $SCRAPER_PID)"
    echo "📊 Monitor scraper logs: docker exec <container> tail -f /app/logs/scraper.log"
    echo "📊 Monitor 2FA API logs: docker exec <container> tail -f /app/logs/2fa_api.log"
    
    # Wait for scraper to complete or keep container running
    wait $SCRAPER_PID
    
elif [ "$RUN_MODE" = "api-only" ]; then
    echo "🔌 Running in API-only mode - keeping 2FA API running..."
    echo "📊 Monitor logs: docker exec <container> tail -f /app/logs/2fa_api.log"
    
    # Keep container running with just the API
    wait $API_PID
    
else
    echo "🎯 Running in production mode..."
    
    # Check if credentials are available
    if [ -z "$TDSYNNEX_USERNAME" ] || [ -z "$TDSYNNEX_PASSWORD" ]; then
        echo "⚠️ TD SYNNEX credentials not found in environment variables"
        echo "Running in API-only mode for manual testing..."
        echo ""
        echo "To test 2FA functionality:"
        echo "1. Send test request to trigger 2FA listening"
        echo "2. Submit verification codes via API"
        echo ""
        wait $API_PID
    else
        echo "🔐 Found TD SYNNEX credentials, starting full scraper..."
        python3 production_scraper_with_2fa.py
    fi
fi

# Cleanup on exit
cleanup