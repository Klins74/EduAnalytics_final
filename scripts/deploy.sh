#!/bin/bash
# Deployment script for EduAnalytics

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEFAULT_ENVIRONMENT="staging"
DEFAULT_VERSION="latest"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
show_help() {
    cat << EOF
EduAnalytics Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment   Target environment (dev, staging, prod) [default: staging]
    -v, --version       Version to deploy [default: latest]
    -t, --tag           Git tag to deploy
    -b, --build         Build images before deployment
    -f, --force         Force deployment without confirmation
    -d, --dry-run       Show what would be deployed without actually deploying
    -h, --help          Show this help message

Examples:
    $0 --environment staging --build
    $0 --environment prod --version v1.2.3
    $0 --environment prod --tag v1.2.3 --build

EOF
}

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

# Parse command line arguments
ENVIRONMENT="$DEFAULT_ENVIRONMENT"
VERSION="$DEFAULT_VERSION"
GIT_TAG=""
BUILD_IMAGES=false
FORCE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -t|--tag)
            GIT_TAG="$2"
            shift 2
            ;;
        -b|--build)
            BUILD_IMAGES=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
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

# Validate environment
case $ENVIRONMENT in
    dev|development)
        ENVIRONMENT="development"
        COMPOSE_PROFILE="dev"
        ;;
    staging|stage)
        ENVIRONMENT="staging"
        COMPOSE_PROFILE="staging"
        ;;
    prod|production)
        ENVIRONMENT="production"
        COMPOSE_PROFILE="prod"
        ;;
    *)
        error "Invalid environment: $ENVIRONMENT. Must be one of: dev, staging, prod"
        ;;
esac

log "Starting deployment to $ENVIRONMENT environment"

# Change to project root
cd "$PROJECT_ROOT"

# Check if git tag is specified
if [[ -n "$GIT_TAG" ]]; then
    log "Checking out git tag: $GIT_TAG"
    if [[ "$DRY_RUN" == false ]]; then
        git checkout "$GIT_TAG" || error "Failed to checkout tag $GIT_TAG"
    fi
    VERSION="$GIT_TAG"
fi

# Validate that we're in a git repository
if [[ ! -d ".git" ]]; then
    error "Not in a git repository"
fi

# Get current commit hash
COMMIT_HASH=$(git rev-parse --short HEAD)
log "Current commit: $COMMIT_HASH"

# Build images if requested
if [[ "$BUILD_IMAGES" == true ]]; then
    log "Building Docker images..."
    
    if [[ "$DRY_RUN" == false ]]; then
        # Build production image
        docker build \
            -f server/Dockerfile.production \
            --target production \
            --tag "eduanalytics:$VERSION" \
            --tag "eduanalytics:latest" \
            --build-arg VERSION="$VERSION" \
            --build-arg COMMIT_HASH="$COMMIT_HASH" \
            .
        
        log "Built image: eduanalytics:$VERSION"
    else
        log "DRY RUN: Would build eduanalytics:$VERSION"
    fi
fi

# Load environment configuration
ENV_FILE="config/env.$ENVIRONMENT"
if [[ -f "$ENV_FILE" ]]; then
    log "Loading environment configuration from $ENV_FILE"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    warn "Environment file $ENV_FILE not found"
fi

# Check if secrets are available for production
if [[ "$ENVIRONMENT" == "production" ]]; then
    log "Checking production secrets..."
    
    REQUIRED_SECRETS=(
        "database_url_prod"
        "redis_url_prod"
        "secret_key_prod"
        "jwt_secret_prod"
    )
    
    for secret in "${REQUIRED_SECRETS[@]}"; do
        if ! docker secret ls | grep -q "$secret"; then
            warn "Required secret '$secret' not found in Docker Swarm"
        fi
    done
fi

# Confirm deployment
if [[ "$FORCE" == false && "$DRY_RUN" == false ]]; then
    echo -e "${YELLOW}About to deploy:${NC}"
    echo "  Environment: $ENVIRONMENT"
    echo "  Version: $VERSION"
    echo "  Commit: $COMMIT_HASH"
    echo "  Profile: $COMPOSE_PROFILE"
    echo ""
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Deployment cancelled"
        exit 0
    fi
fi

# Stop existing services
log "Stopping existing services..."
if [[ "$DRY_RUN" == false ]]; then
    docker-compose \
        -f docker-compose.yml \
        -f docker-compose.profiles.yml \
        --profile "$COMPOSE_PROFILE" \
        down || warn "Failed to stop some services"
else
    log "DRY RUN: Would stop services with profile $COMPOSE_PROFILE"
fi

# Deploy new version
log "Deploying version $VERSION..."
if [[ "$DRY_RUN" == false ]]; then
    export VERSION="$VERSION"
    export COMMIT_HASH="$COMMIT_HASH"
    
    docker-compose \
        -f docker-compose.yml \
        -f docker-compose.profiles.yml \
        --profile "$COMPOSE_PROFILE" \
        up -d
    
    if [[ $? -eq 0 ]]; then
        log "Deployment successful!"
    else
        error "Deployment failed"
    fi
else
    log "DRY RUN: Would deploy with profile $COMPOSE_PROFILE"
fi

# Health check
if [[ "$DRY_RUN" == false ]]; then
    log "Performing health check..."
    
    # Wait for service to start
    sleep 10
    
    # Get the port based on environment
    case $ENVIRONMENT in
        development)
            PORT=8000
            ;;
        staging)
            PORT=8080
            ;;
        production)
            PORT=80
            ;;
    esac
    
    # Check health endpoint
    for i in {1..30}; do
        if curl -f "http://localhost:$PORT/api/health" > /dev/null 2>&1; then
            log "Health check passed!"
            break
        else
            warn "Health check attempt $i/30 failed, retrying..."
            sleep 5
        fi
        
        if [[ $i -eq 30 ]]; then
            error "Health check failed after 30 attempts"
        fi
    done
fi

# Show deployment summary
log "Deployment Summary:"
echo "  Environment: $ENVIRONMENT"
echo "  Version: $VERSION"
echo "  Commit: $COMMIT_HASH"
echo "  Status: $(if [[ "$DRY_RUN" == true ]]; then echo "DRY RUN"; else echo "DEPLOYED"; fi)"

if [[ "$ENVIRONMENT" == "production" ]]; then
    log "Production deployment completed. Monitor logs and metrics carefully."
fi

log "Deployment script finished successfully!"
