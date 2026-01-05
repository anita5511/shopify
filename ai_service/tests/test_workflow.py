import pytest
from app.agent.workflow import AgentWorkflow
from app.models.query import QueryResponse

@pytest.mark.asyncio
async def test_workflow_sales_query():
    """Test complete workflow for sales query"""
    workflow = AgentWorkflow(
        store_id='test-store.myshopify.com',
        access_token='mock_token'
    )
    
    result = await workflow.execute("What were my top 5 selling products last week?")
    
    assert isinstance(result, QueryResponse)
    assert result.intent == 'sales'
    assert result.confidence in ['low', 'medium', 'high']
    assert len(result.shopifyql) > 0
    assert 'SELECT' in result.shopifyql.upper()
    assert 'orders' in result.used_data_sources

@pytest.mark.asyncio
async def test_workflow_inventory_query():
    """Test complete workflow for inventory query"""
    workflow = AgentWorkflow(
        store_id='test-store.myshopify.com',
        access_token='mock_token'
    )
    
    result = await workflow.execute("Which products will go out of stock in 7 days?")
    
    assert isinstance(result, QueryResponse)
    assert result.intent == 'inventory'
    assert 'inventory' in result.answer.lower() or 'stock' in result.answer.lower()

@pytest.mark.asyncio
async def test_workflow_customer_query():
    """Test complete workflow for customer query"""
    workflow = AgentWorkflow(
        store_id='test-store.myshopify.com',
        access_token='mock_token'
    )
    
    result = await workflow.execute("Which customers placed repeat orders in the last 90 days?")
    
    assert isinstance(result, QueryResponse)
    assert result.intent == 'customers'
    assert 'customers' in result.used_data_sources

@pytest.mark.asyncio
async def test_workflow_with_product_entity():
    """Test workflow with specific product mentioned"""
    workflow = AgentWorkflow(
        store_id='test-store.myshopify.com',
        access_token='mock_token'
    )
    
    result = await workflow.execute("How many Wireless Bluetooth Headphones did I sell last month?")
    
    assert isinstance(result, QueryResponse)
    assert result.metadata is not None
    # Check that entity was extracted
    assert len(result.metadata.entities) > 0 or 'Wireless' in result.shopifyql
