#!/bin/bash
# API Documentation Agent - Setup Script

set -e

echo "🚀 Setting up API Documentation Agent..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Windows (WSL or Git Bash)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || -n "$WSL_DISTRO_NAME" ]]; then
    print_status "Detected Windows environment"
    WINDOWS=true
else
    WINDOWS=false
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
print_status "Checking system requirements..."

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Found Python $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_VERSION=$(python --version | cut -d' ' -f2)
    print_status "Found Python $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    print_error "Python 3.9+ is required but not found"
    exit 1
fi

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version)
    print_status "Found Node.js $NODE_VERSION"
else
    print_error "Node.js 18+ is required but not found"
    print_status "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check npm
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    print_status "Found npm $NPM_VERSION"
else
    print_error "npm is required but not found"
    exit 1
fi

# Check Java (required for OpenAPI Generator)
if command_exists java; then
    JAVA_VERSION=$(java -version 2>&1 | head -n1 | cut -d'"' -f2)
    print_status "Found Java $JAVA_VERSION"
else
    print_warning "Java not found - OpenAPI Generator may not work properly"
    print_status "Please install Java 8+ from https://adoptium.net/"
fi

# Create project directories
print_status "Creating project directories..."
mkdir -p config output specs logs templates tests
mkdir -p output/{docs,sdks,tests} 
mkdir -p src/{core,generators,validators,cli}

# Install Python dependencies
print_status "Installing Python dependencies..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r requirements.txt

# Install the package in development mode
print_status "Installing API Documentation Agent in development mode..."
$PYTHON_CMD -m pip install -e .

# Install Node.js tools
print_status "Installing Node.js tools..."
npm install

# Install global tools
print_status "Installing global tools..."
npm install -g @redocly/cli@latest
npm install -g @openapitools/openapi-generator-cli@latest

# Install additional tools
print_status "Installing additional testing tools..."
$PYTHON_CMD -m pip install schemathesis

# Install Step CI if not on Windows (has issues on Windows)
if [ "$WINDOWS" = false ]; then
    if command_exists npm; then
        npm install -g step-ci
    fi
else
    print_warning "Skipping Step CI installation on Windows (compatibility issues)"
fi

# Verify installations
print_status "Verifying tool installations..."

# Create a simple verification script
cat > verify_tools.py << 'EOF'
#!/usr/bin/env python3
import subprocess
import sys

def check_tool(name, command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: Failed")
            return False
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)}")
        return False

tools = [
    ("Python", [sys.executable, "--version"]),
    ("Node.js", ["node", "--version"]),
    ("npm", ["npm", "--version"]),
    ("Redoc CLI", ["redoc-cli", "--version"]),
    ("OpenAPI Generator", ["openapi-generator-cli", "version"]),
    ("Schemathesis", ["st", "--version"]),
]

print("Verifying tool installations:")
success_count = 0
for name, command in tools:
    if check_tool(name, command):
        success_count += 1

print(f"\n{success_count}/{len(tools)} tools verified successfully")

if success_count == len(tools):
    print("🎉 All tools installed successfully!")
    sys.exit(0)
else:
    print("⚠️  Some tools failed verification")
    sys.exit(1)
EOF

$PYTHON_CMD verify_tools.py
VERIFICATION_RESULT=$?

# Clean up verification script
rm verify_tools.py

# Create default configuration
print_status "Creating default configuration..."
if [ ! -f "config/pipeline.yaml" ]; then
    cat > config/pipeline.yaml << 'EOF'
project_name: "api-docs-test"
version: "1.0.0"
description: "API Documentation Generation Test Project"
output_formats: ["html", "markdown"]
target_languages: ["python", "javascript", "java"]
parallel_execution: true
max_workers: 2

openapi_generator:
  java_opts: "-Xmx1024M"
  default_package_name: "api_client"
  git_user_id: "api-team"
  git_repo_id: "api-client"
  additional_properties: {}

redoc:
  theme: "default"
  hide_download_button: false
  disable_search: false
  expand_responses: ["200", "201"]
  required_props_first: true

schemathesis:
  max_examples: 50
  workers: 1
  hypothesis_phases: ["explicit", "reuse", "generate"]
  checks: ["not_a_server_error", "status_code_conformance"]
  request_timeout: 10

quality:
  min_coverage: 0.8
  check_security: true
  check_performance: true
EOF
fi

# Create sample OpenAPI spec if it doesn't exist
if [ ! -f "specs/petstore.yaml" ]; then
    print_status "Creating sample OpenAPI specification..."
    curl -s -o specs/petstore.yaml https://petstore.swagger.io/v2/swagger.yaml || {
        print_warning "Could not download sample spec, creating minimal one..."
        cat > specs/petstore.yaml << 'EOF'
openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
  description: A sample API for testing
paths:
  /pets:
    get:
      summary: List pets
      responses:
        '200':
          description: A list of pets
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Pet'
components:
  schemas:
    Pet:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        status:
          type: string
          enum: [available, pending, sold]
EOF
    }
fi

# Final status
echo ""
if [ $VERIFICATION_RESULT -eq 0 ]; then
    print_status "🎉 Setup completed successfully!"
    echo ""
    print_status "Next steps:"
    echo "  1. Run a test: python -m src.core.pipeline specs/petstore.yaml"
    echo "  2. Or use Docker: docker-compose up api-docs-agent"
    echo "  3. Check the output in the 'output/' directory"
    echo ""
    print_status "For help: python -m src.core.pipeline --help"
else
    print_warning "Setup completed with some issues. Please check the errors above."
    echo ""
    print_status "You can still try running: python -m src.core.pipeline --help"
fi