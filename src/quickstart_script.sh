#!/bin/bash

# Inglish Translator Quick Start Script

echo "=================================="
echo "Inglish Translator - Quick Start"
echo "=================================="
echo ""

# Check Python version
echo "[1/5] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment
echo ""
echo "[2/5] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "[3/5] Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "[4/5] Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "[5/5] Setting up directories..."
mkdir -p data/glossaries
mkdir -p data/patterns
mkdir -p data/datasets/{train,eval,test}
mkdir -p models
mkdir -p results
mkdir -p logs

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "  1. Activate virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run examples:"
echo "     python examples/basic_usage.py"
echo ""
echo "  3. Run benchmark:"
echo "     make benchmark"
echo ""
echo "  4. Run tests:"
echo "     make test"
echo ""
echo "For more commands, run: make help"
echo ""