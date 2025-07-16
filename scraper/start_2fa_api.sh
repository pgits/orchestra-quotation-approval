#!/bin/bash

# Start 2FA Verification API Server
# This script starts the server in the background and provides control commands

PID_FILE="/tmp/2fa_api.pid"
LOG_FILE="/tmp/2fa_api.log"

function start_api() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "API server is already running (PID: $PID)"
            echo "Use 'stop' to stop it first"
            return 1
        else
            echo "Removing stale PID file..."
            rm -f "$PID_FILE"
        fi
    fi
    
    echo "Starting 2FA Verification API server..."
    python3 run_verification_api.py > "$LOG_FILE" 2>&1 &
    API_PID=$!
    echo $API_PID > "$PID_FILE"
    
    sleep 2
    
    if ps -p $API_PID > /dev/null 2>&1; then
        echo "✅ API server started successfully (PID: $API_PID)"
        
        # Extract port from log file
        PORT=$(grep "Running on http://127.0.0.1:" "$LOG_FILE" | head -1 | sed 's/.*127.0.0.1:\([0-9]*\).*/\1/')
        if [ -n "$PORT" ]; then
            echo "🌐 Server is running on: http://localhost:$PORT"
            echo "📋 Available endpoints:"
            echo "  POST /2fa-challenge - Submit verification code"
            echo "  GET  /2fa-status    - Check listener status"
            echo "  GET  /health        - Health check"
            echo ""
            echo "📧 When 2FA challenge appears, send your verification code:"
            echo "curl -X POST http://localhost:$PORT/2fa-challenge \\"
            echo "  -H 'Content-Type: application/json' \\"
            echo "  -d '{\"verificationId\": \"YOUR_CODE_HERE\"}'"
        fi
        
        echo ""
        echo "📊 Monitor logs: tail -f $LOG_FILE"
        echo "🛑 Stop server: $0 stop"
        
    else
        echo "❌ Failed to start API server"
        echo "📋 Check logs: cat $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

function stop_api() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping API server (PID: $PID)..."
            kill $PID
            sleep 2
            
            if ps -p $PID > /dev/null 2>&1; then
                echo "Force killing API server..."
                kill -9 $PID
            fi
            
            rm -f "$PID_FILE"
            echo "✅ API server stopped"
        else
            echo "API server is not running"
            rm -f "$PID_FILE"
        fi
    else
        echo "API server is not running (no PID file found)"
    fi
}

function status_api() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ API server is running (PID: $PID)"
            
            # Try to get port from log
            PORT=$(grep "Running on http://127.0.0.1:" "$LOG_FILE" | head -1 | sed 's/.*127.0.0.1:\([0-9]*\).*/\1/')
            if [ -n "$PORT" ]; then
                echo "🌐 Server URL: http://localhost:$PORT"
                
                # Test health endpoint
                if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
                    echo "💚 Health check: PASS"
                else
                    echo "❤️ Health check: FAIL"
                fi
            fi
        else
            echo "❌ API server is not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    else
        echo "❌ API server is not running"
    fi
}

function show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📋 Recent logs:"
        echo "=============="
        tail -20 "$LOG_FILE"
        echo ""
        echo "📊 Monitor live: tail -f $LOG_FILE"
    else
        echo "No log file found"
    fi
}

# Main script logic
case "$1" in
    start)
        start_api
        ;;
    stop)
        stop_api
        ;;
    restart)
        stop_api
        sleep 1
        start_api
        ;;
    status)
        status_api
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the 2FA API server"
        echo "  stop    - Stop the 2FA API server"
        echo "  restart - Restart the 2FA API server"
        echo "  status  - Check server status"
        echo "  logs    - Show recent logs"
        echo ""
        echo "Examples:"
        echo "  $0 start          # Start the server"
        echo "  $0 status         # Check if running"
        echo "  $0 logs           # View recent logs"
        echo "  $0 stop           # Stop the server"
        exit 1
        ;;
esac