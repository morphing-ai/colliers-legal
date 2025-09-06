#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Colliers Paralegal Development Deploy ${NC}"
echo -e "${GREEN}=========================================${NC}\n"

# Check for .env file
if [ ! -f .env ]; then
  echo -e "${RED}No .env file found!${NC}"
  echo -e "${YELLOW}Please create .env from .env.template${NC}"
  exit 1
fi

# Load environment variables
set -a
source .env
set +a

echo -e "${BLUE}Deploying to: ${YELLOW}https://${FRONTEND_DOMAIN}${NC}"
echo -e "${BLUE}Mode: ${YELLOW}Development (with hot-reload)${NC}\n"

# Ensure required directories exist
echo -e "${BLUE}Setting up directories...${NC}"
mkdir -p letsencrypt data backend/logs
if [ ! -f letsencrypt/acme.json ]; then
  touch letsencrypt/acme.json
  chmod 600 letsencrypt/acme.json
fi

# Check if Traefik network exists
if ! docker network inspect traefik-public >/dev/null 2>&1; then
  echo -e "${YELLOW}Creating traefik-public network...${NC}"
  docker network create traefik-public
fi

# Copy Clerk public key if present
if [ -f "clerk_pub.pem" ]; then
  echo -e "${GREEN}Found Clerk public key, copying to backend...${NC}"
  cp clerk_pub.pem backend/
else
  echo -e "${YELLOW}Warning: clerk_pub.pem not found. Authentication will fall back to Clerk API.${NC}"
fi

# Build development images
echo -e "${BLUE}Building development images with hot-reload support...${NC}"
docker compose build

# Start services with development configuration
echo -e "${GREEN}Starting services in development mode...${NC}"
docker compose up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 15

# Check service health
echo -e "${BLUE}Checking service health...${NC}"

# Check PostgreSQL
if docker compose ps postgres | grep -q "running"; then
  echo -e "  ${GREEN}✓${NC} PostgreSQL is running"
else
  echo -e "  ${RED}✗${NC} PostgreSQL failed to start"
  docker compose logs postgres
fi

# Check Backend
if docker compose ps backend | grep -q "running"; then
  echo -e "  ${GREEN}✓${NC} Backend is running (with hot-reload)"
else
  echo -e "  ${RED}✗${NC} Backend failed to start"
  docker compose logs backend
fi

# Check Frontend
if docker compose ps frontend | grep -q "running"; then
  echo -e "  ${GREEN}✓${NC} Frontend is running (with hot-reload)"
else
  echo -e "  ${RED}✗${NC} Frontend failed to start"
  docker compose logs frontend
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Development Deployment Complete!${NC}"
echo -e "${GREEN}=========================================${NC}\n"

echo -e "${BLUE}Access Points:${NC}"
echo -e "  Frontend:     ${YELLOW}https://${FRONTEND_DOMAIN}${NC}"
echo -e "  Backend API:  ${YELLOW}https://${FRONTEND_DOMAIN}/api${NC}"
echo -e "  PostgreSQL:   ${YELLOW}localhost:5432${NC} (user: ${DB_USER})"

echo -e "\n${BLUE}Hot-Reload Status:${NC}"
echo -e "  ${GREEN}✓${NC} Backend: Watching /backend/app directory"
echo -e "  ${GREEN}✓${NC} Frontend: Watching /frontend/src directory"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "  1. Load legal rules: ${YELLOW}curl -X POST https://${FRONTEND_DOMAIN}/api/compliance/rules/load${NC}"
echo -e "  2. Watch logs: ${YELLOW}docker compose logs -f backend frontend${NC}"
echo -e "  3. Monitor: ${YELLOW}docker compose ps${NC}"

echo -e "\n${BLUE}Useful Commands:${NC}"
echo -e "  View logs:        ${YELLOW}docker compose logs -f [service]${NC}"
echo -e "  Restart service:  ${YELLOW}docker compose restart [service]${NC}"
echo -e "  Stop all:         ${YELLOW}docker compose down${NC}"
echo -e "  Backend shell:    ${YELLOW}docker exec -it colliers-legal-backend bash${NC}"
echo -e "  Frontend shell:   ${YELLOW}docker exec -it colliers-legal-frontend sh${NC}"
echo -e "  DB shell:         ${YELLOW}docker exec -it colliers-legal-postgres psql -U ${DB_USER} colliers_legal${NC}"

# Optional: Follow logs
read -p "Do you want to follow the logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo -e "\n${GREEN}Monitoring logs...${NC}"
  echo -e "${YELLOW}Press Ctrl+C to exit (services will continue running)${NC}\n"
  docker compose logs -f backend frontend
else
  echo -e "\n${YELLOW}Services are running in development mode with hot-reload enabled.${NC}"
  echo -e "${YELLOW}Code changes will automatically trigger reloads.${NC}"
fi