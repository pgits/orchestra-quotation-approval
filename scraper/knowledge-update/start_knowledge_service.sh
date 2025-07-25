#!/bin/bash
# TD SYNNEX Knowledge Update Service Startup Script

set -e

echo "🚀 Starting TD SYNNEX Knowledge Update Service"
echo "=============================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure with your credentials"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

echo "✅ Environment variables loaded"

# Validate required environment variables
required_vars=(
    "AZURE_TENANT_ID"
    "AZURE_CLIENT_ID"
    "AZURE_CLIENT_SECRET"
    "OUTLOOK_USER_EMAIL"
    "CUSTOMER_NUMBER"
    "DATAVERSE_URL"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '  - %s\n' "${missing_vars[@]}"
    echo "Please check your .env file"
    exit 1
fi

echo "✅ Environment validation passed"

# Set default port if not specified
PORT=${PORT:-5000}

echo "📊 Service Configuration:"
echo "  Port: $PORT"
echo "  Customer Number: $CUSTOMER_NUMBER"
echo "  Outlook Email: $OUTLOOK_USER_EMAIL"
echo "  Copilot Agent: ${COPILOT_AGENT_NAME:-'Nate\'s Hardware Buddy v.1'}"
echo "  Dataverse URL: $DATAVERSE_URL"

echo ""
echo "🌐 Starting Flask application..."

# Start the Python application
exec python3 app.py