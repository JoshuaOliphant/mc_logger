#!/bin/bash

# MC Logger - Start Script
# Usage: ./scripts/start.sh [--with-adw]
#   --with-adw: Also start the ADW webhook server on port 8001

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse command line arguments
START_ADW=false
if [[ "$1" == "--with-adw" ]]; then
    START_ADW=true
fi

echo -e "${BLUE}Starting MC Logger...${NC}"

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Shutting down services...${NC}"

    # Kill all child processes
    jobs -p | xargs -r kill 2>/dev/null

    # Wait for processes to terminate
    wait

    echo -e "${GREEN}Services stopped successfully.${NC}"
    exit 0
}

# Trap EXIT, INT, and TERM signals
trap cleanup EXIT INT TERM

# Start MC Logger example app
echo -e "${GREEN}Starting MC Logger example app...${NC}"
cd "$PROJECT_ROOT"
uv run python examples/fastapi_app.py &
EXAMPLE_PID=$!

# Wait for example app to start
echo "Waiting for example app to start..."
sleep 3

# Check if example app is running
if ! kill -0 $EXAMPLE_PID 2>/dev/null; then
    echo -e "${RED}Example app failed to start!${NC}"
    exit 1
fi

# Optionally start ADW webhook server
if [ "$START_ADW" = true ]; then
    echo -e "${GREEN}Starting ADW webhook server...${NC}"
    cd "$PROJECT_ROOT"
    uv run adws/trigger_webhook.py &
    ADW_PID=$!

    # Wait for webhook server to start
    sleep 2

    # Check if webhook server is running
    if ! kill -0 $ADW_PID 2>/dev/null; then
        echo -e "${RED}ADW webhook server failed to start!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Services started successfully!${NC}"
echo -e "${BLUE}Example App: http://localhost:8000${NC}"
echo -e "${BLUE}API Docs:    http://localhost:8000/docs${NC}"
if [ "$START_ADW" = true ]; then
    echo -e "${BLUE}ADW Webhook: http://localhost:8001${NC}"
    echo -e "${BLUE}ADW Health:  http://localhost:8001/health${NC}"
fi
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for user to press Ctrl+C
wait
