from typing import Dict, Any, List
import logging
from app.agent.llm_client import LLMClient

logger = logging.getLogger(__name__)

class AnswerFormatter:
    """
    Step 5: Format raw data into business-friendly answers
    
    Converts technical query results into clear, actionable insights
    Can use LLM to enhance answers with better business language
    """
    
    def __init__(self):
        """Initialize with LLM client for answer enhancement"""
        self.llm_client = LLMClient()
    
    async def format(self, question: str, intent_result: Dict[str, Any], 
               raw_data: List[Dict], shopifyql: str) -> Dict[str, Any]:
        """
        Format raw query results into a business-friendly answer
        
        Args:
            question: Original user question
            intent_result: Classified intent
            raw_data: Raw query results
            shopifyql: The executed query
            
        Returns:
            Dict with 'answer' and 'confidence'
        """
        category = intent_result['category']
        metrics = intent_result.get('metrics', [])
        
        # Route to appropriate formatter
        if category == 'sales':
            result = self._format_sales_answer(question, intent_result, raw_data)
        elif category == 'inventory':
            result = self._format_inventory_answer(question, intent_result, raw_data)
        elif category == 'customers':
            result = self._format_customer_answer(question, intent_result, raw_data)
        else:
            result = self._format_general_answer(question, intent_result, raw_data)
        
        # Try to enhance answer with LLM if available
        try:
            data_summary = f"{len(raw_data)} rows, category: {category}, metrics: {metrics}"
            enhanced_answer = await self.llm_client.enhance_answer(
                result['answer'], 
                question, 
                data_summary
            )
            result['answer'] = enhanced_answer
            logger.info("Answer enhanced with LLM")
        except Exception as e:
            logger.debug(f"LLM enhancement skipped: {e}")
            # Keep original answer if enhancement fails
        
        return result
    
    def _format_sales_answer(self, question: str, intent_result: Dict, raw_data: List[Dict]) -> Dict[str, Any]:
        """Format sales-related answers"""
        metrics = intent_result.get('metrics', [])
        
        if not raw_data:
            return {
                'answer': "No sales data found for the specified period. This could mean no orders were placed during this time.",
                'confidence': 'low'
            }
        
        if 'top_products' in metrics:
            # Format top selling products
            answer_lines = [f"Your top {min(len(raw_data), 5)} selling products"]
            
            time_period = intent_result.get('time_period', {})
            if time_period:
                period_str = self._format_time_period(time_period)
                answer_lines[0] += f" {period_str} were:\n"
            else:
                answer_lines[0] += " were:\n"
            
            total_revenue = 0
            for i, item in enumerate(raw_data[:5], 1):
                product_name = item.get('product_title', 'Unknown Product')
                quantity = item.get('total_sold', 0)
                answer_lines.append(f"{i}. {product_name} - {quantity} units sold")
                
                if 'revenue' in item:
                    total_revenue += item['revenue']
            
            if total_revenue > 0:
                answer_lines.append(f"\nTotal revenue from these products: ${total_revenue:,.2f}")
            
            confidence = self._calculate_confidence(raw_data, time_period)
            
            return {
                'answer': '\n'.join(answer_lines),
                'confidence': confidence
            }
        
        else:
            # General sales summary
            total_orders = len(raw_data)
            total_revenue = sum(item.get('total_revenue', 0) for item in raw_data)
            
            time_period = intent_result.get('time_period', {})
            period_str = self._format_time_period(time_period)
            
            answer = f"Sales summary {period_str}:\n\n"
            answer += f"• Total orders: {total_orders}\n"
            answer += f"• Total revenue: ${total_revenue:,.2f}\n"
            answer += f"• Average order value: ${total_revenue/total_orders:,.2f}" if total_orders > 0 else ""
            
            return {
                'answer': answer,
                'confidence': 'high' if total_orders > 10 else 'medium'
            }
    
    def _format_inventory_answer(self, question: str, intent_result: Dict, raw_data: List[Dict]) -> Dict[str, Any]:
        """Format inventory-related answers"""
        metrics = intent_result.get('metrics', [])
        entities = intent_result.get('entities', [])
        
        if not raw_data:
            return {
                'answer': "No inventory data found for the specified products.",
                'confidence': 'low'
            }
        
        if 'reorder_quantity' in metrics:
            # Reorder recommendation
            item = raw_data[0] if raw_data else {}
            product_name = entities[0] if entities else item.get('product_title', 'the product')
            
            total_sold = item.get('total_sold', 0)
            avg_daily = item.get('avg_daily_sales', 0)
            
            time_period = intent_result.get('time_period', {})
            days = time_period.get('value', 30)
            
            # Calculate recommendation
            daily_rate = total_sold / days if days > 0 else 0
            
            # For future periods, project demand
            future_days = 14  # 2-week buffer
            recommended_qty = int(daily_rate * future_days * 1.2)  # 20% safety buffer
            
            answer = f"Based on the last {days} days, {product_name} sold an average of {daily_rate:.1f} units per day (total: {total_sold} units).\n\n"
            answer += f"Recommendation: Order at least {recommended_qty} units to maintain a 2-week buffer. This accounts for your typical daily sales velocity and includes a 20% safety margin."
            
            confidence = 'high' if days >= 30 else 'medium'
            
            return {
                'answer': answer,
                'confidence': confidence
            }
        
        elif 'stockout_prediction' in metrics:
            # Stockout risk analysis
            at_risk = []
            
            for item in raw_data:
                product_name = item.get('product_title', 'Unknown')
                current_stock = item.get('current_stock', 0)
                avg_daily = item.get('avg_daily_sales', 0)
                
                if avg_daily > 0:
                    days_remaining = current_stock / avg_daily
                    if days_remaining <= 7:
                        at_risk.append({
                            'name': product_name,
                            'stock': current_stock,
                            'daily': avg_daily,
                            'days': days_remaining
                        })
            
            if not at_risk:
                return {
                    'answer': "Good news! Based on recent sales velocity, none of your products are at risk of stockout in the next 7 days.",
                    'confidence': 'high'
                }
            
            answer = f"Based on recent sales velocity, {len(at_risk)} product{'s' if len(at_risk) != 1 else ''} {'are' if len(at_risk) != 1 else 'is'} at risk of stockout within 7 days:\n\n"
            
            # Categorize by risk level
            high_risk = [p for p in at_risk if p['days'] <= 5]
            medium_risk = [p for p in at_risk if 5 < p['days'] <= 7]
            
            if high_risk:
                answer += "⚠️ HIGH RISK:\n"
                for p in high_risk:
                    answer += f"• {p['name']} - Current stock: {p['stock']} units, Daily sales: {p['daily']:.1f} units (runs out in ~{p['days']:.0f} days)\n"
                answer += "\n"
            
            if medium_risk:
                answer += "⚠️ MEDIUM RISK:\n"
                for p in medium_risk:
                    answer += f"• {p['name']} - Current stock: {p['stock']} units, Daily sales: {p['daily']:.1f} units (runs out in ~{p['days']:.0f} days)\n"
            
            answer += f"\nRecommendation: Prioritize reordering {high_risk[0]['name'] if high_risk else at_risk[0]['name']} immediately."
            
            return {
                'answer': answer,
                'confidence': 'medium'
            }
        
        else:
            # General inventory status
            return {
                'answer': f"Found {len(raw_data)} products in inventory. Current stock levels are available in the data.",
                'confidence': 'high'
            }
    
    def _format_customer_answer(self, question: str, intent_result: Dict, raw_data: List[Dict]) -> Dict[str, Any]:
        """Format customer-related answers"""
        metrics = intent_result.get('metrics', [])
        
        if not raw_data:
            return {
                'answer': "No customer data found for the specified period.",
                'confidence': 'low'
            }
        
        if 'repeat_customers' in metrics:
            # Repeat customers analysis
            time_period = intent_result.get('time_period', {})
            period_str = self._format_time_period(time_period)
            
            total_repeat = len(raw_data)
            
            answer = f"You had {total_repeat} repeat customer{'s' if total_repeat != 1 else ''} {period_str}:\n\n"
            answer += "Top Repeat Customers:\n"
            
            for i, customer in enumerate(raw_data[:5], 1):
                name = customer.get('customer_name', customer.get('customer_email', 'Unknown'))
                email = customer.get('customer_email', '')
                order_count = customer.get('order_count', 0)
                total_spent = customer.get('total_spent', 0)
                
                answer += f"{i}. {name}"
                if email and email != name:
                    answer += f" ({email})"
                answer += f" - {order_count} orders, ${total_spent:,.0f} total\n"
            
            # Calculate percentage contribution
            total_revenue = sum(c.get('total_spent', 0) for c in raw_data)
            answer += f"\nThese {total_repeat} customers represent a significant portion of your revenue. Consider implementing a loyalty program to retain them!"
            
            return {
                'answer': answer,
                'confidence': 'high'
            }
        
        else:
            # General customer analysis
            top_customers = raw_data[:10]
            total_spent = sum(c.get('total_spent', 0) for c in top_customers)
            
            answer = f"Top {len(top_customers)} customers by total spending:\n\n"
            
            for i, customer in enumerate(top_customers, 1):
                email = customer.get('customer_email', 'Unknown')
                spent = customer.get('total_spent', 0)
                orders = customer.get('order_count', 0)
                
                answer += f"{i}. {email} - {orders} orders, ${spent:,.0f}\n"
            
            return {
                'answer': answer,
                'confidence': 'high'
            }
    
    def _format_general_answer(self, question: str, intent_result: Dict, raw_data: List[Dict]) -> Dict[str, Any]:
        """Format general analytics answers"""
        if not raw_data:
            return {
                'answer': "No data found for your query.",
                'confidence': 'low'
            }
        
        answer = f"Found {len(raw_data)} results for your query. Here's a summary of the top items:\n\n"
        
        for i, item in enumerate(raw_data[:5], 1):
            # Try to extract meaningful fields
            if 'product_title' in item:
                answer += f"{i}. {item['product_title']}"
                if 'total_quantity' in item:
                    answer += f" - {item['total_quantity']} units"
                if 'total_revenue' in item:
                    answer += f" - ${item['total_revenue']:,.2f}"
                answer += "\n"
        
        return {
            'answer': answer,
            'confidence': 'medium'
        }
    
    def _format_time_period(self, time_period: Dict) -> str:
        """Format time period for display"""
        if not time_period:
            return "recently"
        
        value = time_period.get('value', 0)
        unit = time_period.get('unit', 'days')
        is_future = time_period.get('future', False)
        
        if is_future:
            if value == 7:
                return "next week"
            elif value == 30:
                return "next month"
            else:
                return f"in the next {value} {unit}"
        else:
            if value == 1 and unit == 'days':
                return "yesterday"
            elif value == 7:
                return "last week"
            elif value == 30:
                return "last month"
            else:
                return f"in the last {value} {unit}"
    
    def _calculate_confidence(self, raw_data: List[Dict], time_period: Dict) -> str:
        """Calculate confidence level based on data quality"""
        if not raw_data:
            return 'low'
        
        data_count = len(raw_data)
        days = time_period.get('value', 7) if time_period else 7
        
        # High confidence: lots of data, long time period
        if data_count >= 5 and days >= 30:
            return 'high'
        
        # Medium confidence: moderate data or time period
        if data_count >= 3 and days >= 7:
            return 'medium'
        
        # Low confidence: sparse data or short time period
        return 'low'
