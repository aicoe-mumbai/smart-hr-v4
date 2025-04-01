#!/bin/bash

# Set error handling
set -e

echo "🚀 Starting Smart-HR Production Deployment"

# Activate Python virtual environment
source ~/smart-hr-v4/smart-env/bin/activate

# Navigate to the backend and start Gunicorn (Django)

echo "🔄 Starting Django Backend..."
cd ~/smart-hr-v4/backend/project
pip install -r ~/smart-hr-v4/requirements.txt  # Ensure dependencies are installed
pm2 start uvicorn --name "backend" --interpreter ~/smart-hr-v4/smart-env/bin/python -- project.asgi:application --host 0.0.0.0 --port 8000 --workers 4

# Navigate to the frontend and build React
echo "🔄 Starting React Frontend..."
cd ~/smart-hr-v4/frontend/my-app
npm install  # Ensure dependencies are installed
npm run build  # Build the production files
pm2 serve build/ 3000 --spa --name "frontend"

# Save PM2 process so it restarts automatically
pm2 save

echo "✅ Deployment completed successfully!"
