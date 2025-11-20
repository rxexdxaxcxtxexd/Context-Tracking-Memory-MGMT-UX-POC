@echo off
REM API Documentation Agent - Windows Setup Script

echo 🚀 Setting up API Documentation Agent on Windows...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed or not in PATH
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Create project directories
echo 📁 Creating project directories...
if not exist "config" mkdir config
if not exist "output" mkdir output
if not exist "specs" mkdir specs
if not exist "logs" mkdir logs
if not exist "templates" mkdir templates
if not exist "tests" mkdir tests
if not exist "output\docs" mkdir output\docs
if not exist "output\sdks" mkdir output\sdks
if not exist "output\tests" mkdir output\tests
if not exist "src\core" mkdir src\core
if not exist "src\generators" mkdir src\generators
if not exist "src\validators" mkdir src\validators
if not exist "src\cli" mkdir src\cli

REM Install Python dependencies
echo 📦 Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Install the package in development mode
echo 📦 Installing API Documentation Agent in development mode...
python -m pip install -e .

REM Install Node.js dependencies
echo 📦 Installing Node.js dependencies...
npm install

REM Install global tools
echo 🛠️ Installing global tools...
npm install -g @redocly/cli@latest
npm install -g @openapitools/openapi-generator-cli@latest

REM Install additional Python tools
echo 🛠️ Installing additional testing tools...
python -m pip install schemathesis

REM Verify installations
echo 🔍 Verifying tool installations...

echo Checking Python...
python --version
if errorlevel 1 echo ❌ Python verification failed

echo Checking Node.js...
node --version  
if errorlevel 1 echo ❌ Node.js verification failed

echo Checking npm...
npm --version
if errorlevel 1 echo ❌ npm verification failed

echo Checking Redoc CLI...
redoc-cli --version
if errorlevel 1 echo ❌ Redoc CLI verification failed

echo Checking OpenAPI Generator...
openapi-generator-cli version
if errorlevel 1 echo ❌ OpenAPI Generator verification failed

echo Checking Schemathesis...
st --version
if errorlevel 1 echo ❌ Schemathesis verification failed

REM Create default configuration if it doesn't exist
if not exist "config\pipeline.yaml" (
    echo 📝 Creating default configuration...
    echo project_name: "api-docs-test" > config\pipeline.yaml
    echo version: "1.0.0" >> config\pipeline.yaml
    echo description: "API Documentation Generation Test Project" >> config\pipeline.yaml
    echo output_formats: ["html", "markdown"] >> config\pipeline.yaml
    echo target_languages: ["python", "javascript", "java"] >> config\pipeline.yaml
    echo parallel_execution: true >> config\pipeline.yaml
    echo max_workers: 2 >> config\pipeline.yaml
    echo. >> config\pipeline.yaml
    echo openapi_generator: >> config\pipeline.yaml
    echo   java_opts: "-Xmx1024M" >> config\pipeline.yaml
    echo   default_package_name: "api_client" >> config\pipeline.yaml
    echo   additional_properties: {} >> config\pipeline.yaml
    echo. >> config\pipeline.yaml
    echo redoc: >> config\pipeline.yaml
    echo   theme: "default" >> config\pipeline.yaml
    echo   hide_download_button: false >> config\pipeline.yaml
    echo   expand_responses: ["200", "201"] >> config\pipeline.yaml
    echo. >> config\pipeline.yaml
    echo schemathesis: >> config\pipeline.yaml
    echo   max_examples: 50 >> config\pipeline.yaml
    echo   workers: 1 >> config\pipeline.yaml
    echo   request_timeout: 10 >> config\pipeline.yaml
)

REM Create sample OpenAPI spec if it doesn't exist
if not exist "specs\petstore.yaml" (
    echo 📝 Creating sample OpenAPI specification...
    echo openapi: 3.0.0 > specs\petstore.yaml
    echo info: >> specs\petstore.yaml
    echo   title: Sample API >> specs\petstore.yaml
    echo   version: 1.0.0 >> specs\petstore.yaml
    echo   description: A sample API for testing >> specs\petstore.yaml
    echo paths: >> specs\petstore.yaml
    echo   /pets: >> specs\petstore.yaml
    echo     get: >> specs\petstore.yaml
    echo       summary: List pets >> specs\petstore.yaml
    echo       responses: >> specs\petstore.yaml
    echo         '200': >> specs\petstore.yaml
    echo           description: A list of pets >> specs\petstore.yaml
    echo           content: >> specs\petstore.yaml
    echo             application/json: >> specs\petstore.yaml
    echo               schema: >> specs\petstore.yaml
    echo                 type: array >> specs\petstore.yaml
    echo                 items: >> specs\petstore.yaml
    echo                   $ref: '#/components/schemas/Pet' >> specs\petstore.yaml
    echo components: >> specs\petstore.yaml
    echo   schemas: >> specs\petstore.yaml
    echo     Pet: >> specs\petstore.yaml
    echo       type: object >> specs\petstore.yaml
    echo       properties: >> specs\petstore.yaml
    echo         id: >> specs\petstore.yaml
    echo           type: integer >> specs\petstore.yaml
    echo         name: >> specs\petstore.yaml
    echo           type: string >> specs\petstore.yaml
    echo         status: >> specs\petstore.yaml
    echo           type: string >> specs\petstore.yaml
    echo           enum: [available, pending, sold] >> specs\petstore.yaml
)

echo.
echo ✅ Setup completed successfully!
echo.
echo Next steps:
echo   1. Run a test: python -m src.core.pipeline specs\petstore.yaml
echo   2. Check the output in the 'output\' directory
echo   3. For help: python -m src.core.pipeline --help
echo.
pause