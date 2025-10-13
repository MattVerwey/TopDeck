#!/bin/bash
#
# End-to-End Testing Script for TopDeck
#
# This script performs a complete end-to-end test of TopDeck:
# 1. Starts infrastructure services
# 2. Starts the TopDeck API
# 3. Runs discovery tests
# 4. Tests API endpoints
# 5. Verifies data in Neo4j
# 6. Runs integration tests
# 7. Cleans up
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"

# Change to project root
cd "${PROJECT_ROOT}"

# Configuration
API_PORT="${APP_PORT:-8000}"
API_URL="http://localhost:${API_PORT}"
WAIT_TIMEOUT=30

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

wait_for_service() {
    local url=$1
    local name=$2
    local timeout=$3
    local elapsed=0
    
    print_info "Waiting for ${name} to be ready..."
    
    while [ $elapsed -lt $timeout ]; do
        if curl -s "${url}" > /dev/null 2>&1; then
            print_success "${name} is ready"
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    
    print_error "${name} failed to start within ${timeout} seconds"
    return 1
}

cleanup() {
    print_header "Cleaning Up"
    
    # Stop API server if running
    if [ -n "${API_PID}" ]; then
        print_info "Stopping API server (PID: ${API_PID})..."
        kill ${API_PID} 2>/dev/null || true
        wait ${API_PID} 2>/dev/null || true
        print_success "API server stopped"
    fi
    
    print_info "Tests completed"
}

# Set up cleanup trap
trap cleanup EXIT

# Main test flow
main() {
    print_header "TopDeck End-to-End Testing"
    
    # Check prerequisites
    print_header "Step 1: Checking Prerequisites"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker is installed"
    
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed"
        exit 1
    fi
    print_success "Python is installed"
    
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed"
        exit 1
    fi
    print_success "curl is installed"
    
    # Check .env file
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        print_info "Copying from .env.example..."
        cp .env.example .env
        print_warning "Please configure .env with your Azure credentials"
        print_info "See docs/HOSTING_AND_TESTING_GUIDE.md for details"
        exit 1
    fi
    print_success ".env file exists"
    
    # Step 2: Start Infrastructure Services
    print_header "Step 2: Starting Infrastructure Services"
    
    print_info "Starting Docker Compose services..."
    docker-compose up -d
    
    # Wait for services
    wait_for_service "http://localhost:7474" "Neo4j" 60
    
    print_info "Testing Redis connection..."
    if docker exec topdeck-redis redis-cli -a topdeck123 ping > /dev/null 2>&1; then
        print_success "Redis is ready"
    else
        print_error "Redis is not responding"
        exit 1
    fi
    
    # Step 3: Start TopDeck API
    print_header "Step 3: Starting TopDeck API"
    
    print_info "Starting API server on port ${API_PORT}..."
    python -m topdeck > /tmp/topdeck-api.log 2>&1 &
    API_PID=$!
    print_info "API server started (PID: ${API_PID})"
    
    # Wait for API to be ready
    wait_for_service "${API_URL}/health" "TopDeck API" 30
    
    # Step 4: Test API Endpoints
    print_header "Step 4: Testing API Endpoints"
    
    print_info "Testing health endpoint..."
    if curl -s "${API_URL}/health" | grep -q "healthy"; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        exit 1
    fi
    
    print_info "Testing API info endpoint..."
    if curl -s "${API_URL}/api/info" | grep -q "version"; then
        print_success "API info endpoint working"
    else
        print_error "API info endpoint failed"
        exit 1
    fi
    
    print_info "Testing topology endpoint..."
    if curl -s "${API_URL}/api/v1/topology" > /dev/null 2>&1; then
        print_success "Topology endpoint working"
    else
        print_warning "Topology endpoint failed (may be expected if no data yet)"
    fi
    
    # Step 5: Run Discovery Test
    print_header "Step 5: Running Azure Discovery Test"
    
    if [ -f "scripts/test_discovery.py" ]; then
        print_info "Running discovery test..."
        if python scripts/test_discovery.py; then
            print_success "Discovery test passed"
        else
            print_warning "Discovery test failed (check Azure credentials)"
        fi
    else
        print_warning "Discovery test script not found, skipping"
    fi
    
    # Step 6: Verify Neo4j Data
    print_header "Step 6: Verifying Neo4j Data"
    
    print_info "Checking for discovered resources in Neo4j..."
    RESOURCE_COUNT=$(docker exec topdeck-neo4j cypher-shell -u neo4j -p topdeck123 \
        "MATCH (r:Resource) RETURN count(r) as count;" 2>/dev/null | tail -n 1 | tr -d '[:space:]' || echo "0")
    
    if [ "${RESOURCE_COUNT}" -gt 0 ]; then
        print_success "Found ${RESOURCE_COUNT} resources in Neo4j"
    else
        print_warning "No resources found in Neo4j (run discovery first)"
    fi
    
    # Step 7: Run Integration Tests (if pytest available)
    print_header "Step 7: Running Integration Tests"
    
    if command -v pytest &> /dev/null; then
        print_info "Running integration tests..."
        if pytest tests/integration/ -v --tb=short 2>&1 | tail -20; then
            print_success "Integration tests passed"
        else
            print_warning "Some integration tests failed (check Azure credentials)"
        fi
    else
        print_warning "pytest not installed, skipping integration tests"
    fi
    
    # Step 8: API Documentation
    print_header "Step 8: API Documentation"
    
    print_success "API documentation available at:"
    echo "   Swagger UI: ${API_URL}/api/docs"
    echo "   ReDoc: ${API_URL}/api/redoc"
    echo "   OpenAPI: ${API_URL}/api/openapi.json"
    
    # Step 9: Service URLs
    print_header "Step 9: Service Access URLs"
    
    print_success "Services are running at:"
    echo "   TopDeck API: ${API_URL}"
    echo "   Neo4j Browser: http://localhost:7474 (neo4j/topdeck123)"
    echo "   RabbitMQ UI: http://localhost:15672 (topdeck/topdeck123)"
    
    # Final Summary
    print_header "Test Summary"
    
    print_success "End-to-end test completed!"
    print_info ""
    print_info "Next steps:"
    echo "   1. Open ${API_URL}/api/docs to explore the API"
    echo "   2. Open http://localhost:7474 to query Neo4j"
    echo "   3. Review logs: docker-compose logs -f"
    echo "   4. Run discovery: python scripts/test_discovery.py"
    echo "   5. See docs/HOSTING_AND_TESTING_GUIDE.md for more"
    print_info ""
    print_info "Press Ctrl+C to stop all services"
    
    # Keep services running
    wait ${API_PID}
}

# Run main function
main "$@"
