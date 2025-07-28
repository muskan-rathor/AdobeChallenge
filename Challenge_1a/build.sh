#!/bin/bash
# Adobe India Hackathon 2025 - Challenge 1a Build Script
# Quick setup and testing for the PDF processing solution

set -e  # Exit on any error

echo "🚀 Adobe India Hackathon 2025 - Challenge 1a Setup"
echo "=================================================="

# Step 1: Validate environment
echo "📋 Step 1: Validating environment..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi
echo "✅ Docker available: $(docker --version)"

# Step 2: Run tests
echo "\n📋 Step 2: Running validation tests..."
if command -v python3 &> /dev/null; then
    python3 test_solution.py
else
    echo "⚠ Python3 not available for testing, skipping validation"
fi

# Step 3: Build Docker container
echo "\n📋 Step 3: Building Docker container..."
echo "Building for AMD64 platform (hackathon requirement)..."
docker build --platform linux/amd64 -t pdf-processor .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
else
    echo "❌ Docker build failed!"
    exit 1
fi

# Step 4: Setup directories
echo "\n📋 Step 4: Setting up directories..."
mkdir -p input output
echo "✅ Input and output directories created"

# Step 5: Provide usage instructions
echo "\n🎯 READY TO PROCESS PDFs!"
echo "=========================="
echo
echo "1. Copy your PDF files to the input directory:"
echo "   cp your-pdfs/*.pdf input/"
echo
echo "2. Run the processing:"
echo "   docker run --rm \\"
echo "     -v \$(pwd)/input:/app/input:ro \\"
echo "     -v \$(pwd)/output:/app/output \\"
echo "     --network none \\"
echo "     pdf-processor"
echo
echo "3. Check results:"
echo "   ls output/"
echo "   cat output/yourfile.json"
echo
echo "🏆 Solution ready for Adobe India Hackathon 2025!"