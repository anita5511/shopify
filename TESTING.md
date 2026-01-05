# Testing Guide

Comprehensive guide for testing the Shopify Analytics AI App.

## Quick Test Commands

### Run All Tests

```bash
# Rails tests
docker-compose exec rails_api bundle exec rspec

# Python tests
docker-compose exec ai_service pytest

# Both
docker-compose exec rails_api bundle exec rspec && \
docker-compose exec ai_service pytest
```

## Rails API Tests

### Setup Test Database

```bash
docker-compose exec rails_api rails db:test:prepare
```

### Run Specific Tests

```bash
# All request specs
docker-compose exec rails_api bundle exec rspec spec/requests

# Specific file
docker-compose exec rails_api bundle exec rspec spec/requests/api/v1/questions_spec.rb

# Specific test
docker-compose exec rails_api bundle exec rspec spec/requests/api/v1/questions_spec.rb:10
```

### Test Coverage

The Rails tests cover:
- ✅ Input validation (missing fields, invalid format)
- ✅ Shop lookup (found/not found)
- ✅ Python service integration
- ✅ Error handling
- ✅ Response formatting

### Adding New Rails Tests

Create test file in `spec/requests/`:

```ruby
require 'rails_helper'

RSpec.describe "YourEndpoint", type: :request do
  describe "GET /your_path" do
    it "returns success" do
      get "/your_path"
      expect(response).to have_http_status(:success)
    end
  end
end
```

## Python AI Tests

### Run Tests with Coverage

```bash
docker-compose exec ai_service pytest --cov=app --cov-report=html
```

### Run Specific Tests

```bash
# All tests
docker-compose exec ai_service pytest

# Specific file
docker-compose exec ai_service pytest tests/test_workflow.py

# Specific test
docker-compose exec ai_service pytest tests/test_workflow.py::test_workflow_sales_query

# With verbose output
docker-compose exec ai_service pytest -v
```

### Test Coverage

The Python tests cover:
- ✅ Complete workflow execution
- ✅ Intent classification
- ✅ ShopifyQL generation
- ✅ Query validation
- ✅ Answer formatting
- ✅ Different question types (sales, inventory, customers)
- ✅ Entity extraction

### Adding New Python Tests

Create test in `tests/`:

```python
import pytest
from app.agent.workflow import AgentWorkflow

@pytest.mark.asyncio
async def test_your_feature():
    workflow = AgentWorkflow('test-store.myshopify.com', 'mock_token')
    result = await workflow.execute("Your question here")
    
    assert result.confidence in ['low', 'medium', 'high']
    assert 'expected_text' in result.answer
```

## Manual Testing

### 1. Health Checks

Test both services are running:

```bash
# Rails health
curl http://localhost:3000/health

# Python health
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "rails_api",
  "timestamp": "2026-01-05T10:30:00Z",
  "database": "connected"
}
```

### 2. End-to-End Question Flow

Test complete workflow:

```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "What were my top 5 selling products last week?"
  }'
```

Verify response has:
- ✅ `answer` field (business-friendly text)
- ✅ `confidence` field (low/medium/high)
- ✅ `shopifyql` field (generated query)
- ✅ `intent` field (sales/inventory/customers)
- ✅ `used_data_sources` array
- ✅ `metadata` object

### 3. Error Cases

Test error handling:

**Missing field:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"store_id": "demo-store.myshopify.com"}'

# Expected: 400 Bad Request with error message
```

**Store not found:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "nonexistent.myshopify.com",
    "question": "test"
  }'

# Expected: 404 Not Found
```

**Invalid query:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "DROP TABLE orders"
  }'

# Expected: 400 Bad Request with validation error
```

### 4. Different Question Types

Test all supported intents:

**Sales:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"store_id": "demo-store.myshopify.com", "question": "What were my top selling products last month?"}'
```

**Inventory:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"store_id": "demo-store.myshopify.com", "question": "Which products will run out of stock in 7 days?"}'
```

**Customers:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"store_id": "demo-store.myshopify.com", "question": "Who are my repeat customers?"}'
```

**Reorder:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"store_id": "demo-store.myshopify.com", "question": "How much inventory should I reorder for Wireless Bluetooth Headphones?"}'
```

## Component Testing

### Test Intent Classifier

```python
from app.agent.intent_classifier import IntentClassifier

classifier = IntentClassifier()

# Test sales intent
result = classifier.classify("What were my top selling products?")
assert result['category'] == 'sales'

# Test inventory intent
result = classifier.classify("Which products need reordering?")
assert result['category'] == 'inventory'

# Test time extraction
result = classifier.classify("Show me sales from last week")
assert result['time_period']['value'] == 7
assert result['time_period']['unit'] == 'days'
```

### Test Query Generator

```python
from app.agent.query_generator import QueryGenerator

generator = QueryGenerator()

intent = {
    'category': 'sales',
    'metrics': ['top_products'],
    'time_period': {'value': 7, 'unit': 'days'},
    'entities': []
}

query = generator.generate(intent, {'data_sources': ['orders', 'products']})
assert 'SELECT' in query
assert 'FROM orders' in query
assert 'GROUP BY' in query
```

### Test Validator

```python
from app.agent.validator import QueryValidator

validator = QueryValidator()

# Test valid query
query = "SELECT product_id FROM orders WHERE created_at >= '2026-01-01'"
result = validator.validate(query)
assert result['passed'] == True

# Test invalid query
query = "DROP TABLE orders"
result = validator.validate(query)
assert result['passed'] == False
```

### Test Mock Data

```python
from app.shopify.mock_data import MockShopifyData

mock = MockShopifyData()

# Test products
products = mock.get_top_products({'value': 7, 'unit': 'days'}, [])
assert len(products) > 0
assert 'product_id' in products[0]
assert 'total_sold' in products[0]

# Test inventory
inventory = mock.get_inventory_levels([])
assert len(inventory) == 10  # We have 10 products
```

## Load Testing

### Basic Load Test

Use `ab` (Apache Bench) or `wrk`:

```bash
# Install ab (if needed)
# Ubuntu: apt-get install apache2-utils
# Mac: brew install httpd

# Run 1000 requests with concurrency of 10
ab -n 1000 -c 10 -T 'application/json' \
  -p question.json \
  http://localhost:3000/api/v1/questions
```

Create `question.json`:
```json
{
  "store_id": "demo-store.myshopify.com",
  "question": "What were my sales last week?"
}
```

### Expected Performance

In mock mode:
- Response time: < 500ms (p95)
- Throughput: > 20 req/sec (single instance)

### Stress Test

```bash
# Install wrk
# Ubuntu: apt-get install wrk
# Mac: brew install wrk

wrk -t4 -c100 -d30s --timeout 10s \
  -s post.lua \
  http://localhost:3000/api/v1/questions
```

Create `post.lua`:
```lua
wrk.method = "POST"
wrk.body   = '{"store_id":"demo-store.myshopify.com","question":"Top products?"}'
wrk.headers["Content-Type"] = "application/json"
```

## Integration Testing

### Test Full Stack

Create integration test script `test_integration.sh`:

```bash
#!/bin/bash

echo "Testing full stack integration..."

# 1. Health checks
echo "1. Testing health endpoints..."
curl -s http://localhost:3000/health | grep "healthy" || exit 1
curl -s http://localhost:8000/health | grep "healthy" || exit 1

# 2. Sales query
echo "2. Testing sales query..."
response=$(curl -s -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"store_id":"demo-store.myshopify.com","question":"Top products last week?"}')

echo $response | grep "answer" || exit 1
echo $response | grep "confidence" || exit 1

# 3. Inventory query
echo "3. Testing inventory query..."
response=$(curl -s -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"store_id":"demo-store.myshopify.com","question":"Which products will run out?"}')

echo $response | grep "inventory" || exit 1

# 4. Customer query
echo "4. Testing customer query..."
response=$(curl -s -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"store_id":"demo-store.myshopify.com","question":"Repeat customers?"}')

echo $response | grep "customer" || exit 1

echo "✓ All integration tests passed!"
```

Run:
```bash
chmod +x test_integration.sh
./test_integration.sh
```

## Continuous Integration

Example GitHub Actions workflow (`.github/workflows/test.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build services
      run: docker-compose up -d --build
    
    - name: Wait for services
      run: sleep 15
    
    - name: Run Rails tests
      run: docker-compose exec -T rails_api bundle exec rspec
    
    - name: Run Python tests
      run: docker-compose exec -T ai_service pytest
    
    - name: Run integration tests
      run: ./test_integration.sh
    
    - name: Cleanup
      run: docker-compose down -v
```

## Debugging Failed Tests

### View Rails Logs

```bash
# During test run
docker-compose logs -f rails_api

# After test run
docker-compose exec rails_api tail -f log/test.log
```

### View Python Logs

```bash
docker-compose logs -f ai_service
```

### Interactive Debugging

**Rails console:**
```bash
docker-compose exec rails_api rails console
```

**Python shell:**
```bash
docker-compose exec ai_service python
>>> from app.agent.workflow import AgentWorkflow
>>> # Run code interactively
```

### Common Issues

**Database not ready:**
```bash
docker-compose exec rails_api rails db:create db:migrate
```

**Python dependencies outdated:**
```bash
docker-compose exec ai_service pip install -r requirements.txt
```

**Port conflicts:**
Check `docker-compose ps` and adjust ports in `docker-compose.yml`

## Test Data Management

### Reset to Clean State

```bash
# Reset database
docker-compose exec rails_api rails db:reset

# Recreate demo store
docker-compose exec rails_api rails db:seed
```

### Add Test Stores

```bash
docker-compose exec rails_api rails runner "
  Shop.create!(
    shop_domain: 'test-store.myshopify.com',
    access_token: 'test_token',
    shop_name: 'Test Store'
  )
"
```

## Code Quality

### Linting

**Ruby (RuboCop):**
```bash
docker-compose exec rails_api rubocop
```

**Python (flake8, black):**
```bash
docker-compose exec ai_service flake8 app/
docker-compose exec ai_service black --check app/
```

### Type Checking

**Python (mypy):**
```bash
docker-compose exec ai_service mypy app/
```

## Reporting

### Generate Coverage Reports

**Rails:**
```bash
docker-compose exec rails_api bundle exec rspec --format html --out coverage.html
```

**Python:**
```bash
docker-compose exec ai_service pytest --cov=app --cov-report=html
```

View HTML reports in browser after copying from container.

---

## Summary Checklist

Before deployment:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Load testing shows acceptable performance
- [ ] Error cases handled gracefully
- [ ] Logs are clear and actionable
- [ ] Health checks return success
- [ ] All question types work correctly
- [ ] Mock data is comprehensive
- [ ] Documentation is up to date
