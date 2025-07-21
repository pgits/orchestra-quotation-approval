#!/bin/bash

# TD SYNNEX Email Verification Service Startup Script
# This script starts the email verification service for 2FA code retrieval

set -e

# Configuration
SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="email-verification-service"
DEFAULT_PORT=5000
LOG_FILE="$SERVICE_DIR/service.log"
PID_FILE="$SERVICE_DIR/service.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Function to find available port
find_available_port() {
    local port=$DEFAULT_PORT
    while [ $port -le 5010 ]; do
        if check_port $port; then
            echo $port
            return 0
        fi
        ((port++))
    done
    echo ""
    return 1
}

# Function to stop existing service
stop_service() {
    print_status "Stopping existing email verification service..."
    
    # Kill by PID file if exists
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            print_success "Stopped service with PID $pid"
        fi
        rm -f "$PID_FILE"
    fi
    
    # Kill any remaining Python processes running app.py
    pkill -f "python.*app.py" 2>/dev/null || true
    
    # Wait for processes to stop
    sleep 2
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if we're in the right directory
    if [ ! -f "$SERVICE_DIR/app.py" ]; then
        print_error "app.py not found in $SERVICE_DIR"
        print_error "Please run this script from the email-verification-service directory"
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$SERVICE_DIR/.env" ]; then
        print_error ".env file not found"
        print_error "Please create .env file with Azure AD credentials"
        print_error "See AZURE_APP_REGISTRATION_SETUP.md for setup instructions"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$SERVICE_DIR/.venv" ]; then
        print_warning "Virtual environment not found, creating one..."
        python3 -m venv .venv || {
            print_error "Failed to create virtual environment"
            print_error "Please ensure Python 3 is installed"
            exit 1
        }
    fi
    
    print_success "Prerequisites check passed"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    source "$SERVICE_DIR/.venv/bin/activate"
    
    if command -v uv > /dev/null 2>&1; then
        print_status "Using uv for faster package installation..."
        uv pip install -r requirements.txt
    else
        print_status "Using pip for package installation..."
        pip install -r requirements.txt
    fi
    
    print_success "Dependencies installed"
}

# Function to test authentication
test_authentication() {
    print_status "Testing Azure AD authentication..."
    
    source "$SERVICE_DIR/.venv/bin/activate"
    
    if python3 test_auth.py > /dev/null 2>&1; then
        print_success "Authentication test passed"
    else
        print_error "Authentication test failed"
        print_error "Please check your Azure AD credentials in .env file"
        print_error "Run: python3 test_auth.py for detailed error information"
        exit 1
    fi
}

# Function to start the service
start_service() {
    local port=$(find_available_port)
    
    if [ -z "$port" ]; then
        print_error "No available ports found between $DEFAULT_PORT and 5010"
        exit 1
    fi
    
    print_status "Starting email verification service on port $port..."
    
    source "$SERVICE_DIR/.venv/bin/activate"
    
    # Start the service in background
    PORT=$port python3 app.py > "$LOG_FILE" 2>&1 &
    local service_pid=$!
    
    # Save PID to file
    echo $service_pid > "$PID_FILE"
    
    # Wait a moment for service to start
    sleep 3
    
    # Check if service is running
    if ps -p $service_pid > /dev/null 2>&1; then
        print_success "Service started successfully!"
        print_success "PID: $service_pid"
        print_success "Port: $port"
        print_success "Log file: $LOG_FILE"
        
        # Test the service endpoints
        print_status "Testing service endpoints..."
        
        if curl -s "http://localhost:$port/status" > /dev/null 2>&1; then
            print_success "✅ Service is responding on http://localhost:$port"
            
            echo ""
            echo -e "${BLUE}Available endpoints:${NC}"
            echo "  • GET http://localhost:$port/status - Service status"
            echo "  • GET http://localhost:$port/health - Health check with Graph API test"
            echo "  • GET http://localhost:$port/test-email - Test email connection"
            echo "  • GET http://localhost:$port/verification-code?sender=do_not_reply@tdsynnex.com - Get verification code"
            echo ""
            echo -e "${BLUE}Usage examples:${NC}"
            echo "  curl http://localhost:$port/status"
            echo "  curl http://localhost:$port/health"
            echo "  curl 'http://localhost:$port/verification-code?sender=do_not_reply@tdsynnex.com'"
            echo ""
            echo -e "${BLUE}To stop the service:${NC}"
            echo "  ./start_email_service.sh stop"
            echo ""
        else
            print_error "Service started but not responding"
            exit 1
        fi
    else
        print_error "Failed to start service"
        print_error "Check log file: $LOG_FILE"
        exit 1
    fi
}

# Function to show service status
show_status() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            # Try to extract port from log file
            local port=$(grep "Running on http://127.0.0.1:" "$LOG_FILE" 2>/dev/null | tail -1 | sed 's/.*127.0.0.1://' | cut -d' ' -f1)
            print_success "Service is running"
            echo "  PID: $pid"
            echo "  Port: ${port:-'check log file'}"
            echo "  URL: http://localhost:${port:-'PORT'}"
        else
            print_warning "PID file exists but service is not running"
            rm -f "$PID_FILE"
        fi
    else
        print_warning "Service is not running"
    fi
}

# Function to show help
show_help() {
    echo "TD SYNNEX Email Verification Service"
    echo ""
    echo "Usage: $0 [start|stop|restart|status|test|help]"
    echo ""
    echo "Commands:"
    echo "  start    - Start the email verification service"
    echo "  stop     - Stop the email verification service"
    echo "  restart  - Restart the email verification service"
    echo "  status   - Show service status"
    echo "  test     - Test authentication only"
    echo "  help     - Show this help message"
    echo ""
    echo "The service provides REST API endpoints for retrieving TD SYNNEX"
    echo "2FA verification codes from Outlook emails."
    echo ""
    echo "Prerequisites:"
    echo "  1. Python 3.7+ installed"
    echo "  2. .env file with Azure AD credentials configured"
    echo "  3. Azure App Registration with Mail.Read permissions"
    echo ""
    echo "For initial setup, see: AZURE_APP_REGISTRATION_SETUP.md"
}

# Main script logic
case "${1:-start}" in
    "start")
        echo "🚀 TD SYNNEX Email Verification Service Startup"
        echo "=============================================="
        stop_service
        check_prerequisites
        install_dependencies
        test_authentication
        start_service
        ;;
    "stop")
        echo "🛑 Stopping TD SYNNEX Email Verification Service"
        echo "=============================================="
        stop_service
        print_success "Service stopped"
        ;;
    "restart")
        echo "🔄 Restarting TD SYNNEX Email Verification Service"
        echo "==============================================="
        stop_service
        start_service
        ;;
    "status")
        echo "📊 TD SYNNEX Email Verification Service Status"
        echo "=============================================="
        show_status
        ;;
    "test")
        echo "🧪 Testing Azure AD Authentication"
        echo "================================="
        check_prerequisites
        source "$SERVICE_DIR/.venv/bin/activate"
        python3 test_auth.py
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac