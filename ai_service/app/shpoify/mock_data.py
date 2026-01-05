from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

class MockShopifyData:
    """
    Provides deterministic mock data for development and testing
    Simulates realistic Shopify store data
    """
    
    def __init__(self):
        self.products = self._generate_products()
        self.orders = self._generate_orders()
        self.customers = self._generate_customers()
        self.inventory = self._generate_inventory()
    
    def _generate_products(self) -> List[Dict]:
        """Generate sample products"""
        return [
            {'product_id': 1, 'product_title': 'Wireless Bluetooth Headphones', 'sku': 'WBH-001', 'price': 79.99},
            {'product_id': 2, 'product_title': 'Organic Cotton T-Shirt', 'sku': 'OCT-001', 'price': 29.99},
            {'product_id': 3, 'product_title': 'Stainless Steel Water Bottle', 'sku': 'SSWB-001', 'price': 24.99},
            {'product_id': 4, 'product_title': 'Yoga Mat Pro', 'sku': 'YMP-001', 'price': 49.99},
            {'product_id': 5, 'product_title': 'Smart Watch Series 5', 'sku': 'SWS5-001', 'price': 299.99},
            {'product_id': 6, 'product_title': 'Leather Laptop Bag', 'sku': 'LLB-001', 'price': 89.99},
            {'product_id': 7, 'product_title': 'Portable Phone Charger', 'sku': 'PPC-001', 'price': 34.99},
            {'product_id': 8, 'product_title': 'Bamboo Sunglasses', 'sku': 'BS-001', 'price': 59.99},
            {'product_id': 9, 'product_title': 'Ceramic Coffee Mug Set', 'sku': 'CCMS-001', 'price': 39.99},
            {'product_id': 10, 'product_title': 'Fitness Resistance Bands', 'sku': 'FRB-001', 'price': 19.99},
        ]
    
    def _generate_orders(self) -> List[Dict]:
        """Generate sample orders over the last 90 days"""
        orders = []
        now = datetime.utcnow()
        
        # Generate orders with realistic distribution
        for day in range(90):
            date = now - timedelta(days=day)
            
            # More recent orders
            num_orders = random.randint(3, 8) if day < 30 else random.randint(1, 4)
            
            for _ in range(num_orders):
                product = random.choice(self.products)
                customer_id = random.randint(1, 20)
                quantity = random.randint(1, 3)
                
                orders.append({
                    'order_id': len(orders) + 1,
                    'product_id': product['product_id'],
                    'product_title': product['product_title'],
                    'customer_id': customer_id,
                    'customer_email': f'customer{customer_id}@email.com',
                    'customer_name': f'Customer {customer_id}',
                    'quantity': quantity,
                    'total_price': product['price'] * quantity,
                    'created_at': date.isoformat()
                })
        
        return orders
    
    def _generate_customers(self) -> List[Dict]:
        """Generate sample customers"""
        names = [
            'Sarah Johnson', 'Michael Chen', 'Emily Davis', 'James Wilson',
            'Lisa Anderson', 'David Martinez', 'Jennifer Taylor', 'Robert Brown',
            'Maria Garcia', 'William Lee', 'Amanda White', 'Christopher Moore',
            'Jessica Thomas', 'Daniel Jackson', 'Ashley Harris', 'Matthew Martin',
            'Stephanie Thompson', 'Andrew Robinson', 'Michelle Clark', 'Kevin Lewis'
        ]
        
        return [
            {
                'customer_id': i + 1,
                'customer_name': names[i],
                'customer_email': f"{names[i].lower().replace(' ', '.')}@email.com"
            }
            for i in range(len(names))
        ]
    
    def _generate_inventory(self) -> List[Dict]:
        """Generate current inventory levels"""
        inventory_levels = [45, 15, 78, 22, 12, 34, 56, 28, 41, 67]
        
        return [
            {
                'product_id': product['product_id'],
                'product_title': product['product_title'],
                'sku': product['sku'],
                'quantity': inventory_levels[i]
            }
            for i, product in enumerate(self.products)
        ]
    
    def get_top_products(self, time_period: Dict, entities: List[str]) -> List[Dict]:
        """Get top selling products"""
        days = time_period.get('value', 7) if time_period else 7
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Filter orders by date
        recent_orders = [
            o for o in self.orders 
            if datetime.fromisoformat(o['created_at']) >= cutoff_date
        ]
        
        # Filter by entities if specified
        if entities:
            recent_orders = [
                o for o in recent_orders
                if any(entity.lower() in o['product_title'].lower() for entity in entities)
            ]
        
        # Aggregate by product
        product_sales = {}
        for order in recent_orders:
            pid = order['product_id']
            if pid not in product_sales:
                product_sales[pid] = {
                    'product_id': pid,
                    'product_title': order['product_title'],
                    'total_sold': 0,
                    'revenue': 0
                }
            product_sales[pid]['total_sold'] += order['quantity']
            product_sales[pid]['revenue'] += order['total_price']
        
        # Sort by quantity sold
        result = sorted(product_sales.values(), key=lambda x: x['total_sold'], reverse=True)
        return result[:5]
    
    def get_sales_velocity(self, time_period: Dict, entities: List[str]) -> List[Dict]:
        """Get sales velocity for reorder calculations"""
        days = time_period.get('value', 30) if time_period else 30
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_orders = [
            o for o in self.orders 
            if datetime.fromisoformat(o['created_at']) >= cutoff_date
        ]
        
        # Filter by entities
        if entities:
            recent_orders = [
                o for o in recent_orders
                if any(entity.lower() in o['product_title'].lower() for entity in entities)
            ]
        
        # Aggregate
        product_sales = {}
        for order in recent_orders:
            pid = order['product_id']
            if pid not in product_sales:
                product_sales[pid] = {
                    'product_id': pid,
                    'product_title': order['product_title'],
                    'total_sold': 0
                }
            product_sales[pid]['total_sold'] += order['quantity']
        
        # Add average daily sales
        for product in product_sales.values():
            product['avg_daily_sales'] = product['total_sold'] / days
        
        return list(product_sales.values())
    
    def get_stockout_risks(self, time_period: Dict) -> List[Dict]:
        """Identify products at risk of stockout"""
        # Calculate sales velocity for last 7 days
        velocity = self.get_sales_velocity({'value': 7, 'unit': 'days'}, [])
        
        # Combine with inventory
        at_risk = []
        for vel in velocity:
            # Find corresponding inventory
            inv = next((i for i in self.inventory if i['product_id'] == vel['product_id']), None)
            if inv:
                current_stock = inv['quantity']
                daily_sales = vel['avg_daily_sales']
                
                if daily_sales > 0:
                    days_remaining = current_stock / daily_sales
                    
                    if days_remaining <= 7:
                        at_risk.append({
                            'product_id': vel['product_id'],
                            'product_title': vel['product_title'],
                            'current_stock': current_stock,
                            'avg_daily_sales': daily_sales
                        })
        
        return sorted(at_risk, key=lambda x: x['current_stock'] / x['avg_daily_sales'])
    
    def get_repeat_customers(self, time_period: Dict) -> List[Dict]:
        """Get customers with repeat orders"""
        days = time_period.get('value', 90) if time_period else 90
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_orders = [
            o for o in self.orders 
            if datetime.fromisoformat(o['created_at']) >= cutoff_date
        ]
        
        # Aggregate by customer
        customer_orders = {}
        for order in recent_orders:
            cid = order['customer_id']
            if cid not in customer_orders:
                customer_orders[cid] = {
                    'customer_id': cid,
                    'customer_email': order['customer_email'],
                    'customer_name': order['customer_name'],
                    'order_count': 0,
                    'total_spent': 0
                }
            customer_orders[cid]['order_count'] += 1
            customer_orders[cid]['total_spent'] += order['total_price']
        
        # Filter for repeat customers only (>1 order)
        repeat = [c for c in customer_orders.values() if c['order_count'] > 1]
        
        return sorted(repeat, key=lambda x: x['order_count'], reverse=True)
    
    def get_sales_summary(self, time_period: Dict) -> List[Dict]:
        """Get overall sales summary"""
        days = time_period.get('value', 7) if time_period else 7
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_orders = [
            o for o in self.orders 
            if datetime.fromisoformat(o['created_at']) >= cutoff_date
        ]
        
        # Group by date
        daily_sales = {}
        for order in recent_orders:
            date = datetime.fromisoformat(order['created_at']).date()
            if date not in daily_sales:
                daily_sales[date] = {
                    'date': date.isoformat(),
                    'order_count': 0,
                    'total_revenue': 0
                }
            daily_sales[date]['order_count'] += 1
            daily_sales[date]['total_revenue'] += order['total_price']
        
        return sorted(daily_sales.values(), key=lambda x: x['date'], reverse=True)
    
    def get_inventory_levels(self, entities: List[str]) -> List[Dict]:
        """Get current inventory levels"""
        if entities:
            return [
                i for i in self.inventory
                if any(entity.lower() in i['product_title'].lower() for entity in entities)
            ]
        return self.inventory
    
    def get_top_customers(self, time_period: Dict) -> List[Dict]:
        """Get top customers by spending"""
        days = time_period.get('value', 30) if time_period else 30
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_orders = [
            o for o in self.orders 
            if datetime.fromisoformat(o['created_at']) >= cutoff_date
        ]
        
        # Aggregate by customer
        customer_spending = {}
        for order in recent_orders:
            cid = order['customer_id']
            if cid not in customer_spending:
                customer_spending[cid] = {
                    'customer_id': cid,
                    'customer_email': order['customer_email'],
                    'customer_name': order['customer_name'],
                    'order_count': 0,
                    'total_spent': 0
                }
            customer_spending[cid]['order_count'] += 1
            customer_spending[cid]['total_spent'] += order['total_price']
        
        return sorted(customer_spending.values(), key=lambda x: x['total_spent'], reverse=True)[:10]
