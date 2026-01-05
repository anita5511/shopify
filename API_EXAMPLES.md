# API Examples

This document provides example requests and responses for the Shopify Analytics API.

## Base URLs

- Rails API: `http://localhost:3000`
- Python AI Service: `http://localhost:8000` (internal, not exposed)

## Authentication

Currently using store-based authentication via `store_id`. OAuth flow is documented but not fully implemented in mock mode.

---

## Endpoints

### 1. Health Check (Rails)

**Request:**
```bash
curl http://localhost:3000/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "rails_api",
  "timestamp": "2026-01-05T10:30:00Z"
}
```

---

### 2. Ask Question (Rails → Python)

**Endpoint:** `POST /api/v1/questions`

#### Example 1: Top Selling Products

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "What were my top 5 selling products last week?"
  }'
```

**Response (200 OK):**
```json
{
  "answer": "Your top 5 selling products last week were:\n\n1. Wireless Bluetooth Headphones - 45 units sold\n2. Organic Cotton T-Shirt - 38 units sold\n3. Stainless Steel Water Bottle - 32 units sold\n4. Yoga Mat Pro - 28 units sold\n5. Smart Watch Series 5 - 24 units sold\n\nTotal revenue from these products: $8,450",
  "confidence": "high",
  "shopifyql": "SELECT product_id, product_title, SUM(quantity) as total_sold FROM orders WHERE created_at >= '2025-12-29' AND created_at <= '2026-01-05' GROUP BY product_id, product_title ORDER BY total_sold DESC LIMIT 5",
  "intent": "sales",
  "used_data_sources": [
    "orders",
    "products"
  ],
  "metadata": {
    "time_period": {
      "value": 7,
      "unit": "days"
    },
    "entities": [],
    "processing_time_ms": 245
  }
}
```

---

#### Example 2: Inventory Reorder Recommendation

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "How much inventory should I reorder for Wireless Bluetooth Headphones based on last 30 days sales?"
  }'
```

**Response (200 OK):**
```json
{
  "answer": "Based on the last 30 days, Wireless Bluetooth Headphones sold an average of 12 units per day (total: 360 units). Current inventory: 45 units.\n\nRecommendation: Order at least 170 units to maintain a 2-week buffer. This accounts for your current stock and typical daily sales velocity.",
  "confidence": "high",
  "shopifyql": "SELECT product_id, product_title, SUM(quantity) as total_sold, AVG(quantity) as avg_daily_sales FROM orders WHERE product_title LIKE '%Wireless Bluetooth Headphones%' AND created_at >= '2025-12-06' AND created_at <= '2026-01-05' GROUP BY product_id, product_title",
  "intent": "inventory",
  "used_data_sources": [
    "orders",
    "products",
    "inventory_levels"
  ],
  "metadata": {
    "time_period": {
      "value": 30,
      "unit": "days"
    },
    "entities": [
      "Wireless Bluetooth Headphones"
    ],
    "processing_time_ms": 312
  }
}
```

---

#### Example 3: Stockout Prediction

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "Which products are likely to go out of stock in 7 days?"
  }'
```

**Response (200 OK):**
```json
{
  "answer": "Based on recent sales velocity, 3 products are at risk of stockout within 7 days:\n\n⚠️ HIGH RISK:\n• Smart Watch Series 5 - Current stock: 12 units, Daily sales: 2.1 units (runs out in ~5 days)\n• Organic Cotton T-Shirt - Current stock: 15 units, Daily sales: 2.8 units (runs out in ~5 days)\n\n⚠️ MEDIUM RISK:\n• Yoga Mat Pro - Current stock: 22 units, Daily sales: 3.2 units (runs out in ~7 days)\n\nRecommendation: Prioritize reordering Smart Watch Series 5 and Organic Cotton T-Shirt immediately.",
  "confidence": "medium",
  "shopifyql": "SELECT p.product_id, p.product_title, i.quantity as current_stock, (SELECT AVG(daily_sales) FROM (SELECT DATE(created_at) as date, SUM(quantity) as daily_sales FROM orders WHERE product_id = p.product_id AND created_at >= '2025-12-29' GROUP BY date) subq) as avg_daily_sales FROM products p JOIN inventory_levels i ON p.product_id = i.product_id WHERE i.quantity / (SELECT AVG(daily_sales) FROM orders WHERE product_id = p.product_id) <= 7",
  "intent": "inventory",
  "used_data_sources": [
    "products",
    "inventory_levels",
    "orders"
  ],
  "metadata": {
    "time_period": {
      "value": 7,
      "unit": "days"
    },
    "entities": [],
    "processing_time_ms": 389
  }
}
```

---

#### Example 4: Repeat Customers

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "Which customers placed repeat orders in the last 90 days?"
  }'
```

**Response (200 OK):**
```json
{
  "answer": "You had 8 repeat customers in the last 90 days:\n\nTop Repeat Customers:\n1. Sarah Johnson (sarah.j@email.com) - 5 orders, $1,245 total\n2. Michael Chen (michael.c@email.com) - 4 orders, $890 total\n3. Emily Davis (emily.d@email.com) - 3 orders, $567 total\n4. James Wilson (james.w@email.com) - 3 orders, $445 total\n5. Lisa Anderson (lisa.a@email.com) - 2 orders, $390 total\n\nThese 8 customers represent 32% of your revenue in this period. Consider implementing a loyalty program to retain them!",
  "confidence": "high",
  "shopifyql": "SELECT customer_id, customer_email, customer_name, COUNT(*) as order_count, SUM(total_price) as total_spent FROM orders WHERE created_at >= '2025-10-07' AND created_at <= '2026-01-05' GROUP BY customer_id, customer_email, customer_name HAVING COUNT(*) > 1 ORDER BY order_count DESC",
  "intent": "customers",
  "used_data_sources": [
    "orders",
    "customers"
  ],
  "metadata": {
    "time_period": {
      "value": 90,
      "unit": "days"
    },
    "entities": [],
    "processing_time_ms": 278
  }
}
```

---

#### Example 5: Inventory Needs (Next Month)

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "How many units of Yoga Mat Pro will I need next month?"
  }'
```

**Response (200 OK):**
```json
{
  "answer": "Based on the last 60 days of sales data:\n\nYoga Mat Pro:\n• Average daily sales: 3.2 units\n• Expected demand for next 30 days: ~96 units\n• Current inventory: 22 units\n• Recommended order: 75-100 units\n\nThis recommendation includes a 20% safety buffer for demand fluctuations and accounts for your current stock levels.",
  "confidence": "medium",
  "shopifyql": "SELECT product_id, product_title, SUM(quantity) as total_sold, AVG(quantity) as avg_daily_sales FROM orders WHERE product_title LIKE '%Yoga Mat Pro%' AND created_at >= '2025-11-06' AND created_at <= '2026-01-05' GROUP BY product_id, product_title",
  "intent": "inventory",
  "used_data_sources": [
    "orders",
    "products",
    "inventory_levels"
  ],
  "metadata": {
    "time_period": {
      "value": 30,
      "unit": "days"
    },
    "entities": [
      "Yoga Mat Pro"
    ],
    "processing_time_ms": 295
  }
}
```

---

## Error Responses

### Missing Required Field

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com"
  }'
```

**Response (400 Bad Request):**
```json
{
  "error": "Missing required field: question"
}
```

---

### Store Not Found

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "nonexistent-store.myshopify.com",
    "question": "What are my sales?"
  }'
```

**Response (404 Not Found):**
```json
{
  "error": "Store not found: nonexistent-store.myshopify.com"
}
```

---

### Python Service Unavailable

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "Show me sales"
  }'
```

**Response (503 Service Unavailable):**
```json
{
  "error": "AI service temporarily unavailable. Please try again in a moment."
}
```

---

### Invalid Query (Unsafe Operations)

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "DROP TABLE orders"
  }'
```

**Response (400 Bad Request):**
```json
{
  "error": "Query validation failed: unsafe operation detected",
  "details": "The generated query contains blocked operations. Please rephrase your question."
}
```

---

## Python AI Service Endpoints (Internal)

### Health Check

**Request:**
```bash
curl http://localhost:8000/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "ai_agent",
  "mode": "mock",
  "timestamp": "2026-01-05T10:30:00Z"
}
```

---

### Agent Query (Direct)

**Endpoint:** `POST /agent/query`

**Note:** This endpoint is typically called by Rails, not directly by clients.

**Request:**
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "demo-store.myshopify.com",
    "question": "What were my top 3 products yesterday?",
    "access_token": "mock_token_12345"
  }'
```

**Response (200 OK):**
```json
{
  "answer": "Your top 3 products yesterday were:\n1. Wireless Bluetooth Headphones (8 units)\n2. Organic Cotton T-Shirt (6 units)\n3. Smart Watch Series 5 (5 units)",
  "confidence": "high",
  "shopifyql": "SELECT product_id, product_title, SUM(quantity) as total_sold FROM orders WHERE created_at >= '2026-01-04' AND created_at < '2026-01-05' GROUP BY product_id, product_title ORDER BY total_sold DESC LIMIT 3",
  "intent": "sales",
  "used_data_sources": [
    "orders",
    "products"
  ],
  "metadata": {
    "intent_details": {
      "category": "sales",
      "time_period": {
        "value": 1,
        "unit": "days"
      },
      "entities": [],
      "metrics": [
        "top_products"
      ]
    },
    "planning": {
      "data_sources": [
        "orders",
        "products"
      ],
      "required_fields": [
        "product_id",
        "product_title",
        "quantity",
        "created_at"
      ],
      "aggregation_type": "sum_group"
    },
    "validation": {
      "passed": true,
      "checks": [
        "safe_tables",
        "safe_operations",
        "no_injection"
      ]
    },
    "data_quality": {
      "rows_returned": 3,
      "completeness": 1.0
    }
  }
}
```

---

## Response Field Descriptions

### Main Fields

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Business-friendly answer in plain language |
| `confidence` | string | Confidence level: "low", "medium", or "high" |
| `shopifyql` | string | Generated ShopifyQL query for transparency |
| `intent` | string | Classified intent: "sales", "inventory", "customers", "general" |
| `used_data_sources` | array | List of Shopify data sources queried |
| `metadata` | object | Additional context and processing details |

### Confidence Levels

- **high**: Complete data, clear patterns, sufficient history (>30 days)
- **medium**: Partial data, some gaps, moderate history (7-30 days)
- **low**: Sparse data, insufficient history (<7 days), ambiguous patterns

### Metadata Fields

| Field | Description |
|-------|-------------|
| `time_period` | Extracted time window from question |
| `entities` | Product names or customer segments mentioned |
| `processing_time_ms` | Time taken to process the request |
| `intent_details` | Detailed intent classification results |
| `planning` | Data source planning details |
| `validation` | Query validation results |
| `data_quality` | Quality metrics of returned data |

---

## Testing with Different Stores

### Create a Test Store

```bash
docker-compose exec rails_api rails runner "
Shop.create!(
  shop_domain: 'test-store.myshopify.com',
  access_token: 'test_token_67890',
  shop_name: 'Test Store'
)
"
```

### Use Test Store

```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "test-store.myshopify.com",
    "question": "Show me today'\''s sales"
  }'
```

---

## Rate Limiting (Future)

When rate limiting is implemented:

**Response (429 Too Many Requests):**
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "limit": "100 requests per hour"
}
```

---

## Tips for Best Results

1. **Be specific with time periods**: "last week" works better than "recently"
2. **Name products clearly**: Use exact product names when asking about specific items
3. **Ask one question at a time**: Multiple questions in one request may reduce accuracy
4. **Use natural language**: The system understands conversational questions
5. **Check confidence levels**: Low confidence may indicate insufficient data

---

## Need Help?

- Check service health: `curl http://localhost:3000/health`
- View logs: `docker-compose logs -f rails_api` or `docker-compose logs -f ai_service`
- Restart services: `docker-compose restart`
- Reset database: `docker-compose exec rails_api rails db:reset`
