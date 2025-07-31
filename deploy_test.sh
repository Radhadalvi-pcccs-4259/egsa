#!/bin/bash

# Local deployment test script
# This script simulates what the GitHub Actions will do

echo "🧪 Testing local deployment process..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: This script should be run from the myproject directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r ../requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser
echo "👤 Creating admin user..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Admin user created: admin/admin123')
else:
    print('Admin user already exists: admin/admin123')
"

# Test the server
echo "🧪 Testing server startup..."
python manage.py check

echo "✅ Local deployment test completed!"
echo "🚀 You can now run: python manage.py runserver"
echo "👤 Admin login: admin / admin123"
