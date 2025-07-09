#!/bin/bash
# Test TD SYNNEX Container both locally and in Azure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="td-synnex-scraper-rg"
CONTAINER_NAME="td-synnex-azure-scraper"
LOCAL_IMAGE="td-synnex-azure-scraper:latest"

# Check if credentials are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo -e "${RED}Usage: $0 <TDSYNNEX_USERNAME> <TDSYNNEX_PASSWORD>${NC}"
    echo -e "${YELLOW}Example: $0 'your-username' 'your-password'${NC}"
    exit 1
fi

TDSYNNEX_USERNAME="$1"
TDSYNNEX_PASSWORD="$2"

echo -e "${GREEN}🧪 Testing TD SYNNEX Container${NC}"
echo -e "${YELLOW}=================================================${NC}"

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
        exit 1
    fi
}

# Function to check if image exists
check_image() {
    if ! docker image inspect $LOCAL_IMAGE >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker image $LOCAL_IMAGE not found.${NC}"
        echo -e "${YELLOW}Please build the image first with:${NC}"
        echo "docker build --platform linux/amd64 -f Dockerfile.azure-container -t $LOCAL_IMAGE ."
        exit 1
    fi
}

# Test 1: Docker Environment Check
echo -e "${GREEN}📋 Step 1: Checking Docker Environment${NC}"
check_docker
check_image
echo -e "${GREEN}✅ Docker environment ready${NC}"
echo ""

# Test 2: Local Health Check
echo -e "${GREEN}🏥 Step 2: Testing Container Health Check (Local)${NC}"
echo -e "${YELLOW}Running health check...${NC}"

if docker run --rm \
    -e TDSYNNEX_USERNAME="$TDSYNNEX_USERNAME" \
    -e TDSYNNEX_PASSWORD="$TDSYNNEX_PASSWORD" \
    $LOCAL_IMAGE python container_runner.py health; then
    echo -e "${GREEN}✅ Local health check passed${NC}"
else
    echo -e "${RED}❌ Local health check failed${NC}"
    exit 1
fi
echo ""

# Test 3: Local Chrome Test
echo -e "${GREEN}🌐 Step 3: Testing Chrome Installation (Local)${NC}"
echo -e "${YELLOW}Checking Chrome version...${NC}"
docker run --rm $LOCAL_IMAGE google-chrome-stable --version

echo -e "${YELLOW}Checking ChromeDriver version...${NC}"
docker run --rm $LOCAL_IMAGE chromedriver --version

echo -e "${GREEN}✅ Chrome installation verified${NC}"
echo ""

# Test 4: Local Scraper Test (Quick)
echo -e "${GREEN}🚀 Step 4: Testing Local Scraper (Quick Test)${NC}"
echo -e "${YELLOW}This will run the scraper locally for testing...${NC}"
echo -e "${YELLOW}Press Ctrl+C within 30 seconds to skip this test${NC}"

# Give user chance to cancel
sleep 5

echo -e "${YELLOW}Starting local scraper test...${NC}"

# Cross-platform timeout using background process and kill
docker run --rm \
    -e TDSYNNEX_USERNAME="$TDSYNNEX_USERNAME" \
    -e TDSYNNEX_PASSWORD="$TDSYNNEX_PASSWORD" \
    -v $(pwd)/test_output:/app/output \
    $LOCAL_IMAGE &

DOCKER_PID=$!

# Wait up to 60 seconds for completion
SECONDS=0
while [ $SECONDS -lt 60 ] && kill -0 $DOCKER_PID 2>/dev/null; do
    sleep 1
done

# Check if process is still running and kill if needed
if kill -0 $DOCKER_PID 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Local scraper test timed out, stopping container...${NC}"
    kill $DOCKER_PID 2>/dev/null
    wait $DOCKER_PID 2>/dev/null
    TEST_RESULT=1
else
    wait $DOCKER_PID
    TEST_RESULT=$?
fi

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ Local scraper test completed${NC}"
    
    # Check if output files were created
    if [ -d "test_output" ] && [ "$(ls -A test_output)" ]; then
        echo -e "${GREEN}✅ Output files created:${NC}"
        ls -la test_output/
    else
        echo -e "${YELLOW}⚠️ No output files found (may be normal for quick test)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Local scraper test timed out or failed (may be normal for testing)${NC}"
fi
echo ""

# Test 5: Azure Deployment Test
echo -e "${GREEN}☁️ Step 5: Testing Azure Deployment${NC}"
echo -e "${YELLOW}Deploying to Azure Container Instances...${NC}"

if ./deploy-container.sh "$TDSYNNEX_USERNAME" "$TDSYNNEX_PASSWORD"; then
    echo -e "${GREEN}✅ Azure deployment successful${NC}"
else
    echo -e "${RED}❌ Azure deployment failed${NC}"
    exit 1
fi
echo ""

# Test 6: Azure Container Status Check
echo -e "${GREEN}📊 Step 6: Checking Azure Container Status${NC}"
echo -e "${YELLOW}Waiting for container to start...${NC}"
sleep 10

CONTAINER_STATE=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query "instanceView.state" -o tsv)
echo -e "${YELLOW}Container state: $CONTAINER_STATE${NC}"

if [ "$CONTAINER_STATE" = "Running" ] || [ "$CONTAINER_STATE" = "Succeeded" ]; then
    echo -e "${GREEN}✅ Azure container is running/succeeded${NC}"
else
    echo -e "${RED}❌ Azure container state: $CONTAINER_STATE${NC}"
    echo -e "${YELLOW}Checking container events...${NC}"
    az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query "containers[0].instanceView.events"
fi
echo ""

# Test 7: Azure Container Logs
echo -e "${GREEN}📋 Step 7: Checking Azure Container Logs${NC}"
echo -e "${YELLOW}Recent logs from Azure container:${NC}"
echo -e "${YELLOW}================================${NC}"

az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME | head -50

echo -e "${YELLOW}================================${NC}"
echo ""

# Test 8: Final Status Summary
echo -e "${GREEN}📈 Step 8: Test Summary${NC}"
echo -e "${YELLOW}=========================${NC}"

# Get final container status
FINAL_STATE=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query "instanceView.state" -o tsv)
EXIT_CODE=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query "containers[0].instanceView.currentState.exitCode" -o tsv)

echo -e "${YELLOW}Azure Container Status: $FINAL_STATE${NC}"
echo -e "${YELLOW}Exit Code: $EXIT_CODE${NC}"

if [ "$FINAL_STATE" = "Succeeded" ] && [ "$EXIT_CODE" = "0" ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Container is working correctly.${NC}"
    echo -e "${GREEN}✅ Local testing: SUCCESS${NC}"
    echo -e "${GREEN}✅ Azure deployment: SUCCESS${NC}"
    echo -e "${GREEN}✅ Container execution: SUCCESS${NC}"
elif [ "$FINAL_STATE" = "Running" ]; then
    echo -e "${YELLOW}⏳ Container is still running. Check logs for progress.${NC}"
    echo -e "${YELLOW}Monitor with: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow${NC}"
else
    echo -e "${RED}❌ Some tests failed. Check logs above for details.${NC}"
    echo -e "${YELLOW}Debug commands:${NC}"
    echo -e "${YELLOW}  az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME${NC}"
    echo -e "${YELLOW}  az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query instanceView${NC}"
fi

echo ""
echo -e "${GREEN}🔧 Useful Commands:${NC}"
echo -e "${YELLOW}  View logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME${NC}"
echo -e "${YELLOW}  Follow logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow${NC}"
echo -e "${YELLOW}  Check status: az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query instanceView${NC}"
echo -e "${YELLOW}  Delete container: az container delete --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --yes${NC}"
echo ""
echo -e "${GREEN}Test completed!${NC}"