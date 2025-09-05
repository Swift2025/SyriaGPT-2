#!/bin/bash

# Render deployment script for SyriaGPT
set -e

echo "🚀 Starting SyriaGPT deployment to Render..."

# Check if required environment variables are set
required_vars=(
    "GEMINI_API_KEY"
    "JWT_SECRET_KEY"
    "SMTP_HOST"
    "SMTP_USERNAME"
    "SMTP_PASSWORD"
    "GOOGLE_CLIENT_ID"
    "GOOGLE_CLIENT_SECRET"
)

echo "🔍 Checking environment variables..."
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set"
        exit 1
    else
        echo "✅ $var is set"
    fi
done

# Run database migrations
echo "🗄️ Running database migrations..."
alembic upgrade head

# Start the application
echo "🎯 Starting SyriaGPT application..."
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1 --access-log
