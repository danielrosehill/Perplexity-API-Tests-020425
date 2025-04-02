#!/bin/bash
# Helper script to run the API tests

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found."
    echo "Please create a .env file with your API keys based on .env.example"
    echo "cp .env.example .env"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Run the tests
echo "Running API tests..."
python3 test_apis.py

# Check if tests completed successfully
if [ $? -eq 0 ]; then
    echo "Tests completed successfully."
    echo "Results are saved in the outputs directory."
else
    echo "Error: Tests failed to complete."
    exit 1
fi
