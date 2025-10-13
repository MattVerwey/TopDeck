#!/bin/bash
#
# End-to-End Risk Analysis Test
#
# This script demonstrates the complete risk analysis workflow:
# 1. Start infrastructure services
# 2. Create network graph demo data
# 3. Run risk analysis on demo data
# 4. Show dependencies in code, portal, and AKS nodes
# 5. Display step-by-step instructions
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"

# Change to project root
cd "${PROJECT_ROOT}"

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_step() {
    echo ""
    echo -e "${CYAN}📍 STEP $1: $2${NC}"
    echo -e "${CYAN}----------------------------------------${NC}"
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
    echo -e "  $1"
}

wait_for_service() {
    local url=$1
    local name=$2
    local timeout=$3
    local elapsed=0
    
    echo -e "  Waiting for ${name} to be ready..."
    
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

# Main execution
main() {
    print_header "🎯 TOPDECK RISK ANALYSIS - END-TO-END TEST"
    
    echo "This test demonstrates:"
    print_info "• Network graph demo with dependencies"
    print_info "• Risk analysis on AKS, pods, and other resources"
    print_info "• SPOF detection"
    print_info "• Blast radius calculation"
    print_info "• Complete application workflow"
    echo ""
    
    # Step 1: Check prerequisites
    print_step "1" "Checking Prerequisites"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker is installed"
    
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed"
        exit 1
    fi
    print_success "Python is installed ($(python --version))"
    
    # Step 2: Start Infrastructure Services
    print_step "2" "Starting Infrastructure Services"
    
    print_info "Starting Neo4j, Redis, and RabbitMQ..."
    docker-compose up -d
    
    print_info "Waiting for services to be ready..."
    wait_for_service "http://localhost:7474" "Neo4j" 60
    
    print_info "Testing Neo4j connectivity..."
    sleep 5  # Give Neo4j extra time to fully initialize
    
    if docker exec topdeck-neo4j cypher-shell -u neo4j -p topdeck123 "RETURN 1 as test;" > /dev/null 2>&1; then
        print_success "Neo4j is responding"
    else
        print_error "Neo4j is not responding properly"
        exit 1
    fi
    
    # Step 3: Install Python dependencies
    print_step "3" "Installing Python Dependencies"
    
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python -m venv venv
    fi
    
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    print_info "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    print_success "Dependencies installed"
    
    # Step 4: Create Network Graph Demo Data
    print_step "4" "Creating Network Graph Demo Data"
    
    print_info "Running demo_network_graph.py..."
    echo ""
    python scripts/demo_network_graph.py
    echo ""
    
    # Verify demo data was created
    DEMO_COUNT=$(docker exec topdeck-neo4j cypher-shell -u neo4j -p topdeck123 \
        "MATCH (n) WHERE n.demo = true RETURN count(n) as count;" 2>/dev/null | tail -n 1 | tr -d '[:space:]' || echo "0")
    
    if [ "$DEMO_COUNT" -gt 0 ]; then
        print_success "Demo data created: $DEMO_COUNT resources"
    else
        print_error "Failed to create demo data"
        exit 1
    fi
    
    # Step 5: Run Risk Analysis Demo
    print_step "5" "Running Risk Analysis on Demo Data"
    
    print_info "Demonstrating risk analysis features..."
    echo ""
    python scripts/demo_risk_analysis.py
    echo ""
    
    # Step 6: Run Demo Tests
    print_step "6" "Running Verification Tests"
    
    if command -v pytest &> /dev/null; then
        print_info "Running network graph demo tests..."
        echo ""
        pytest tests/demo/test_network_graph_demo.py -v --tb=short
        echo ""
        print_success "Tests completed"
    else
        print_warning "pytest not installed, skipping tests"
    fi
    
    # Step 7: Summary and Next Steps
    print_step "7" "Test Summary"
    
    print_success "End-to-end risk analysis test completed!"
    echo ""
    echo "What was demonstrated:"
    print_info "✅ Network graph with Azure resources (AKS, pods, app gateway, storage)"
    print_info "✅ Dependency relationships (DEPENDS_ON, ROUTES_TO, CONTAINS, etc.)"
    print_info "✅ Risk analysis on multiple resource types"
    print_info "✅ SPOF (Single Point of Failure) detection"
    print_info "✅ Blast radius calculation"
    print_info "✅ Risk scoring and recommendations"
    echo ""
    
    print_header "📚 NEXT STEPS - How to Use TopDeck"
    
    echo "1️⃣  Explore Data in Neo4j Browser:"
    print_info "   URL: http://localhost:7474"
    print_info "   Login: neo4j / topdeck123"
    print_info ""
    print_info "   Try these queries:"
    print_info "   • View all demo resources:"
    print_info "     MATCH (n) WHERE n.demo = true RETURN n LIMIT 50"
    print_info ""
    print_info "   • View dependency graph:"
    print_info "     MATCH path = (n)-[r]->(m) WHERE n.demo = true AND m.demo = true RETURN path"
    print_info ""
    print_info "   • Find resources with most dependents:"
    print_info "     MATCH (r:Resource)<-[:DEPENDS_ON]-(d)"
    print_info "     WHERE r.demo = true"
    print_info "     RETURN r.name, r.resource_type, count(d) as dependents"
    print_info "     ORDER BY dependents DESC"
    echo ""
    
    echo "2️⃣  Start TopDeck API Server:"
    print_info "   python -m topdeck"
    print_info ""
    print_info "   Then access:"
    print_info "   • API Docs: http://localhost:8000/api/docs"
    print_info "   • Health Check: http://localhost:8000/health"
    echo ""
    
    echo "3️⃣  Use Risk Analysis API:"
    print_info "   Get risk assessment:"
    print_info "   curl http://localhost:8000/api/v1/risk/resources/{resource_id}"
    print_info ""
    print_info "   List SPOFs:"
    print_info "   curl http://localhost:8000/api/v1/risk/spof"
    print_info ""
    print_info "   Calculate blast radius:"
    print_info "   curl http://localhost:8000/api/v1/risk/blast-radius/{resource_id}"
    echo ""
    
    echo "4️⃣  Python SDK Examples:"
    print_info "   See examples in PHASE_3_README.md"
    print_info "   • Risk assessment"
    print_info "   • SPOF detection"
    print_info "   • Blast radius calculation"
    print_info "   • Failure simulation"
    echo ""
    
    echo "5️⃣  Run Integration Tests:"
    print_info "   pytest tests/analysis/ -v"
    print_info "   pytest tests/demo/ -v"
    echo ""
    
    echo "6️⃣  View Documentation:"
    print_info "   • PHASE_3_README.md - Risk Analysis Quick Start"
    print_info "   • PHASE_3_RISK_ANALYSIS_COMPLETION.md - Complete docs"
    print_info "   • QUICK_START.md - General TopDeck guide"
    echo ""
    
    print_header "✅ TEST COMPLETE"
    
    echo "Services are still running. To stop them:"
    print_info "docker-compose down"
    echo ""
    
    echo "To restart the demo:"
    print_info "./scripts/e2e_risk_analysis_test.sh"
    echo ""
}

# Run main function
main "$@"
