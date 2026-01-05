# AI-Powered Shopify Analytics App

A two-service architecture implementing an AI-powered analytics system for Shopify stores. Users can ask natural language questions about their store data, and the system translates these into ShopifyQL queries, executes them, and returns business-friendly answers.

## Architecture

This application consists of:
- **Rails API Gateway** (`/rails_api`): API-only Rails app handling authentication, validation, and request routing
- **Python AI Service** (`/ai_service`): FastAPI service with LLM-powered agent for intent classification, ShopifyQL generation, and answer formatting

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed design documentation.

## Prerequisites

- Docker & Docker Compose
- (Optional) Ruby 3.2+, Rails 7, PostgreSQL for local development
- (Optional) Python 3.11+ for local development

## Quick Start

### 1. Clone and Configure

```bash
# Copy environment files
cp rails_api/.env.example rails_api/.env
cp ai_service/.env.example ai_service/.env
```

### 2. Start Services

```bash
docker-compose up --build
```

This will:
- Build both services
- Start PostgreSQL database
- Run Rails migrations
- Start Rails API on port 3000
- Start Python AI service on port 8000

### 3. Initialize Sample Store (Optional)

```bash
# Create a mock store in the database
docker-compose exec rails_api rails runner "Shop.create!(shop_domain: 'demo-store.myshopify.com', access_token: 'mock_token_12345', shop_name: 'Demo Store')"
```

### 4. Test the API

```bash
# Health check
curl http://localhost:3000/health

# Ask a question
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "What were my top 5 selling products last week?"
  }'
```

See [API_EXAMPLES.md](./API_EXAMPLES.md) for more examples.

## Mock Mode (Default)

By default, the system runs in **mock mode** with deterministic test data:
- No real Shopify credentials needed
- Returns realistic sample data for products, orders, and inventory
- Perfect for development and demonstration

To enable real Shopify integration, set `SHOPIFY_MODE=real` in `ai_service/.env` and configure OAuth tokens.

## Development

### Rails API (Local)

```bash
cd rails_api
bundle install
rails db:create db:migrate
rails s -p 3000
```

### Python AI Service (Local)

```bash
cd ai_service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing

### Rails Tests

```bash
cd rails_api
bundle exec rspec
```

### Python Tests

```bash
cd ai_service
pytest
```

## Project Structure

```
.
├── rails_api/              # Rails API Gateway
│   ├── app/
│   │   ├── controllers/    # API endpoints
│   │   ├── models/         # Shop model
│   │   └── services/       # PythonAiClient
│   ├── db/                 # Migrations
│   ├── spec/               # RSpec tests
│   └── Dockerfile
├── ai_service/             # Python AI Service
│   ├── app/
│   │   ├── agent/          # Agentic workflow
│   │   ├── models/         # Pydantic models
│   │   ├── shopify/        # Shopify client & mocks
│   │   └── main.py         # FastAPI app
│   ├── tests/              # Pytest tests
│   └── Dockerfile
├── docker-compose.yml
├── ARCHITECTURE.md
└── API_EXAMPLES.md
```

## Features

### Implemented
✅ Rails API gateway with request validation  
✅ Python AI agent with 5-step workflow  
✅ Intent classification (sales, inventory, customers)  
✅ ShopifyQL query generation  
✅ Query validation against allowlist  
✅ Mock Shopify data for demo  
✅ Business-friendly answer formatting  
✅ Confidence scoring (low/medium/high)  
✅ Request logging  
✅ Error handling  
✅ Docker containerization  

### Bonus Features
✅ Query validation layer  
🔲 Caching layer (documented in ARCHITECTURE.md)  
🔲 Conversation memory (documented in ARCHITECTURE.md)  
🔲 Metrics dashboard (documented in ARCHITECTURE.md)  

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs rails_api
docker-compose logs ai_service

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

### Database issues
```bash
# Reset database
docker-compose exec rails_api rails db:reset
```

### Port conflicts
Edit `docker-compose.yml` to change port mappings if 3000 or 8000 are in use.

## License

MIT

## Time Spent

~48 hours focusing on:
- Clean architecture and separation of concerns
- Agentic workflow design with clear reasoning steps
- Production-ready error handling
- Comprehensive documentation
- Runnable demo with mock data
