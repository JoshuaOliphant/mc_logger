#!/bin/bash

# MC Logger - Stop Script
# Stops MC Logger example app and ADW services

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping MC Logger...${NC}"

# Kill any running start.sh processes
echo -e "${GREEN}Killing start.sh processes...${NC}"
pkill -f "start.sh" 2>/dev/null

# Kill example app
echo -e "${GREEN}Killing MC Logger example app...${NC}"
pkill -f "examples/fastapi_app.py" 2>/dev/null

# Kill ADW webhook server
echo -e "${GREEN}Killing ADW webhook server...${NC}"
pkill -f "trigger_webhook.py" 2>/dev/null

# Kill processes on specific ports (8000 for example app, 8001 for ADW webhook)
echo -e "${GREEN}Killing processes on ports 8000 and 8001...${NC}"
lsof -ti:8000,8001 | xargs kill -9 2>/dev/null

echo -e "${GREEN}✓ Services stopped successfully!${NC}"
