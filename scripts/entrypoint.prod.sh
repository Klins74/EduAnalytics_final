#!/bin/bash
# Production entrypoint script for EduAnalytics

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting EduAnalytics in production mode...${NC}"

# Wait for database to be ready
echo -e "${YELLOW}Waiting for database...${NC}"
while ! pg_isready -h ${DB_HOST:-postgres-prod} -p ${DB_PORT:-5432} -U ${DB_USER:-eduanalytics}; do
    echo "Database is unavailable - sleeping"
    sleep 2
done
echo -e "${GREEN}Database is ready!${NC}"

# Wait for Redis to be ready
echo -e "${YELLOW}Waiting for Redis...${NC}"
while ! redis-cli -h ${REDIS_HOST:-redis-prod} -p ${REDIS_PORT:-6379} ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 2
done
echo -e "${GREEN}Redis is ready!${NC}"

# Load secrets if available
if [ -f "/run/secrets/database_url_prod" ]; then
    export DATABASE_URL=$(cat /run/secrets/database_url_prod)
    echo -e "${GREEN}Loaded database URL from Docker secret${NC}"
fi

if [ -f "/run/secrets/redis_url_prod" ]; then
    export REDIS_URL=$(cat /run/secrets/redis_url_prod)
    echo -e "${GREEN}Loaded Redis URL from Docker secret${NC}"
fi

if [ -f "/run/secrets/secret_key_prod" ]; then
    export SECRET_KEY=$(cat /run/secrets/secret_key_prod)
    echo -e "${GREEN}Loaded secret key from Docker secret${NC}"
fi

if [ -f "/run/secrets/jwt_secret_prod" ]; then
    export JWT_SECRET_KEY=$(cat /run/secrets/jwt_secret_prod)
    echo -e "${GREEN}Loaded JWT secret from Docker secret${NC}"
fi

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
cd /app
python -c "
import asyncio
from app.db.init_db import init_db

async def main():
    await init_db()
    print('Database initialized successfully')

asyncio.run(main())
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database migrations completed successfully${NC}"
else
    echo -e "${RED}Database migrations failed${NC}"
    exit 1
fi

# Create uploads directory if it doesn't exist
mkdir -p /app/uploads/submissions
mkdir -p /app/uploads/temp
mkdir -p /app/logs

# Set proper permissions
chmod 755 /app/uploads
chmod 755 /app/logs

# Validate configuration
echo -e "${YELLOW}Validating configuration...${NC}"
python -c "
import os
import sys

required_vars = ['SECRET_KEY', 'DATABASE_URL']
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f'Missing required environment variables: {missing_vars}')
    sys.exit(1)
else:
    print('Configuration validation passed')
"

if [ $? -ne 0 ]; then
    echo -e "${RED}Configuration validation failed${NC}"
    exit 1
fi

# Start application
echo -e "${GREEN}Starting EduAnalytics application...${NC}"
echo -e "${YELLOW}Command: $@${NC}"

# Execute the command passed to the container
exec "$@"
