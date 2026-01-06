import logging
import time
from typing import Dict, Any

from app.models.query import QueryResponse, QueryMetadata, IntentDetails, PlanningDetails, ValidationDetails, DataQuality
from app.agent.intent_classifier import IntentClassifier
from app.agent.query_generator import QueryGenerator
from app.agent.validator import QueryValidator
from app.agent.answer_formatter import AnswerFormatter
from app.shopify.client import ShopifyClient

logger = logging.getLogger(__name__)

class AgentWorkflow:
    """
    5-Step Agentic Workflow:
    1. Classify intent
    2. Plan data sources
    3. Generate ShopifyQL
    4. Validate & execute
    5. Format answer
    """
    
    def __init__(self, store_id: str, access_token: str):
        self.store_id = store_id
        self.access_token = access_token
        self.shopify_client = ShopifyClient(store_id, access_token)
        
        # Initialize workflow components
        self.intent_classifier = IntentClassifier()
        self.query_generator = QueryGenerator()
        self.validator = QueryValidator()
        self.answer_formatter = AnswerFormatter()
    
    async def execute(self, question: str) -> QueryResponse:
        """Execute the complete agentic workflow"""
        start_time = time.time()
        
        try:
            # STEP 1: Classify Intent
            logger.info("Step 1: Classifying intent...")
            intent_result = await self.intent_classifier.classify(question)
            logger.info(f"Intent classified as: {intent_result['category']}")
            
            # STEP 2: Plan Data Sources
            logger.info("Step 2: Planning data sources...")
            planning = self._plan_data_sources(intent_result)
            logger.info(f"Data sources needed: {planning['data_sources']}")
            
            # STEP 3: Generate ShopifyQL
            logger.info("Step 3: Generating ShopifyQL...")
            shopifyql = self.query_generator.generate(intent_result, planning)
            logger.info(f"Generated query: {shopifyql[:100]}...")
            
            # STEP 4: Validate & Execute
            logger.info("Step 4: Validating and executing query...")
            validation_result = self.validator.validate(shopifyql)
            
            if not validation_result['passed']:
                raise ValueError(f"Query validation failed: {validation_result.get('reason', 'Unknown error')}")
            
            # Execute query
            raw_data = await self.shopify_client.execute_query(shopifyql, intent_result)
            logger.info(f"Query executed, returned {len(raw_data)} rows")
            
            # STEP 5: Format Answer
            logger.info("Step 5: Formatting answer...")
            answer_result = self.answer_formatter.format(
                question=question,
                intent_result=intent_result,
                raw_data=raw_data,
                shopifyql=shopifyql
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Build complete response
            response = QueryResponse(
                answer=answer_result['answer'],
                confidence=answer_result['confidence'],
                shopifyql=shopifyql,
                intent=intent_result['category'],
                used_data_sources=planning['data_sources'],
                metadata=QueryMetadata(
                    intent_details=IntentDetails(**intent_result),
                    planning=PlanningDetails(**planning),
                    validation=ValidationDetails(**validation_result),
                    data_quality=DataQuality(
                        rows_returned=len(raw_data),
                        completeness=self._calculate_completeness(raw_data)
                    ),
                    time_period=intent_result.get('time_period'),
                    entities=intent_result.get('entities', []),
                    processing_time_ms=processing_time_ms
                )
            )
            
            logger.info(f"Workflow completed in {processing_time_ms}ms")
            return response
            
        except Exception as e:
            logger.error(f"Workflow error: {str(e)}", exc_info=True)
            raise
    
    def _plan_data_sources(self, intent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: Determine which Shopify data sources are needed
        """
        category = intent_result['category']
        metrics = intent_result.get('metrics', [])
        
        # Map intent to data sources
        data_source_map = {
            'sales': ['orders', 'products'],
            'inventory': ['inventory_levels', 'products', 'orders'],
            'customers': ['customers', 'orders'],
            'general': ['orders', 'products']
        }
        
        data_sources = data_source_map.get(category, ['orders'])
        
        # Determine required fields based on metrics
        required_fields = self._get_required_fields(category, metrics)
        
        # Determine aggregation type
        aggregation_type = self._determine_aggregation(metrics)
        
        return {
            'data_sources': data_sources,
            'required_fields': required_fields,
            'aggregation_type': aggregation_type
        }
    
    def _get_required_fields(self, category: str, metrics: List[str]) -> List[str]:
        """Determine required fields based on intent and metrics"""
        base_fields = {
            'sales': ['product_id', 'product_title', 'quantity', 'total_price', 'created_at'],
            'inventory': ['product_id', 'product_title', 'quantity', 'sku'],
            'customers': ['customer_id', 'customer_email', 'customer_name', 'total_price'],
            'general': ['product_id', 'quantity', 'created_at']
        }
        return base_fields.get(category, ['product_id', 'created_at'])
    
    def _determine_aggregation(self, metrics: List[str]) -> str:
        """Determine aggregation type from metrics"""
        if any(m in metrics for m in ['top_products', 'top_sellers']):
            return 'sum_group'
        elif any(m in metrics for m in ['stockout_prediction', 'reorder_quantity']):
            return 'projection'
        elif 'repeat_customers' in metrics:
            return 'count_group'
        else:
            return 'simple'
    
    def _calculate_completeness(self, raw_data: list) -> float:
        """Calculate data completeness score"""
        if not raw_data:
            return 0.0
        
        # Simple completeness: presence of data
        # More sophisticated: check for null values, data quality, etc.
        return 1.0 if len(raw_data) > 0 else 0.0
