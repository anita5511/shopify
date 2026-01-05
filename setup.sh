#!/bin/bash

echo "========================================="
echo "Shopify Analytics AI App Setup"
echo "========================================="
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Create .env files if they don't exist
echo "Setting up environment files..."

if [ ! -f rails_api/.env ]; then
    cp rails_api/.env.example rails_api/.env
    echo "✓ Created rails_api/.env"
else
    echo "✓ rails_api/.env already exists"
fi

if [ ! -f ai_service/.env ]; then
    cp ai_service/.env.example ai_service/.env
    echo "✓ Created ai_service/.env"
else
    echo "✓ ai_service/.env already exists"
fi

echo ""
echo "Building and starting services..."
echo "This may take a few minutes on first run..."
echo ""

# Build and start services
docker-compose up --build -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "rails_api.*Up"; then
    echo "✓ Rails API is running on http://localhost:3000"
else
    echo "❌ Rails API failed to start"
    docker-compose logs rails_api
    exit 1
fi

if docker-compose ps | grep -q "ai_service.*Up"; then
    echo "✓ Python AI Service is running on http://localhost:8000"
else
    echo "❌ Python AI Service failed to start"
    docker-compose logs ai_service
    exit 1
fi

echo ""
echo "Creating demo store..."
docker-compose exec -T rails_api rails runner "
  Shop.find_or_create_by!(shop_domain: 'demo-store.myshopify.com') do |shop|
    shop.access_token = 'mock_token_12345'
    shop.shop_name = 'Demo Store'
  end
  puts 'Demo store created successfully'
"

echo ""
echo "========================================="
echo "✓ Setup Complete!"
echo "========================================="
echo ""
echo "Services are running:"
echo "  - Rails API: http://localhost:3000"
echo "  - Python AI: http://localhost:8000"
echo ""
echo "Test the API:"
echo "  curl http://localhost:3000/health"
echo ""
echo "Ask a question:"
echo '  curl -X POST http://localhost:3000/api/v1/questions \'
echo '    -H "Content-Type: application/json" \'
echo '    -d '"'"'{"store_id": "demo-store.myshopify.com", "question": "What were my top 5 selling products last week?"}'"'"
echo ""
echo "View logs:"
echo "  docker-compose logs -f rails_api"
echo "  docker-compose logs -f ai_service"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
echo "See API_EXAMPLES.md for more examples!"
echo "========================================="
