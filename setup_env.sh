#!/bin/bash

# Setup script for CrossSolver optimization environment

echo "Setting up CrossSolver optimization environment..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

echo ""
echo "Environment setup complete!"
echo ""
echo "To activate the environment, run:"
echo "source venv/bin/activate"
echo ""
echo "To test the optimization model, run:"
echo "cd server && python test.py"
echo ""
echo "Note: You'll need a Gurobi license to run the optimization model."
echo "If you don't have one, you can get a free academic license from:"
echo "https://www.gurobi.com/academia/academic-program-and-licenses/" 