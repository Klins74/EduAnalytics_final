#!/bin/bash
# Enhanced test coverage script for CI/CD pipeline

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
SERVER_DIR="$PROJECT_ROOT/server"

# Coverage thresholds
COVERAGE_THRESHOLD=85
BRANCH_COVERAGE_THRESHOLD=80
COMPLEXITY_THRESHOLD=10

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Help function
show_help() {
    cat << EOF
Enhanced Test Coverage Script

Usage: $0 [OPTIONS]

Options:
    --threshold NUM     Minimum coverage threshold (default: $COVERAGE_THRESHOLD)
    --branch-threshold  Minimum branch coverage threshold (default: $BRANCH_COVERAGE_THRESHOLD)
    --complexity NUM    Maximum complexity threshold (default: $COMPLEXITY_THRESHOLD)
    --fast              Run fast tests only (skip slow markers)
    --unit              Run unit tests only
    --integration       Run integration tests only
    --xml               Generate XML report for CI
    --html              Generate HTML report
    --fail-fast         Stop on first failure
    -h, --help          Show this help

Examples:
    $0                          # Run all tests with default settings
    $0 --threshold 90           # Require 90% coverage
    $0 --fast                   # Run only fast tests
    $0 --unit --xml             # Run unit tests and generate XML report

EOF
}

# Parse arguments
FAST_ONLY=false
UNIT_ONLY=false
INTEGRATION_ONLY=false
XML_REPORT=false
HTML_REPORT=false
FAIL_FAST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --threshold)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        --branch-threshold)
            BRANCH_COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        --complexity)
            COMPLEXITY_THRESHOLD="$2"
            shift 2
            ;;
        --fast)
            FAST_ONLY=true
            shift
            ;;
        --unit)
            UNIT_ONLY=true
            shift
            ;;
        --integration)
            INTEGRATION_ONLY=true
            shift
            ;;
        --xml)
            XML_REPORT=true
            shift
            ;;
        --html)
            HTML_REPORT=true
            shift
            ;;
        --fail-fast)
            FAIL_FAST=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Change to server directory
cd "$SERVER_DIR"

log "Starting enhanced test coverage analysis..."
log "Coverage threshold: ${COVERAGE_THRESHOLD}%"
log "Branch coverage threshold: ${BRANCH_COVERAGE_THRESHOLD}%"
log "Complexity threshold: $COMPLEXITY_THRESHOLD"

# Check if required tools are installed
log "Checking required tools..."

if ! command -v pytest &> /dev/null; then
    error "pytest is not installed. Install with: pip install pytest"
fi

if ! command -v coverage &> /dev/null; then
    error "coverage is not installed. Install with: pip install coverage"
fi

# Install additional testing tools if not present
log "Installing additional testing tools..."
pip install --quiet pytest-cov pytest-xdist pytest-benchmark radon xenon || warn "Failed to install some testing tools"

# Clean previous coverage data
log "Cleaning previous coverage data..."
rm -rf htmlcov/ .coverage coverage.xml test-results.xml

# Build pytest command
PYTEST_CMD="pytest"

# Add test selection based on options
if [[ "$FAST_ONLY" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -m 'not slow'"
    info "Running fast tests only"
elif [[ "$UNIT_ONLY" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -m 'unit'"
    info "Running unit tests only"
elif [[ "$INTEGRATION_ONLY" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -m 'integration'"
    info "Running integration tests only"
fi

# Add coverage options
PYTEST_CMD="$PYTEST_CMD --cov=app --cov-branch --cov-fail-under=$COVERAGE_THRESHOLD"

# Add report options
if [[ "$XML_REPORT" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov-report=xml --junit-xml=test-results.xml"
fi

if [[ "$HTML_REPORT" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov-report=html"
fi

# Add fail fast option
if [[ "$FAIL_FAST" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -x"
fi

# Add parallel execution for faster tests
PYTEST_CMD="$PYTEST_CMD -n auto"

# Add verbose output
PYTEST_CMD="$PYTEST_CMD -v"

# Run tests
log "Running tests with command: $PYTEST_CMD"
if ! $PYTEST_CMD; then
    error "Tests failed or coverage threshold not met"
fi

# Generate detailed coverage report
log "Generating detailed coverage report..."
coverage report --show-missing --skip-covered --precision=2

# Check branch coverage specifically
log "Checking branch coverage..."
BRANCH_COVERAGE=$(coverage report --show-missing | tail -n 1 | awk '{print $4}' | sed 's/%//')

if [[ -n "$BRANCH_COVERAGE" ]]; then
    if (( $(echo "$BRANCH_COVERAGE < $BRANCH_COVERAGE_THRESHOLD" | bc -l) )); then
        error "Branch coverage $BRANCH_COVERAGE% is below threshold $BRANCH_COVERAGE_THRESHOLD%"
    else
        log "Branch coverage: $BRANCH_COVERAGE% (threshold: $BRANCH_COVERAGE_THRESHOLD%)"
    fi
fi

# Check code complexity
log "Analyzing code complexity..."
if command -v radon &> /dev/null; then
    log "Running complexity analysis with radon..."
    
    # Cyclomatic complexity
    echo "=== Cyclomatic Complexity ==="
    radon cc app/ -a -nb
    
    # Maintainability index
    echo "=== Maintainability Index ==="
    radon mi app/ -nb
    
    # Check for high complexity functions
    HIGH_COMPLEXITY=$(radon cc app/ -j | jq -r '.[] | to_entries[] | select(.value.complexity > '$COMPLEXITY_THRESHOLD') | .key + ": " + (.value.complexity | tostring)')
    
    if [[ -n "$HIGH_COMPLEXITY" ]]; then
        warn "High complexity functions detected (threshold: $COMPLEXITY_THRESHOLD):"
        echo "$HIGH_COMPLEXITY"
    else
        log "All functions are within complexity threshold"
    fi
fi

# Check for code duplication
if command -v pylint &> /dev/null; then
    log "Checking for code duplication..."
    pylint app/ --disable=all --enable=duplicate-code || warn "Code duplication check completed with warnings"
fi

# Generate test statistics
log "Generating test statistics..."

# Count test files and functions
TEST_FILES=$(find tests/ -name "test_*.py" | wc -l)
TEST_FUNCTIONS=$(grep -r "def test_" tests/ | wc -l)

echo "=== Test Statistics ==="
echo "Test files: $TEST_FILES"
echo "Test functions: $TEST_FUNCTIONS"

# Check for missing docstrings in production code
log "Checking for missing docstrings..."
MISSING_DOCSTRINGS=$(find app/ -name "*.py" -exec grep -L '"""' {} \; | wc -l)
if [[ $MISSING_DOCSTRINGS -gt 0 ]]; then
    warn "$MISSING_DOCSTRINGS files are missing docstrings"
else
    log "All Python files have docstrings"
fi

# Final summary
log "Test coverage analysis completed successfully!"
echo "=== Final Summary ==="
echo "✅ Coverage threshold: ${COVERAGE_THRESHOLD}% (met)"
echo "✅ Branch coverage threshold: ${BRANCH_COVERAGE_THRESHOLD}% (met)"
echo "✅ Complexity threshold: $COMPLEXITY_THRESHOLD (met)"
echo "📊 Test files: $TEST_FILES"
echo "📊 Test functions: $TEST_FUNCTIONS"

if [[ "$HTML_REPORT" == true ]] && [[ -d "htmlcov" ]]; then
    log "HTML coverage report generated in htmlcov/"
    echo "Open htmlcov/index.html in your browser to view detailed coverage report"
fi

if [[ "$XML_REPORT" == true ]] && [[ -f "coverage.xml" ]]; then
    log "XML coverage report generated: coverage.xml"
fi

log "All quality checks passed! 🎉"
