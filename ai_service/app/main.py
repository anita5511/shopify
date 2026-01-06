from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import logging

from app.models.query import QueryRequest, QueryResponse
from app.agent.workflow import AgentWorkflow

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Shopify Analytics AI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ai_agent",
        "mode": os.getenv('SHOPIFY_MODE', 'mock'),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/agent/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        logger.info(f"Processing query for store: {request.store_id}")
        logger.info(f"Question: {request.question}")
        
        workflow = AgentWorkflow(
            store_id=request.store_id,
            access_token=request.access_token
        )
        
        result = await workflow.execute(request.question)
        
        logger.info(f"Query completed with confidence: {result.confidence}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
