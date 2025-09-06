#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  Colliers - Paralegal Production Deploy ${NC}"
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
echo -e "${BLUE}Mode: ${YELLOW}Production${NC}\n"

# Ensure required directories exist
echo -e "${BLUE}Setting up directories...${NC}"
mkdir -p letsencrypt data
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

# Pull latest changes
echo -e "${BLUE}Pulling latest changes from repository...${NC}"
git pull origin master

# Build production images
echo -e "${BLUE}Building production images...${NC}"
docker compose build --no-cache

# Stop existing services
echo -e "${YELLOW}Stopping existing services...${NC}"
docker compose down

# Start services in production mode
echo -e "${GREEN}Starting services in production mode...${NC}"
docker compose up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 20

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
  echo -e "  ${GREEN}✓${NC} Backend is running"
  
  # Test backend health endpoint
  if curl -f -s "https://${FRONTEND_DOMAIN}/api/health" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Backend API is responsive"
  else
    echo -e "  ${YELLOW}!${NC} Backend API health check failed"
  fi
else
  echo -e "  ${RED}✗${NC} Backend failed to start"
  docker compose logs backend
fi

# Check Frontend
if docker compose ps frontend | grep -q "running"; then
  echo -e "  ${GREEN}✓${NC} Frontend is running"
  
  # Test frontend
  if curl -f -s "https://${FRONTEND_DOMAIN}" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Frontend is accessible"
  else
    echo -e "  ${YELLOW}!${NC} Frontend not accessible yet (may still be building)"
  fi
else
  echo -e "  ${RED}✗${NC} Frontend failed to start"
  docker compose logs frontend
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Production Deployment Complete!${NC}"
echo -e "${GREEN}=========================================${NC}\n"

echo -e "${BLUE}Access Points:${NC}"
echo -e "  Application:  ${YELLOW}https://${FRONTEND_DOMAIN}${NC}"
echo -e "  Backend API:  ${YELLOW}https://${FRONTEND_DOMAIN}/api${NC}"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "  1. Verify application: ${YELLOW}https://${FRONTEND_DOMAIN}${NC}"
echo -e "  2. Load legal rules: ${YELLOW}curl -X POST https://${FRONTEND_DOMAIN}/api/compliance/rules/load${NC}"
echo -e "  3. Monitor logs: ${YELLOW}docker compose logs -f${NC}"

echo -e "\n${BLUE}Monitoring Commands:${NC}"
echo -e "  View all logs:    ${YELLOW}docker compose logs -f${NC}"
echo -e "  View backend:     ${YELLOW}docker compose logs -f backend${NC}"
echo -e "  View frontend:    ${YELLOW}docker compose logs -f frontend${NC}"
echo -e "  Check status:     ${YELLOW}docker compose ps${NC}"

echo -e "\n${BLUE}Maintenance Commands:${NC}"
echo -e "  Restart all:      ${YELLOW}docker compose restart${NC}"
echo -e "  Stop all:         ${YELLOW}docker compose down${NC}"
echo -e "  Update & deploy:  ${YELLOW}git pull && ./deploy-prod.sh${NC}"
echo -e "  Database backup:  ${YELLOW}docker exec colliers-postgres pg_dump -U ${DB_USER} colliers_legal > backup.sql${NC}"

echo -e "\n${GREEN}Deployment successful! Application should be available at:${NC}"
echo -e "${YELLOW}https://${FRONTEND_DOMAIN}${NC}\n"