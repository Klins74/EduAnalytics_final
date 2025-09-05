#!/bin/bash
# Build and publish Docker images script

set -e

# Configuration
REGISTRY="${REGISTRY:-ghcr.io}"
NAMESPACE="${NAMESPACE:-your-org}"
IMAGE_NAME="${IMAGE_NAME:-eduanalytics}"
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
EduAnalytics Docker Build and Publish Script

Usage: $0 [OPTIONS]

Options:
    -r, --registry      Docker registry [default: ghcr.io]
    -n, --namespace     Registry namespace [default: your-org]
    -i, --image         Image name [default: eduanalytics]
    -v, --version       Version tag [default: latest]
    -t, --tags          Additional tags (comma-separated)
    -p, --platforms     Target platforms [default: linux/amd64,linux/arm64]
    --push              Push images to registry
    --no-cache          Build without cache
    --dry-run          Show what would be built/pushed
    -h, --help          Show this help message

Examples:
    $0 --version v1.2.3 --push
    $0 --version latest --tags v1.2,stable --push
    $0 --registry my-registry.com --namespace myorg --push

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
VERSION="$DEFAULT_VERSION"
ADDITIONAL_TAGS=""
PLATFORMS="linux/amd64,linux/arm64"
PUSH=false
NO_CACHE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -t|--tags)
            ADDITIONAL_TAGS="$2"
            shift 2
            ;;
        -p|--platforms)
            PLATFORMS="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --dry-run)
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

# Construct full image name
FULL_IMAGE_NAME="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}"

# Get git information
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "")

log "Build Configuration:"
echo "  Registry: $REGISTRY"
echo "  Namespace: $NAMESPACE"
echo "  Image: $IMAGE_NAME"
echo "  Full name: $FULL_IMAGE_NAME"
echo "  Version: $VERSION"
echo "  Platforms: $PLATFORMS"
echo "  Git commit: $GIT_COMMIT"
echo "  Git branch: $GIT_BRANCH"
echo "  Git tag: ${GIT_TAG:-none}"
echo "  Push: $PUSH"
echo "  No cache: $NO_CACHE"
echo "  Dry run: $DRY_RUN"

# Prepare tags
TAGS=("$VERSION")

# Add git-based tags
if [[ -n "$GIT_TAG" ]]; then
    TAGS+=("$GIT_TAG")
fi

if [[ "$GIT_BRANCH" == "main" ]] || [[ "$GIT_BRANCH" == "master" ]]; then
    TAGS+=("latest")
elif [[ "$GIT_BRANCH" == "develop" ]]; then
    TAGS+=("develop")
fi

# Add commit-based tag
TAGS+=("$GIT_BRANCH-$GIT_COMMIT")

# Add additional tags if provided
if [[ -n "$ADDITIONAL_TAGS" ]]; then
    IFS=',' read -ra ADDITIONAL_TAG_ARRAY <<< "$ADDITIONAL_TAGS"
    for tag in "${ADDITIONAL_TAG_ARRAY[@]}"; do
        TAGS+=("$tag")
    done
fi

# Remove duplicates and construct tag arguments
declare -A UNIQUE_TAGS
for tag in "${TAGS[@]}"; do
    UNIQUE_TAGS["$tag"]=1
done

TAG_ARGS=""
for tag in "${!UNIQUE_TAGS[@]}"; do
    TAG_ARGS="$TAG_ARGS --tag $FULL_IMAGE_NAME:$tag"
done

log "Tags to be applied: ${!UNIQUE_TAGS[*]}"

# Check if Docker Buildx is available
if ! docker buildx version > /dev/null 2>&1; then
    error "Docker Buildx is required but not available"
fi

# Create builder if it doesn't exist
BUILDER_NAME="eduanalytics-builder"
if ! docker buildx ls | grep -q "$BUILDER_NAME"; then
    log "Creating Docker Buildx builder: $BUILDER_NAME"
    if [[ "$DRY_RUN" == false ]]; then
        docker buildx create --name "$BUILDER_NAME" --use
    fi
else
    log "Using existing Docker Buildx builder: $BUILDER_NAME"
    if [[ "$DRY_RUN" == false ]]; then
        docker buildx use "$BUILDER_NAME"
    fi
fi

# Prepare build arguments
BUILD_ARGS=""
BUILD_ARGS="$BUILD_ARGS --build-arg VERSION=$VERSION"
BUILD_ARGS="$BUILD_ARGS --build-arg COMMIT_HASH=$GIT_COMMIT"
BUILD_ARGS="$BUILD_ARGS --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
BUILD_ARGS="$BUILD_ARGS --build-arg GIT_BRANCH=$GIT_BRANCH"

if [[ -n "$GIT_TAG" ]]; then
    BUILD_ARGS="$BUILD_ARGS --build-arg GIT_TAG=$GIT_TAG"
fi

# Prepare docker buildx command
DOCKER_CMD="docker buildx build"
DOCKER_CMD="$DOCKER_CMD --file server/Dockerfile.production"
DOCKER_CMD="$DOCKER_CMD --target production"
DOCKER_CMD="$DOCKER_CMD --platform $PLATFORMS"
DOCKER_CMD="$DOCKER_CMD $TAG_ARGS"
DOCKER_CMD="$DOCKER_CMD $BUILD_ARGS"

if [[ "$NO_CACHE" == true ]]; then
    DOCKER_CMD="$DOCKER_CMD --no-cache"
fi

if [[ "$PUSH" == true ]]; then
    DOCKER_CMD="$DOCKER_CMD --push"
else
    DOCKER_CMD="$DOCKER_CMD --load"
fi

DOCKER_CMD="$DOCKER_CMD ."

# Show what will be executed
log "Docker command to execute:"
echo "$DOCKER_CMD"

if [[ "$DRY_RUN" == true ]]; then
    log "DRY RUN: Command above would be executed"
    exit 0
fi

# Build the image
log "Building Docker image..."
eval "$DOCKER_CMD"

if [[ $? -eq 0 ]]; then
    log "Build completed successfully!"
    
    # Show image information
    if [[ "$PUSH" == false ]]; then
        log "Built images:"
        for tag in "${!UNIQUE_TAGS[@]}"; do
            docker images "$FULL_IMAGE_NAME:$tag" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        done
    else
        log "Images pushed to registry:"
        for tag in "${!UNIQUE_TAGS[@]}"; do
            echo "  $FULL_IMAGE_NAME:$tag"
        done
    fi
    
    # Security scan
    if command -v trivy &> /dev/null && [[ "$PUSH" == false ]]; then
        log "Running security scan with Trivy..."
        trivy image "$FULL_IMAGE_NAME:$VERSION" || warn "Security scan found issues"
    fi
    
    # Size optimization suggestions
    log "Image optimization suggestions:"
    echo "  - Use multi-stage builds (already implemented)"
    echo "  - Minimize layers by combining RUN commands"
    echo "  - Use .dockerignore to exclude unnecessary files"
    echo "  - Consider using distroless or alpine base images"
    
else
    error "Build failed"
fi

log "Build and publish script completed!"

# Cleanup suggestions
if [[ "$PUSH" == false ]]; then
    echo ""
    echo "To push the images to the registry, run:"
    echo "  $0 --version $VERSION --push"
    echo ""
    echo "To clean up local images, run:"
    echo "  docker rmi $FULL_IMAGE_NAME:$VERSION"
fi
