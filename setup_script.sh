#!/bin/bash
# setup.sh - Quick setup script for Healthcare AI Assistant

set -e

echo "🏥 Healthcare AI Assistant Setup Script"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ pip3 found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "🔧 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "🔧 Creating directories..."
mkdir -p uploads
mkdir -p healthcare_vectordb
mkdir -p logs
mkdir -p templates
mkdir -p static/{css,js,images}

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your OpenAI API key"
else
    echo "✅ .env file already exists"
fi

# Check if OpenAI API key is set
if [ -f ".env" ]; then
    source .env
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
        echo "⚠️  OpenAI API key not set in .env file"
        echo "   Please edit .env and add your OpenAI API key"
    else
        echo "✅ OpenAI API key configured"
    fi
fi

# Create HTML template if it doesn't exist
if [ ! -f "templates/index.html" ]; then
    echo "⚠️  HTML template not found. Please make sure to create templates/index.html"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Ensure templates/index.html exists"
echo "3. Run the application:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "🌐 The application will be available at: http://localhost:5000"
echo ""
echo "📚 For more information, see README.md"