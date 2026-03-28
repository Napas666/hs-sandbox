#!/bin/bash
set -e

cd /root/app
git pull origin main
docker compose up --build -d
docker image prune -f
echo "Deploy complete!"
