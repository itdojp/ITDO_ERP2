#!/bin/bash

# Multi-Stage Build Script for ITDO ERP
# Supports building different stages for development, testing, and production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY=${REGISTRY:-registry.itdo-erp.com}
PROJECT=${PROJECT:-itdo-erp}
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
VERSION=${VERSION:-$(git describe --tags --always 2>/dev/null || echo "latest")}

# Build targets
BACKEND_TARGET=${BACKEND_TARGET:-production}
FRONTEND_TARGET=${FRONTEND_TARGET:-production}

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to build component
build_component() {
    local component=$1
    local target=$2
    local context=$3
    local dockerfile=${4:-Dockerfile}
    
    print_status $BLUE "🔨 Building $component ($target stage)..."
    
    local image_name="$REGISTRY/$PROJECT/$component:$VERSION-$target"
    local latest_tag="$REGISTRY/$PROJECT/$component:$target"
    
    # Build arguments
    local build_args=(
        --build-arg BUILD_DATE="$BUILD_DATE"
        --build-arg VCS_REF="$VCS_REF"
        --build-arg VERSION="$VERSION"
        --target "$target"
        --tag "$image_name"
        --tag "$latest_tag"
    )
    
    # Add component-specific build args
    case $component in
        frontend)
            build_args+=(
                --build-arg VITE_API_URL="${VITE_API_URL:-http://localhost:8000}"
                --build-arg VITE_APP_VERSION="$VERSION"
            )
            ;;
    esac
    
    # Platform support
    if [[ "${MULTI_PLATFORM:-false}" == "true" ]]; then
        build_args+=(--platform linux/amd64,linux/arm64)
        docker buildx create --use --name multiplatform || true
    fi
    
    # Build command
    if [[ "${MULTI_PLATFORM:-false}" == "true" ]]; then
        docker buildx build "${build_args[@]}" --push "$context" -f "$context/$dockerfile"
    else
        docker build "${build_args[@]}" "$context" -f "$context/$dockerfile"
    fi
    
    print_status $GREEN "✅ Successfully built $image_name"
    
    # Security scan if requested
    if [[ "${SECURITY_SCAN:-false}" == "true" && "$target" == "production" ]]; then
        print_status $YELLOW "🔍 Running security scan on $image_name..."
        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy:latest image --format json --output "/tmp/trivy-$component.json" "$image_name" || true
        print_status $GREEN "✅ Security scan completed for $component"
    fi
}

# Function to display usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] COMPONENT...

Multi-stage build script for ITDO ERP components.

COMPONENTS:
    backend        Build backend API service
    frontend       Build frontend web application
    security       Build security scanning image
    all            Build all components (default)

OPTIONS:
    -t, --target TARGET          Build target (development|testing|production)
    -r, --registry REGISTRY      Container registry URL (default: registry.itdo-erp.com)
    -v, --version VERSION        Image version tag (default: git describe)
    --backend-target TARGET      Specific target for backend (overrides --target)
    --frontend-target TARGET     Specific target for frontend (overrides --target)
    --multi-platform             Build for multiple platforms (requires buildx)
    --security-scan             Run security scan after build
    --push                      Push images to registry
    --no-cache                  Build without using cache
    --parallel                  Build components in parallel
    -h, --help                  Show this help message

EXAMPLES:
    $0 backend                           # Build backend production image
    $0 --target development frontend     # Build frontend development image
    $0 --multi-platform all             # Build all components for multiple platforms
    $0 --security-scan --push all       # Build, scan, and push all production images

ENVIRONMENT VARIABLES:
    REGISTRY                    Container registry URL
    VERSION                     Image version tag
    BACKEND_TARGET             Backend build target
    FRONTEND_TARGET            Frontend build target
    VITE_API_URL               Frontend API URL
    MULTI_PLATFORM             Enable multi-platform builds
    SECURITY_SCAN              Enable security scanning
    PUSH_IMAGES                Push images after build
    NO_CACHE                   Disable build cache
    PARALLEL_BUILD             Build components in parallel

EOF
}

# Function to validate prerequisites
check_prerequisites() {
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_status $RED "❌ Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_status $RED "❌ Docker daemon is not running"
        exit 1
    fi
    
    # Check buildx for multi-platform builds
    if [[ "${MULTI_PLATFORM:-false}" == "true" ]]; then
        if ! docker buildx version &> /dev/null; then
            print_status $RED "❌ Docker buildx is required for multi-platform builds"
            exit 1
        fi
    fi
    
    # Check git for version info
    if ! command -v git &> /dev/null; then
        print_status $YELLOW "⚠️ Git not found, using default version"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            BACKEND_TARGET="$2"
            FRONTEND_TARGET="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        --backend-target)
            BACKEND_TARGET="$2"
            shift 2
            ;;
        --frontend-target)
            FRONTEND_TARGET="$2"
            shift 2
            ;;
        --multi-platform)
            MULTI_PLATFORM=true
            shift
            ;;
        --security-scan)
            SECURITY_SCAN=true
            shift
            ;;
        --push)
            PUSH_IMAGES=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --parallel)
            PARALLEL_BUILD=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        backend|frontend|security|all)
            COMPONENTS+=("$1")
            shift
            ;;
        *)
            print_status $RED "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Default to building all components
if [[ ${#COMPONENTS[@]} -eq 0 ]]; then
    COMPONENTS=("all")
fi

# Expand "all" to individual components
if [[ " ${COMPONENTS[*]} " =~ " all " ]]; then
    COMPONENTS=("backend" "frontend" "security")
fi

# Main execution
main() {
    print_status $BLUE "🚀 Starting ITDO ERP Multi-Stage Build"
    print_status $BLUE "Registry: $REGISTRY"
    print_status $BLUE "Version: $VERSION"
    print_status $BLUE "Build Date: $BUILD_DATE"
    print_status $BLUE "VCS Ref: $VCS_REF"
    print_status $BLUE "Components: ${COMPONENTS[*]}"
    
    check_prerequisites
    
    # Build components
    if [[ "${PARALLEL_BUILD:-false}" == "true" ]]; then
        print_status $YELLOW "🔄 Building components in parallel..."
        
        # Start background builds
        pids=()
        for component in "${COMPONENTS[@]}"; do
            case $component in
                backend)
                    build_component backend "$BACKEND_TARGET" ./backend &
                    pids+=($!)
                    ;;
                frontend)
                    build_component frontend "$FRONTEND_TARGET" ./frontend &
                    pids+=($!)
                    ;;
                security)
                    build_component security-scanner production . Dockerfile.security &
                    pids+=($!)
                    ;;
            esac
        done
        
        # Wait for all builds to complete
        for pid in "${pids[@]}"; do
            if wait $pid; then
                print_status $GREEN "✅ Parallel build process $pid completed successfully"
            else
                print_status $RED "❌ Parallel build process $pid failed"
                exit 1
            fi
        done
        
    else
        # Sequential builds
        for component in "${COMPONENTS[@]}"; do
            case $component in
                backend)
                    build_component backend "$BACKEND_TARGET" ./backend
                    ;;
                frontend)
                    build_component frontend "$FRONTEND_TARGET" ./frontend
                    ;;
                security)
                    build_component security-scanner production . Dockerfile.security
                    ;;
                *)
                    print_status $RED "❌ Unknown component: $component"
                    exit 1
                    ;;
            esac
        done
    fi
    
    # Push images if requested
    if [[ "${PUSH_IMAGES:-false}" == "true" ]]; then
        print_status $YELLOW "📤 Pushing images to registry..."
        
        for component in "${COMPONENTS[@]}"; do
            case $component in
                backend)
                    docker push "$REGISTRY/$PROJECT/backend:$VERSION-$BACKEND_TARGET"
                    docker push "$REGISTRY/$PROJECT/backend:$BACKEND_TARGET"
                    ;;
                frontend)
                    docker push "$REGISTRY/$PROJECT/frontend:$VERSION-$FRONTEND_TARGET"
                    docker push "$REGISTRY/$PROJECT/frontend:$FRONTEND_TARGET"
                    ;;
                security)
                    docker push "$REGISTRY/$PROJECT/security-scanner:$VERSION-production"
                    docker push "$REGISTRY/$PROJECT/security-scanner:production"
                    ;;
            esac
        done
        
        print_status $GREEN "✅ All images pushed successfully"
    fi
    
    # Display build summary
    print_status $GREEN "🎉 Multi-stage build completed successfully!"
    print_status $BLUE "📋 Build Summary:"
    
    for component in "${COMPONENTS[@]}"; do
        case $component in
            backend)
                echo "  • Backend ($BACKEND_TARGET): $REGISTRY/$PROJECT/backend:$VERSION-$BACKEND_TARGET"
                ;;
            frontend)
                echo "  • Frontend ($FRONTEND_TARGET): $REGISTRY/$PROJECT/frontend:$VERSION-$FRONTEND_TARGET"
                ;;
            security)
                echo "  • Security Scanner: $REGISTRY/$PROJECT/security-scanner:$VERSION-production"
                ;;
        esac
    done
    
    # Display next steps
    print_status $YELLOW "💡 Next steps:"
    echo "1. Test the built images: docker run <image-name>"
    echo "2. Deploy to development: docker-compose up"
    echo "3. Run security scans: docker run --rm -v \$(pwd):/workspace $REGISTRY/$PROJECT/security-scanner:production"
    echo "4. Push to registry: $0 --push ${COMPONENTS[*]}"
}

# Execute main function
main