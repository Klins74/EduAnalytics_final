#!/bin/bash
# CI test runner script

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== EduAnalytics CI Test Runner ===${NC}"

# Set test environment
export ENV=testing
export DATABASE_URL=sqlite+aiosqlite:///./test.db
export REDIS_URL=redis://localhost:6379/15

# Create test directories
mkdir -p /app/test-results
mkdir -p /app/coverage-reports

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install -e .

# Run linting
echo -e "${YELLOW}Running code linting...${NC}"
flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Linting passed${NC}"
else
    echo -e "${RED}✗ Linting failed${NC}"
    exit 1
fi

# Run type checking
echo -e "${YELLOW}Running type checking...${NC}"
mypy app/ --ignore-missing-imports --no-strict-optional
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Type checking passed${NC}"
else
    echo -e "${RED}✗ Type checking failed${NC}"
    exit 1
fi

# Run security checks
echo -e "${YELLOW}Running security checks...${NC}"
if command -v bandit &> /dev/null; then
    bandit -r app/ -ll
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Security checks passed${NC}"
    else
        echo -e "${RED}✗ Security checks failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Bandit not available, skipping security checks${NC}"
fi

# Initialize test database
echo -e "${YELLOW}Initializing test database...${NC}"
python -c "
import asyncio
from app.db.init_db import init_db

async def main():
    await init_db()
    print('Test database initialized')

asyncio.run(main())
"

# Run unit tests
echo -e "${YELLOW}Running unit tests...${NC}"
pytest tests/ \
    -v \
    --cov=app \
    --cov-report=html:/app/coverage-reports/html \
    --cov-report=xml:/app/coverage-reports/coverage.xml \
    --cov-report=term \
    --junit-xml=/app/test-results/junit.xml \
    --html=/app/test-results/report.html \
    --self-contained-html \
    --cov-fail-under=85
    --cov-branch

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
    exit 1
fi

# Run integration tests
echo -e "${YELLOW}Running integration tests...${NC}"
pytest tests/integration/ \
    -v \
    --junit-xml=/app/test-results/integration-junit.xml

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Integration tests passed${NC}"
else
    echo -e "${RED}✗ Integration tests failed${NC}"
    exit 1
fi

# Run API contract tests
echo -e "${YELLOW}Running API contract tests...${NC}"
pytest tests/api/ \
    -v \
    --junit-xml=/app/test-results/api-junit.xml

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ API contract tests passed${NC}"
else
    echo -e "${RED}✗ API contract tests failed${NC}"
    exit 1
fi

# Generate coverage report
echo -e "${YELLOW}Generating coverage report...${NC}"
coverage report --show-missing

# Check coverage threshold
COVERAGE=$(coverage report --format=total)
echo "Coverage: ${COVERAGE}%"

if [ "$COVERAGE" -lt 85 ]; then
    echo -e "${RED}✗ Coverage below threshold (85%)${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Coverage above threshold (85%)${NC}"
fi

echo -e "${GREEN}=== All tests passed! ===${NC}"
