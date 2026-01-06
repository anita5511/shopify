# Real Shopify Integration Setup

Complete guide to set up the app with your real Shopify store.

## Prerequisites

1. ✅ Shopify Partner account
2. ✅ Your credentials (already provided):
   - API Key: `9a7bafac3a952dd027308e98ad1b7aac`
   - API Secret: `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`
   - Shop: `ani-15122023.myshopify.com`
3. ✅ ngrok or public domain for OAuth callback
4. LLM API key (OpenAI, Anthropic, or Google)

## Step 1: Configure Environment Variables

Your credentials are already set in `rails_api/.env` and the system is configured!

### Rails Environment (`rails_api/.env`)
```bash
# Already configured ✅
SHOPIFY_API_KEY=9a7bafac3a952dd027308e98ad1b7aac
SHOPIFY_API_SECRET=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
SHOPIFY_SCOPES=read_all_orders,read_customers,read_inventory,read_orders,read_products
SHOPIFY_REDIRECT_URI=https://abcd.ngrok-free.app/api/v1/auth/shopify/callback
SHOPIFY_APP_URL=https://abcd.ngrok-free.app
SHOPIFY_SHOP=ani-15122023.myshopify.com
```

### Python Environment (`ai_service/.env`)

**Choose your LLM provider:**

**Option 1: OpenAI (Recommended)**
```bash
SHOPIFY_MODE=real
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-your-openai-key-here
```

**Option 2: Anthropic Claude**
```bash
SHOPIFY_MODE=real
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=your-anthropic-key-here
```

**Option 3: Google Gemini**
```bash
SHOPIFY_MODE=real
LLM_PROVIDER=google
LLM_MODEL=gemini-pro
GOOGLE_API_KEY=your-google-key-here
```

**Option 4: Pattern-based (No LLM)**
```bash
SHOPIFY_MODE=real
LLM_PROVIDER=pattern
```

## Step 2: Set Up ngrok (if using local development)

```bash
# Install ngrok
# Mac: brew install ngrok
# Linux: snap install ngrok

# Start ngrok tunnel
ngrok http 3000

# Update your .env with the ngrok URL
# Example: https://abcd.ngrok-free.app
```

## Step 3: Update Shopify App Settings

1. Go to your Shopify Partner Dashboard
2. Navigate to your app settings
3. Update the following:
   - **App URL**: `https://abcd.ngrok-free.app`
   - **Allowed redirection URL(s)**: 
     ```
     https://abcd.ngrok-free.app/api/v1/auth/shopify/callback
     ```

## Step 4: Start the Application

```bash
# Rebuild with real mode
docker-compose down
docker-compose up --build
```

Check services are running:
```bash
curl http://localhost:3000/health
curl http://localhost:8000/health
```

## Step 5: Install App on Your Store

### Method 1: Direct Installation URL

Visit:
```
https://abcd.ngrok-free.app/api/v1/auth/shopify/install?shop=ani-15122023.myshopify.com
```

This will return:
```json
{
  "authorization_url": "https://ani-15122023.myshopify.com/admin/oauth/authorize?...",
  "message": "Redirect user to this URL to authorize the app"
}
```

Copy the `authorization_url` and visit it in your browser.

### Method 2: Using curl

```bash
# Get installation URL
curl "http://localhost:3000/api/v1/auth/shopify/install?shop=ani-15122023.myshopify.com"

# Copy the authorization_url from response and visit in browser
```

### Method 3: Direct Browser

Simply navigate to:
```
https://ani-15122023.myshopify.com/admin/oauth/authorize?client_id=9a7bafac3a952dd027308e98ad1b7aac&scope=read_all_orders,read_customers,read_inventory,read_orders,read_products&redirect_uri=https://abcd.ngrok-free.app/api/v1/auth/shopify/callback
```

## Step 6: Authorize the App

1. You'll be redirected to Shopify
2. Review the permissions requested
3. Click "Install app"
4. You'll be redirected back to your callback URL
5. The app will exchange the code for an access token
6. Token will be saved in the database

Expected response:
```json
{
  "success": true,
  "message": "Shop authenticated successfully",
  "shop_domain": "ani-15122023.myshopify.com",
  "redirect_to": "https://abcd.ngrok-free.app/dashboard?shop=ani-15122023.myshopify.com"
}
```

## Step 7: Verify Installation

Check authentication status:
```bash
curl "http://localhost:3000/api/v1/auth/shopify/status?shop=ani-15122023.myshopify.com"
```

Expected response:
```json
{
  "authenticated": true,
  "shop_domain": "ani-15122023.myshopify.com",
  "shop_name": "Ani 15122023",
  "installed_at": "2026-01-06T10:30:00Z"
}
```

## Step 8: Test with Real Data

Now you can query your actual store data!

```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "ani-15122023.myshopify.com",
    "question": "What were my top 5 selling products last week?"
  }'
```

This will:
1. ✅ Lookup your store credentials from database
2. ✅ Use LLM to classify the question (if configured)
3. ✅ Generate ShopifyQL
4. ✅ Fetch REAL data from your Shopify store via Admin API
5. ✅ Format answer with business insights
6. ✅ Use LLM to enhance the answer (if configured)

## LLM Configuration Details

### OpenAI Setup (Recommended)

1. Create account at https://platform.openai.com
2. Generate API key
3. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-proj-...
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4
   ```

**Cost**: ~$0.03 per question (GPT-4)

### Anthropic Claude Setup

1. Create account at https://console.anthropic.com
2. Generate API key
3. Add to `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   LLM_PROVIDER=anthropic
   LLM_MODEL=claude-3-sonnet-20240229
   ```

**Cost**: ~$0.015 per question (Claude 3 Sonnet)

### Google Gemini Setup

1. Get API key from https://makersuite.google.com/app/apikey
2. Add to `.env`:
   ```bash
   GOOGLE_API_KEY=AIza...
   LLM_PROVIDER=google
   LLM_MODEL=gemini-pro
   ```

**Cost**: Free tier available

### Pattern-based (No LLM)

No API key needed, uses regex and rules:
```bash
LLM_PROVIDER=pattern
```

**Cost**: Free, but less intelligent classification

## Features with Real Shopify + LLM

### What Works Now

✅ **OAuth Authentication**
- Full authorization flow
- Token storage and retrieval
- HMAC signature verification

✅ **Real Data Fetching**
- Orders from Shopify Admin API
- Products and inventory
- Customer data
- Respects date filters

✅ **LLM-Powered Intent Classification**
- More accurate than pattern matching
- Handles complex questions
- Better entity extraction
- Understands context

✅ **LLM-Enhanced Answers**
- More natural language
- Better business insights
- Actionable recommendations
- Context-aware responses

### Example with LLM

**Without LLM** (Pattern-based):
```
Your top 5 products last week were:
1. Product A - 45 units
2. Product B - 38 units
...
```

**With LLM** (GPT-4 or Claude):
```
Great news! Your sales performance last week was strong. Here's what's trending:

🏆 Best Performers:
1. Product A dominated with 45 units sold - this is 20% above your weekly average. 
   Consider featuring it prominently on your homepage.
2. Product B showed consistent demand with 38 units...

💡 Insights:
- Your top 3 products account for 65% of sales volume
- Strong performance suggests increasing inventory for Product A
- Consider bundling Product A with complementary items

Next Steps: Review your marketing strategy for these top performers and 
ensure adequate stock levels for the upcoming week.
```

## Switching Between Mock and Real Mode

### Use Mock Mode (Development/Testing)
```bash
# In ai_service/.env
SHOPIFY_MODE=mock
```

Benefits:
- No API calls to Shopify
- Instant responses
- Deterministic data
- No rate limits

### Use Real Mode (Production)
```bash
# In ai_service/.env
SHOPIFY_MODE=real
```

Benefits:
- Actual store data
- Real-time insights
- Production accuracy

## Troubleshooting

### OAuth Installation Issues

**Problem**: "Invalid client_id"
**Solution**: Verify `SHOPIFY_API_KEY` matches your Partner Dashboard

**Problem**: "Redirect URI mismatch"
**Solution**: Ensure `SHOPIFY_REDIRECT_URI` exactly matches app settings

**Problem**: "Invalid HMAC"
**Solution**: Check `SHOPIFY_API_SECRET` is correct

### API Call Issues

**Problem**: "Unauthorized" errors
**Solution**: 
```bash
# Check token is stored
curl "http://localhost:3000/api/v1/auth/shopify/status?shop=ani-15122023.myshopify.com"

# Re-authenticate if needed
# Visit install URL again
```

**Problem**: "Rate limit exceeded"
**Solution**: Shopify has rate limits. The app respects them automatically.

**Problem**: "No data returned"
**Solution**: Check your store has orders/products in the requested time range

### LLM Issues

**Problem**: "LLM classification failed"
**Solution**: App falls back to pattern-based automatically. Check API key.

**Problem**: High costs
**Solution**: Switch to cheaper model or use `LLM_PROVIDER=pattern`

## Testing Real Integration

### 1. Test OAuth Flow
```bash
# Start fresh
docker-compose exec rails_api rails db:reset

# Install app
curl "http://localhost:3000/api/v1/auth/shopify/install?shop=ani-15122023.myshopify.com"
# Visit the authorization_url

# Check status
curl "http://localhost:3000/api/v1/auth/shopify/status?shop=ani-15122023.myshopify.com"
```

### 2. Test Data Fetching
```bash
# Sales query
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "ani-15122023.myshopify.com",
    "question": "What were my sales last week?"
  }'

# Inventory query
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "ani-15122023.myshopify.com",
    "question": "Which products are low in stock?"
  }'

# Customer query
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "ani-15122023.myshopify.com",
    "question": "Who are my repeat customers?"
  }'
```

### 3. Compare LLM vs Pattern

**With LLM** (`LLM_PROVIDER=openai`):
- Better intent classification
- Enhanced answers with insights
- More natural language

**With Pattern** (`LLM_PROVIDER=pattern`):
- Faster responses
- No API costs
- Deterministic behavior

## Production Deployment

For production deployment:

1. Replace ngrok with real domain
2. Set up SSL/TLS
3. Use production database (not Docker container)
4. Enable rate limiting
5. Add monitoring (Datadog, New Relic)
6. Implement caching layer (Redis)
7. Scale horizontally behind load balancer

See ARCHITECTURE.md for detailed production considerations.

## Summary

You now have:
- ✅ Real Shopify OAuth integration
- ✅ Access to your store's actual data
- ✅ LLM-powered intent classification (optional)
- ✅ LLM-enhanced answer formatting (optional)
- ✅ Production-ready architecture

The system works in both mock and real modes, with or without LLM, giving you maximum flexibility!
