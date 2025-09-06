#!/bin/bash
# Force reload development environment with fresh build

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Forcing frontend rebuild...${NC}"

# Stop frontend container
docker compose stop frontend

# Remove frontend container
docker compose rm -f frontend

# Rebuild frontend image
docker compose build frontend --no-cache

# Start frontend with fresh build
docker compose up -d frontend

echo -e "${GREEN}Frontend rebuilt and restarted!${NC}"
echo -e "${YELLOW}Waiting for Vite to start...${NC}"
sleep 5

# Show logs
echo -e "${GREEN}Frontend logs:${NC}"
docker compose logs -f frontend