# Architecture Documentation

## System Overview

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Client    │────────▶│   Rails API      │────────▶│  Python AI      │
│             │         │   Gateway        │         │  Service        │
│             │◀────────│  (Port 3000)     │◀────────│  (Port 8000)    │
└─────────────┘         └──────────────────┘         └─────────────────┘
                               │                              │
                               ▼                              ▼
                        ┌──────────────┐            ┌─────────────────┐
                        │  PostgreSQL  │            │ Shopify API     │
                        │  Database    │            │ (Mock/Real)     │
                        └──────────────┘            └─────────────────┘
```

## Components

### 1. Rails API Gateway (`/rails_api`)

**Responsibility**: Request validation, authentication, routing, response formatting

**Technology**: Ruby on Rails 7 (API-only mode)

**Key Files**:
- `app/controllers/api/v1/questions_controller.rb` - Main endpoint
- `app/services/python_ai_client.rb` - HTTP client for Python service
- `app/models/shop.rb` - Store credentials model
- `db/migrate/*` - Database schema

**Endpoints**:
- `GET /health` - Health check
- `POST /api/v1/questions` - Main analytics query endpoint

**Flow**:
1. Receive question + store_id
2. Validate input (presence, format)
3. Lookup store credentials in database
4. Forward to Python service with access_token
5. Return formatted response
6. Log request (optional)

**Error Handling**:
- 400: Invalid input (missing fields, invalid format)
- 404: Store not found
- 503: Python service unavailable
- 500: Internal server error

### 2. Python AI Service (`/ai_service`)

**Responsibility**: AI-powered intent classification, query generation, execution, and formatting

**Technology**: FastAPI + Pydantic

**Key Files**:
- `app/main.py` - FastAPI application
- `app/agent/workflow.py` - 5-step agentic workflow
- `app/agent/intent_classifier.py` - Intent classification logic
- `app/agent/query_generator.py` - ShopifyQL generation
- `app/agent/validator.py` - Query validation
- `app/agent/answer_formatter.py` - Business-friendly formatting
- `app/shopify/client.py` - Shopify API adapter
- `app/shopify/mock_data.py` - Mock data provider
- `app/models/*.py` - Pydantic models

**Endpoints**:
- `GET /health` - Health check
- `POST /agent/query` - Execute agentic workflow

## Agentic Workflow

The Python service implements a **5-step agentic workflow**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENTIC WORKFLOW                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   STEP 1: CLASSIFY    │
                    │   Intent Detection    │
                    │   - Sales/Inventory/  │
                    │     Customers         │
                    │   - Time Period       │
                    │   - Entities          │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   STEP 2: PLAN        │
                    │   Determine Data      │
                    │   Sources Needed      │
                    │   - Tables            │
                    │   - Fields            │
                    │   - Aggregations      │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   STEP 3: GENERATE    │
                    │   ShopifyQL Query     │
                    │   - Syntax correct    │
                    │   - Optimized         │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   STEP 4: VALIDATE    │
                    │   & Execute           │
                    │   - Check allowlist   │
                    │   - Prevent injection │
                    │   - Handle errors     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   STEP 5: FORMAT      │
                    │   Business-Friendly   │
                    │   - Layman language   │
                    │   - Confidence score  │
                    │   - Actionable        │
                    └───────────────────────┘
```

### Step 1: Intent Classification

**Input**: Natural language question

**Process**:
- Classify intent category: `sales`, `inventory`, `customers`, `general`
- Extract time period: "last week", "next month", "30 days"
- Extract entities: product names, customer segments
- Identify metrics: top sellers, stockouts, reorder quantities

**Output**:
```python
{
    "intent": "inventory",
    "time_period": {"value": 7, "unit": "days"},
    "entities": ["Product X"],
    "metrics": ["stockout_prediction"]
}
```

**Implementation**: Pattern matching + keyword analysis (LLM integration ready)

### Step 2: Planning

**Input**: Classified intent

**Process**:
- Map intent to required Shopify data sources
- Determine necessary tables: `orders`, `products`, `inventory_levels`
- Identify required fields and aggregations

**Output**:
```python
{
    "data_sources": ["inventory_levels", "products", "orders"],
    "required_fields": ["quantity", "sku", "sold_count"],
    "aggregation_type": "projection"
}
```

### Step 3: ShopifyQL Generation

**Input**: Data plan

**Process**:
- Generate syntactically correct ShopifyQL
- Apply time filters
- Add appropriate aggregations (SUM, COUNT, AVG)
- Handle JOINs when needed

**Output**:
```sql
SELECT 
  product_id,
  product_title,
  SUM(quantity) as total_sold
FROM orders
WHERE created_at >= '2025-12-29'
  AND created_at <= '2026-01-05'
GROUP BY product_id, product_title
ORDER BY total_sold DESC
LIMIT 5
```

**Note**: ShopifyQL syntax approximates Shopify's analytics query language. Real implementation would use exact Shopify schema.

### Step 4: Validation & Execution

**Input**: Generated query + access token

**Validation**:
- Check against allowlist of safe tables
- Verify no SQL injection patterns
- Ensure read-only operations
- Validate date ranges

**Allowlist**:
- Tables: `orders`, `products`, `inventory_levels`, `customers`, `order_line_items`
- Operations: `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `ORDER BY`, `LIMIT`
- Blocked: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `EXEC`

**Execution**:
- Call ShopifyClient adapter
- Handle empty results
- Catch API errors
- Retry logic (future enhancement)

**Output**: Raw data array

### Step 5: Answer Formatting

**Input**: Raw query results + original question

**Process**:
- Convert technical data to business insights
- Add context and recommendations
- Calculate confidence based on data quality
- Generate actionable summary

**Confidence Scoring**:
- `high`: Complete data, clear patterns, >30 days history
- `medium`: Partial data, some gaps, 7-30 days history
- `low`: Sparse data, <7 days history, ambiguous patterns

**Output**:
```python
{
    "answer": "Based on the last 30 days, you sell around 10 units per day. You should reorder at least 70 units to avoid stockouts next week.",
    "confidence": "medium",
    "shopifyql": "SELECT ...",
    "intent": "inventory",
    "used_data_sources": ["orders", "inventory_levels"]
}
```

## Data Flow

### Successful Request Flow

```
1. Client → Rails: POST /api/v1/questions
   {
     "store_id": "demo-store.myshopify.com",
     "question": "What were my top 5 selling products last week?"
   }

2. Rails validates input
3. Rails queries DB for shop credentials
4. Rails → Python: POST /agent/query
   {
     "store_id": "demo-store.myshopify.com",
     "question": "What were my top 5 selling products last week?",
     "access_token": "mock_token_12345"
   }

5. Python executes 5-step workflow
6. Python → Rails: Response
   {
     "answer": "Your top 5 products last week were...",
     "confidence": "high",
     "shopifyql": "SELECT ...",
     "intent": "sales",
     "used_data_sources": ["orders", "products"]
   }

7. Rails → Client: Formatted response
```

### Error Flow

```
1. Client → Rails: Invalid request (missing field)
2. Rails → Client: 400 Bad Request
   {
     "error": "Missing required field: question"
   }

OR

1. Client → Rails: Valid request
2. Rails → Python: Request forwarded
3. Python: Query validation fails
4. Python → Rails: 400 Bad Request
   {
     "error": "Query contains unsafe operations"
   }
5. Rails → Client: 400 Bad Request
```

## Shopify Integration

### Mock Mode (Default)

**Purpose**: Enable development and demo without real Shopify credentials

**Implementation**:
- `app/shopify/mock_data.py` provides deterministic sample data
- Simulates realistic product, order, and inventory data
- Responds to ShopifyQL-like queries with filtered mock results

**Data Sets**:
- 10 sample products (various categories)
- 50 sample orders (last 90 days)
- Inventory levels for all products
- 20 sample customers

### Real Mode

**Configuration**: Set `SHOPIFY_MODE=real` in `.env`

**Requirements**:
- Shopify Partner account
- OAuth app credentials (`SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`)
- Store access tokens (stored in database)

**OAuth Flow** (documented, not fully implemented):
1. Redirect user to Shopify authorization URL
2. User approves app
3. Shopify redirects with authorization code
4. Exchange code for access token
5. Store token in database

**API Calls**:
- Use Shopify Admin REST API
- Endpoint: `https://{shop_domain}/admin/api/2024-01/graphql.json`
- Authentication: `X-Shopify-Access-Token` header

## Database Schema

### Shops Table

```sql
CREATE TABLE shops (
  id BIGSERIAL PRIMARY KEY,
  shop_domain VARCHAR NOT NULL UNIQUE,
  access_token VARCHAR NOT NULL,
  shop_name VARCHAR,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

**Purpose**: Store Shopify credentials per store

**Fields**:
- `shop_domain`: Unique identifier (e.g., "demo-store.myshopify.com")
- `access_token`: OAuth access token for Shopify API
- `shop_name`: Display name

### Future Tables (Optional)

```sql
-- Request logging
CREATE TABLE analytics_requests (
  id BIGSERIAL PRIMARY KEY,
  shop_id BIGINT REFERENCES shops(id),
  question TEXT,
  intent VARCHAR,
  shopifyql TEXT,
  confidence VARCHAR,
  response_time_ms INTEGER,
  created_at TIMESTAMP NOT NULL
);

-- Caching layer
CREATE TABLE query_cache (
  id BIGSERIAL PRIMARY KEY,
  shop_id BIGINT REFERENCES shops(id),
  query_hash VARCHAR NOT NULL,
  result JSONB,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL
);
```

## Security Considerations

### Input Validation
- Rails validates all incoming requests
- Python validates ShopifyQL before execution
- Allowlist approach for safe operations

### SQL Injection Prevention
- ShopifyQL validator blocks dangerous patterns
- Parameterized queries (when using real DB)
- Read-only operations enforced

### Token Security
- Access tokens stored encrypted (production recommendation)
- Tokens never exposed in logs or responses
- HTTPS required in production

### Rate Limiting
- Implement rate limiting on Rails API (future)
- Respect Shopify API rate limits
- Exponential backoff on retries

## Performance Considerations

### Caching Strategy (Future Enhancement)

**Query Result Cache**:
- Cache results by query hash + time window
- TTL: 5-15 minutes depending on data freshness needs
- Invalidate on data updates

**Shopify Response Cache**:
- Cache raw Shopify API responses
- Reduce API calls to Shopify
- TTL: 1-5 minutes

### Optimization Opportunities

1. **Connection Pooling**: Use persistent HTTP connections
2. **Batch Queries**: Combine related queries when possible
3. **Async Processing**: Queue long-running analyses
4. **Database Indexes**: Index shop_domain, created_at fields

## Scalability

### Horizontal Scaling

**Rails API**:
- Stateless design enables easy horizontal scaling
- Load balancer distributes requests
- Shared PostgreSQL database

**Python AI Service**:
- Stateless agent design
- Scale based on CPU/memory usage
- Consider GPU instances for LLM inference

### Vertical Scaling

- Increase resources for LLM processing
- Optimize database queries
- Use faster storage for caching

## Testing Strategy

### Unit Tests

**Rails**:
- Model validations
- Service object logic
- API response formats

**Python**:
- Intent classification accuracy
- Query generation correctness
- Validation logic
- Answer formatting

### Integration Tests

**Rails**:
- Full request flow: endpoint → service → response
- Error handling scenarios
- Database interactions

**Python**:
- Full agent workflow
- Mock Shopify client interactions
- Edge cases (empty data, malformed queries)

### End-to-End Tests

- Docker Compose environment
- Realistic user scenarios
- Performance benchmarks

## Future Enhancements

### Conversation Memory
- Store conversation history
- Enable follow-up questions: "What about last month?"
- Context-aware responses

### Advanced Analytics
- Trend detection
- Anomaly alerts
- Predictive models (inventory forecasting)

### Multi-Turn Reasoning
- Agent asks clarifying questions
- Handles ambiguous queries interactively

### Metrics Dashboard
- Track query patterns
- Monitor agent performance
- Analyze common intents

### Real-Time Processing
- WebSocket support for streaming responses
- Progressive result display
- Live data updates

## Deployment

### Production Checklist

- [ ] Enable HTTPS/TLS
- [ ] Set up environment variables securely
- [ ] Configure database backups
- [ ] Implement rate limiting
- [ ] Set up monitoring (Datadog, New Relic)
- [ ] Configure logging aggregation
- [ ] Enable error tracking (Sentry)
- [ ] Set up CI/CD pipeline
- [ ] Load testing
- [ ] Security audit

### Recommended Infrastructure

- **Compute**: AWS ECS, Google Cloud Run, or Kubernetes
- **Database**: AWS RDS PostgreSQL or Google Cloud SQL
- **Caching**: Redis
- **Load Balancer**: AWS ALB or Google Cloud Load Balancing
- **Monitoring**: Datadog, Prometheus + Grafana
