import os
import logging
from typing import List, Dict, Any
import httpx

from app.shopify.mock_data import MockShopifyData

logger = logging.getLogger(__name__)

class ShopifyClient:
    """
    Shopify API client with two modes:
    - mock: Returns deterministic mock data (default)
    - real: Makes actual API calls to Shopify
    """
    
    def __init__(self, store_id: str, access_token: str):
        self.store_id = store_id
        self.access_token = access_token
        self.mode = os.getenv('SHOPIFY_MODE', 'mock')
        
        if self.mode == 'mock':
            self.mock_data = MockShopifyData()
            logger.info(f"ShopifyClient initialized in MOCK mode for store: {store_id}")
        else:
            self.api_version = '2024-01'
            self.base_url = f"https://{store_id}/admin/api/{self.api_version}"
            logger.info(f"ShopifyClient initialized in REAL mode for store: {store_id}")
    
    async def execute_query(self, shopifyql: str, intent_result: Dict[str, Any]) -> List[Dict]:
        """
        Execute a ShopifyQL query
        
        Args:
            shopifyql: The query to execute
            intent_result: Intent classification result for context
            
        Returns:
            List of result rows
        """
        if self.mode == 'mock':
            return self._execute_mock_query(shopifyql, intent_result)
        else:
            return await self._execute_real_query(shopifyql)
    
    def _execute_mock_query(self, shopifyql: str, intent_result: Dict[str, Any]) -> List[Dict]:
        """Execute query against mock data"""
        category = intent_result.get('category', 'general')
        metrics = intent_result.get('metrics', [])
        time_period = intent_result.get('time_period', {})
        entities = intent_result.get('entities', [])
        
        logger.info(f"Executing mock query for category: {category}, metrics: {metrics}")
        
        # Route to appropriate mock data method
        if category == 'sales' and 'top_products' in metrics:
            return self.mock_data.get_top_products(time_period, entities)
        
        elif category == 'inventory' and 'reorder_quantity' in metrics:
            return self.mock_data.get_sales_velocity(time_period, entities)
        
        elif category == 'inventory' and 'stockout_prediction' in metrics:
            return self.mock_data.get_stockout_risks(time_period)
        
        elif category == 'customers' and 'repeat_customers' in metrics:
            return self.mock_data.get_repeat_customers(time_period)
        
        elif category == 'sales':
            return self.mock_data.get_sales_summary(time_period)
        
        elif category == 'inventory':
            return self.mock_data.get_inventory_levels(entities)
        
        elif category == 'customers':
            return self.mock_data.get_top_customers(time_period)
        
        else:
            # Default: return general analytics
            return self.mock_data.get_top_products(time_period, entities)
    
    async def _execute_real_query(self, shopifyql: str, intent_result: Dict[str, Any]) -> List[Dict]:
        """
        Execute query against real Shopify API
        Converts ShopifyQL to Shopify Admin API calls
        """
        logger.info("Executing REAL Shopify query")
        
        category = intent_result.get('category', 'general')
        time_period = intent_result.get('time_period', {})
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'X-Shopify-Access-Token': self.access_token,
                    'Content-Type': 'application/json'
                }
                
                base_url = f"https://{self.store_id}/admin/api/{self.api_version}"
                
                # Convert ShopifyQL intent to appropriate API endpoint
                if category == 'sales':
                    return await self._fetch_orders(client, base_url, headers, time_period)
                elif category == 'inventory':
                    return await self._fetch_inventory(client, base_url, headers, time_period)
                elif category == 'customers':
                    return await self._fetch_customers(client, base_url, headers, time_period)
                else:
                    return await self._fetch_orders(client, base_url, headers, time_period)
                    
        except httpx.HTTPError as e:
            logger.error(f"Shopify API error: {str(e)}")
            raise
    
    async def _fetch_orders(self, client, base_url: str, headers: dict, time_period: dict) -> List[Dict]:
        """Fetch orders from Shopify API"""
        # Calculate date range
        from datetime import datetime, timedelta
        
        days = time_period.get('value', 7) if time_period else 7
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Fetch orders
        response = await client.get(
            f"{base_url}/orders.json",
            headers=headers,
            params={
                'status': 'any',
                'created_at_min': start_date,
                'limit': 250
            },
            timeout=30.0
        )
        
        response.raise_for_status()
        orders_data = response.json()['orders']
        
        # Transform to our format
        results = []
        for order in orders_data:
            for item in order.get('line_items', []):
                results.append({
                    'order_id': order['id'],
                    'product_id': item.get('product_id'),
                    'product_title': item.get('title'),
                    'customer_id': order.get('customer', {}).get('id'),
                    'customer_email': order.get('customer', {}).get('email'),
                    'customer_name': f"{order.get('customer', {}).get('first_name', '')} {order.get('customer', {}).get('last_name', '')}".strip(),
                    'quantity': item.get('quantity', 1),
                    'total_price': float(item.get('price', 0)),
                    'created_at': order['created_at']
                })
        
        logger.info(f"Fetched {len(results)} order line items from Shopify")
        return results
    
    async def _fetch_inventory(self, client, base_url: str, headers: dict, time_period: dict) -> List[Dict]:
        """Fetch inventory from Shopify API"""
        # First get products
        response = await client.get(
            f"{base_url}/products.json",
            headers=headers,
            params={'limit': 250},
            timeout=30.0
        )
        
        response.raise_for_status()
        products = response.json()['products']
        
        results = []
        for product in products:
            for variant in product.get('variants', []):
                results.append({
                    'product_id': product['id'],
                    'product_title': product['title'],
                    'sku': variant.get('sku'),
                    'quantity': variant.get('inventory_quantity', 0)
                })
        
        logger.info(f"Fetched {len(results)} inventory items from Shopify")
        return results
    
    async def _fetch_customers(self, client, base_url: str, headers: dict, time_period: dict) -> List[Dict]:
        """Fetch customers from Shopify API"""
        response = await client.get(
            f"{base_url}/customers.json",
            headers=headers,
            params={'limit': 250},
            timeout=30.0
        )
        
        response.raise_for_status()
        customers = response.json()['customers']
        
        results = []
        for customer in customers:
            results.append({
                'customer_id': customer['id'],
                'customer_email': customer.get('email'),
                'customer_name': f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                'total_spent': float(customer.get('total_spent', 0)),
                'order_count': customer.get('orders_count', 0)
            })
        
        logger.info(f"Fetched {len(results)} customers from Shopify")
        return results
    
    def _convert_to_graphql(self, shopifyql: str) -> str:
        """
        Convert ShopifyQL to Shopify GraphQL
        
        This is a placeholder - real implementation would need proper query translation
        """
        # TODO: Implement ShopifyQL -> GraphQL conversion
        pass
    
    # Methods for OAuth flow (real mode)
    
    @staticmethod
    def get_authorization_url(shop_domain: str, api_key: str, redirect_uri: str, scopes: List[str]) -> str:
        """
        Generate OAuth authorization URL
        
        Usage:
            url = ShopifyClient.get_authorization_url(
                shop_domain='example.myshopify.com',
                api_key='your_api_key',
                redirect_uri='https://yourapp.com/auth/callback',
                scopes=['read_products', 'read_orders']
            )
        """
        scope_string = ','.join(scopes)
        return (
            f"https://{shop_domain}/admin/oauth/authorize?"
            f"client_id={api_key}&"
            f"scope={scope_string}&"
            f"redirect_uri={redirect_uri}"
        )
    
    @staticmethod
    async def exchange_code_for_token(shop_domain: str, api_key: str, api_secret: str, code: str) -> str:
        """
        Exchange authorization code for access token
        
        Args:
            shop_domain: Store domain
            api_key: Your app's API key
            api_secret: Your app's API secret
            code: Authorization code from OAuth callback
            
        Returns:
            Access token
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{shop_domain}/admin/oauth/access_token",
                json={
                    'client_id': api_key,
                    'client_secret': api_secret,
                    'code': code
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['access_token']
            else:
                raise Exception(f"Failed to exchange code: {response.text}")
