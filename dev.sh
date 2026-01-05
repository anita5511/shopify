#!/bin/bash

# Development helper script for common tasks

case "$1" in
  start)
    echo "Starting services..."
    docker-compose up -d
    ;;
    
  stop)
    echo "Stopping services..."
    docker-compose down
    ;;
    
  restart)
    echo "Restarting services..."
    docker-compose restart
    ;;
    
  logs)
    if [ -z "$2" ]; then
      docker-compose logs -f
    else
      docker-compose logs -f "$2"
    fi
    ;;
    
  test)
    echo "Running tests..."
    if [ "$2" = "rails" ]; then
      docker-compose exec rails_api bundle exec rspec
    elif [ "$2" = "python" ]; then
      docker-compose exec ai_service pytest -v
    else
      echo "Running all tests..."
      docker-compose exec rails_api bundle exec rspec
      docker-compose exec ai_service pytest -v
    fi
    ;;
    
  console)
    if [ "$2" = "rails" ]; then
      docker-compose exec rails_api rails console
    elif [ "$2" = "python" ]; then
      docker-compose exec ai_service python
    else
      echo "Specify: rails or python"
    fi
    ;;
    
  reset)
    echo "Resetting database..."
    docker-compose exec rails_api rails db:drop db:create db:migrate db:seed
    ;;
    
  rebuild)
    echo "Rebuilding services..."
    docker-compose down -v
    docker-compose up --build -d
    ;;
    
  query)
    if [ -z "$2" ]; then
      echo "Usage: ./dev.sh query \"Your question here\""
      exit 1
    fi
    
    curl -X POST http://localhost:3000/api/v1/questions \
      -H "Content-Type: application/json" \
      -d "{\"store_id\":\"demo-store.myshopify.com\",\"question\":\"$2\"}"
    echo ""
    ;;
    
  health)
    echo "Checking health..."
    echo "Rails API:"
    curl -s http://localhost:3000/health | python -m json.tool
    echo -e "\nPython AI Service:"
    curl -s http://localhost:8000/health | python -m json.tool
    ;;
    
  *)
    echo "Shopify Analytics AI - Development Helper"
    echo ""
    echo "Usage: ./dev.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start              Start all services"
    echo "  stop               Stop all services"
    echo "  restart            Restart all services"
    echo "  logs [service]     View logs (rails_api, ai_service, or all)"
    echo "  test [rails|python] Run tests"
    echo "  console [rails|python] Open interactive console"
    echo "  reset              Reset database"
    echo "  rebuild            Rebuild all containers"
    echo "  query \"question\"   Send a query to the API"
    echo "  health             Check health of all services"
    echo ""
    echo "Examples:"
    echo "  ./dev.sh start"
    echo "  ./dev.sh logs rails_api"
    echo "  ./dev.sh test python"
    echo "  ./dev.sh query \"What were my top products last week?\""
    echo "  ./dev.sh health"
    ;;
esac
