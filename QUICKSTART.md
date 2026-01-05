# Quick Start Guide

Get the Shopify Analytics AI App running in under 5 minutes.

## Prerequisites

- Docker & Docker Compose installed
- Terminal access

## Steps

### 1. Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create environment files
- Build Docker containers
- Start all services
- Create a demo store

### 2. Test the API

Health check:
```bash
curl http://localhost:3000/health
```

Ask a question:
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "What were my top 5 selling products last week?"
  }'
```

### 3. Explore

- View Rails logs: `docker-compose logs -f rails_api`
- View Python logs: `docker-compose logs -f ai_service`
- See [API_EXAMPLES.md](./API_EXAMPLES.md) for more queries
- See [ARCHITECTURE.md](./ARCHITECTURE.md) for system design

## Common Commands

**Start services:**
```bash
docker-compose up
```

**Stop services:**
```bash
docker-compose down
```

**Rebuild services:**
```bash
docker-compose up --build
```

**Reset database:**
```bash
docker-compose exec rails_api rails db:reset
```

**Run Rails tests:**
```bash
docker-compose exec rails_api bundle exec rspec
```

**Run Python tests:**
```bash
docker-compose exec ai_service pytest
```

## Troubleshooting

### Services won't start

Check logs:
```bash
docker-compose logs rails_api
docker-compose logs ai_service
```

### Port conflicts

Edit `docker-compose.yml` to change ports if 3000 or 8000 are already in use.

### Database issues

Reset the database:
```bash
docker-compose exec rails_api rails db:drop db:create db:migrate db:seed
```

## Next Steps

1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) to understand the system design
2. Try different questions from [API_EXAMPLES.md](./API_EXAMPLES.md)
3. Explore the agentic workflow in `ai_service/app/agent/`
4. Add your own Shopify credentials for real mode (see README.md)

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs`
2. Verify Docker is running: `docker ps`
3. Try rebuilding: `docker-compose down -v && docker-compose up --build`
