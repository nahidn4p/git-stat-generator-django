#!/bin/bash
# Quick setup script for GitHub Stats Generator

echo "Setting up GitHub Stats Generator..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Build Tailwind CSS
echo "Building Tailwind CSS..."
npm run build-css

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env and add your GitHub token (optional)"
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "Setup complete!"
echo ""
echo "To start the development server:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Don't forget to:"
echo "  1. Edit .env and add your GitHub token (optional)"
echo "  2. Run 'npm run watch-css' in another terminal for CSS auto-rebuild"

