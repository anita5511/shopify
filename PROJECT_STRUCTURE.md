# Project Structure

Complete file listing and description for the Shopify Analytics AI App.

```
shopify-analytics-ai/
│
├── README.md                          # Main project documentation
├── ARCHITECTURE.md                    # Detailed architecture guide
├── API_EXAMPLES.md                    # API usage examples
├── QUICKSTART.md                      # Quick start guide
├── PROJECT_STRUCTURE.md               # This file
├── .gitignore                         # Git ignore rules
├── docker-compose.yml                 # Docker orchestration
└── setup.sh                           # Automated setup script
│
├── rails_api/                         # Rails API Gateway Service
│   ├── Dockerfile                     # Rails container config
│   ├── Gemfile                        # Ruby dependencies
│   ├── Gemfile.lock                   # Locked dependencies
│   ├── Rakefile                       # Rake tasks
│   ├── config.ru                      # Rack config
│   ├── .env.example                   # Environment template
│   │
│   ├── app/
│   │   ├── controllers/
│   │   │   ├── application_controller.rb
│   │   │   ├── health_controller.rb           # Health check endpoint
│   │   │   └── api/
│   │   │       └── v1/
│   │   │           └── questions_controller.rb # Main API endpoint
│   │   │
│   │   ├── models/
│   │   │   └── shop.rb                        # Shop/store model
│   │   │
│   │   └── services/
│   │       └── python_ai_client.rb            # Python service HTTP client
│   │
│   ├── config/
│   │   ├── application.rb             # Rails app configuration
│   │   ├── boot.rb                    # Boot process
│   │   ├── environment.rb             # Environment loader
│   │   ├── routes.rb                  # API routes
│   │   ├── database.yml               # Database configuration
│   │   └── puma.rb                    # Puma server config
│   │
│   ├── db/
│   │   ├── migrate/
│   │   │   └── 20260105000001_create_shops.rb # Shop table migration
│   │   └── seeds.rb                   # Seed data (demo store)
│   │
│   └── spec/                          # RSpec tests
│       ├── spec_helper.rb
│       ├── rails_helper.rb
│       └── requests/
│           └── api/
│               └── v1/
│                   └── questions_spec.rb      # API integration tests
│
├── ai_service/                        # Python AI Service
│   ├── Dockerfile                     # Python container config
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Environment template
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application
│   │   │
│   │   ├── models/                    # Pydantic models
│   │   │   ├── __init__.py
│   │   │   └── query.py               # Request/response models
│   │   │
│   │   ├── agent/                     # Agentic workflow components
│   │   │   ├── __init__.py
│   │   │   ├── workflow.py            # Main 5-step workflow orchestrator
│   │   │   ├── intent_classifier.py   # Step 1: Intent classification
│   │   │   ├── query_generator.py     # Step 3: ShopifyQL generation
│   │   │   ├── validator.py           # Step 4: Query validation
│   │   │   └── answer_formatter.py    # Step 5: Answer formatting
│   │   │
│   │   └── shopify/                   # Shopify integration
│   │       ├── __init__.py
│   │       ├── client.py              # Shopify API client (mock/real)
│   │       └── mock_data.py           # Mock data generator
│   │
│   └── tests/                         # Pytest tests
│       ├── __init__.py
│       └── test_workflow.py           # Workflow integration tests
│
└── .git/                              # Git repository
```

## Key Files Explained

### Root Level

- **README.md**: Main entry point with setup instructions, features, and overview
- **ARCHITECTURE.md**: Deep dive into system design, data flow, and architecture decisions
- **API_EXAMPLES.md**: Comprehensive API usage examples with curl commands
- **docker-compose.yml**: Orchestrates Rails, Python, and PostgreSQL services
- **setup.sh**: One-command setup script for quick start

### Rails API Service

**Controllers:**
- `questions_controller.rb`: Main endpoint for processing analytics questions
  - Validates input
  - Looks up shop credentials
  - Forwards to Python service
  - Returns formatted response

- `health_controller.rb`: Health check endpoint with database status

**Models:**
- `shop.rb`: ActiveRecord model for storing shop credentials
  - Validates shop_domain format
  - Stores access_token for Shopify API

**Services:**
- `python_ai_client.rb`: HTTP client for communicating with Python service
  - Handles timeouts and retries
  - Formats requests/responses
  - Error handling

**Configuration:**
- `routes.rb`: Defines API endpoints
- `application.rb`: Rails app settings, CORS configuration
- `database.yml`: PostgreSQL connection settings

**Database:**
- `create_shops.rb`: Migration for shops table
- `seeds.rb`: Creates demo store for testing

**Tests:**
- `questions_spec.rb`: Request specs testing full API flow

### Python AI Service

**Main Application:**
- `main.py`: FastAPI app with health check and query endpoints

**Models:**
- `query.py`: Pydantic models for request/response validation
  - QueryRequest: Input validation
  - QueryResponse: Structured output
  - Metadata models: Intent, planning, validation details

**Agent Workflow** (5-Step Process):

1. **workflow.py**: Orchestrates the complete agent flow
   - Executes all 5 steps in sequence
   - Manages data passing between steps
   - Handles errors and logging

2. **intent_classifier.py**: Step 1 - Intent Classification
   - Classifies question category (sales/inventory/customers)
   - Extracts time periods using regex patterns
   - Identifies entities (product names)
   - Determines required metrics

3. **query_generator.py**: Step 3 - ShopifyQL Generation
   - Generates SQL-like queries based on intent
   - Applies time filters
   - Handles entity filtering
   - Creates appropriate aggregations

4. **validator.py**: Step 4 - Query Validation
   - Allowlist validation (safe tables and operations)
   - SQL injection prevention
   - Read-only enforcement
   - Syntax checking

5. **answer_formatter.py**: Step 5 - Answer Formatting
   - Converts raw data to business insights
   - Adds context and recommendations
   - Calculates confidence scores
   - Generates actionable summaries

**Shopify Integration:**
- `client.py`: Shopify API adapter
  - Mock mode: Uses mock data generator
  - Real mode: Skeleton for actual Shopify API calls
  - OAuth flow helpers

- `mock_data.py`: Deterministic mock data
  - 10 sample products
  - 90 days of orders
  - 20 customers
  - Realistic inventory levels

**Tests:**
- `test_workflow.py`: Integration tests for complete workflow
  - Tests different question types
  - Validates response structure
  - Checks confidence scoring

## Data Flow

```
1. Client Request
   ↓
2. Rails API (Port 3000)
   - Validate input
   - Lookup shop in PostgreSQL
   ↓
3. Python AI Service (Port 8000)
   - Step 1: Classify intent
   - Step 2: Plan data sources (in workflow.py)
   - Step 3: Generate ShopifyQL
   - Step 4: Validate & execute
   - Step 5: Format answer
   ↓
4. Shopify Client
   - Execute query (mock or real)
   - Return raw data
   ↓
5. Response back through Rails to client
```

## Configuration Files

### Environment Variables

**Rails (.env):**
- `DATABASE_URL`: PostgreSQL connection
- `PYTHON_AI_SERVICE_URL`: Python service endpoint
- `RAILS_ENV`: Environment (development/production)

**Python (.env):**
- `SHOPIFY_MODE`: mock or real
- `LOG_LEVEL`: Logging verbosity

### Docker

**docker-compose.yml:**
- Defines 3 services: db, rails_api, ai_service
- Sets up networking between services
- Configures volumes for persistence
- Maps ports for external access

## Adding New Features

### New Question Type

1. Update `intent_classifier.py`: Add keywords and patterns
2. Update `query_generator.py`: Add query template
3. Update `answer_formatter.py`: Add formatting logic
4. Add mock data in `mock_data.py` if needed
5. Add test case in `test_workflow.py`

### New Data Source

1. Add to `ALLOWED_TABLES` in `validator.py`
2. Update planning logic in `workflow.py`
3. Add mock data generator in `mock_data.py`
4. Update query templates in `query_generator.py`

### Real Shopify Integration

1. Set `SHOPIFY_MODE=real` in `.env`
2. Add Shopify credentials
3. Implement `_execute_real_query()` in `client.py`
4. Add OAuth endpoints in Rails
5. Test with real store

## Security Considerations

- Access tokens stored in database (should be encrypted in production)
- Query validation prevents SQL injection
- CORS configured for API access
- Allowlist approach for safe operations
- Read-only database operations enforced

## Performance Optimization

Current:
- Single-threaded request processing
- No caching layer
- Synchronous workflow execution

Future enhancements:
- Redis caching for frequent queries
- Async workflow with Celery
- Connection pooling
- Query result caching (5-15 min TTL)

## Testing Strategy

**Rails:**
- Request specs for API endpoints
- Model validation tests
- Service integration tests

**Python:**
- Unit tests for each agent component
- Integration tests for full workflow
- Mock data validation

**End-to-End:**
- Docker Compose environment
- Realistic user scenarios
- Performance benchmarks
