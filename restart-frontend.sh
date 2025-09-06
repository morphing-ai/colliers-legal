#!/bin/bash
# Quick script to restart frontend with fresh build

echo "Restarting frontend container..."
docker compose restart frontend

echo "Waiting for frontend to reload..."
sleep 5

echo "Following logs..."
docker compose logs -f frontend
