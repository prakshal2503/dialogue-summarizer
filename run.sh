#!/bin/bash
# ============================================================
# Dialogue Summarizer — Setup & Run Script
# ============================================================

echo ""
echo "⬡  DIALOGUE SUMMARIZER — Cloud Framework"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+"
    exit 1
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install pip."
    exit 1
fi

# Check MongoDB
echo "🔍 Checking MongoDB connection..."
python3 -c "
from pymongo import MongoClient
try:
    c = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=3000)
    c.server_info()
    print('✅ MongoDB is running')
except Exception as e:
    print(f'⚠️  MongoDB not detected: {e}')
    print('   Make sure MongoDB is running: sudo systemctl start mongod')
    print('   Or set MONGODB_URI env variable for Atlas')
" 2>/dev/null

echo ""
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt -q

echo ""
echo "🔧 Running Django migrations (for sessions)..."
python3 manage.py migrate --run-syncdb 2>/dev/null || python3 manage.py migrate

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo ""
echo "🔐 Admin credentials:"
echo "   Username: admin"
echo "   Password: Admin@123!  (set ADMIN_PASSWORD env var to change)"
echo ""
echo "🌐 Starting development server..."
echo "   http://localhost:8000"
echo ""
echo "   Press CTRL+C to stop."
echo "=========================================="
echo ""

# Environment variables (optional)
# export MONGODB_URI="mongodb://localhost:27017/"
# export MONGODB_DATABASE="dialogue_summarizer_db"
# export ADMIN_PASSWORD="YourSecurePassword!"
# export RECAPTCHA_PUBLIC_KEY="your_site_key"
# export RECAPTCHA_PRIVATE_KEY="your_secret_key"

python3 manage.py runserver 0.0.0.0:8000
