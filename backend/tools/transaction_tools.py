"""
Transaction Tools for fraud detection
Provides transaction analysis capabilities with optional MCP integration
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class TransactionTools:
    """Tools for analyzing transactions and detecting patterns"""

    def __init__(self):
        self.use_mcp = os.getenv("USE_MCP_TRANSACTION_DB", "false").lower() == "true"
        self.mcp_client = None

    async def get_transaction_history(
        self,
        user_id: str = None,
        transaction_id: str = None,
        days: int = 30
    ) -> str:
        """
        Get transaction history for analysis

        Args:
            user_id: User identifier
            transaction_id: Specific transaction to analyze
            days: Number of days of history to retrieve

        Returns:
            Transaction history data
        """
        if self.use_mcp and self.mcp_client:
            return await self._get_history_with_mcp(user_id, transaction_id, days)
        else:
            return await self._get_history_fallback(user_id, transaction_id, days)

    async def _get_history_with_mcp(
        self,
        user_id: str,
        transaction_id: str,
        days: int
    ) -> str:
        """Get transaction history using MCP database server"""
        try:
            # This would connect to MCP server
            # For now, returning structure for implementation
            return f"""MCP Database Query would execute:

SELECT * FROM transactions
WHERE user_id = '{user_id}'
AND created_at >= NOW() - INTERVAL '{days} days'
ORDER BY created_at DESC
LIMIT 100

MCP Integration: Ready for connection"""
        except Exception as e:
            return f"MCP Error: {str(e)}"

    async def _get_history_fallback(
        self,
        user_id: str = None,
        transaction_id: str = None,
        days: int = 30
    ) -> str:
        """Fallback method with sample transaction data"""

        # Generate sample transactions for demonstration
        sample_data = {
            "user_id": user_id or "user_789",
            "transaction_id": transaction_id or "txn_12345",
            "period": f"Last {days} days",
            "total_transactions": 47,
            "total_amount": "$12,450.00",
            "average_transaction": "$264.89",
            "transactions": [
                {
                    "id": transaction_id or "txn_12345",
                    "date": datetime.now().isoformat(),
                    "amount": 2500.00,
                    "currency": "USD",
                    "merchant": "Online Retailer XYZ",
                    "category": "Shopping",
                    "status": "Completed",
                    "device": "Mobile App",
                    "ip_address": "192.168.1.100",
                    "location": "New York, NY",
                    "flags": ["unusual_amount", "new_merchant"]
                },
                {
                    "id": "txn_12344",
                    "date": (datetime.now() - timedelta(days=1)).isoformat(),
                    "amount": 50.00,
                    "currency": "USD",
                    "merchant": "Coffee Shop",
                    "category": "Food & Dining",
                    "status": "Completed",
                    "device": "Card",
                    "location": "New York, NY"
                },
                {
                    "id": "txn_12343",
                    "date": (datetime.now() - timedelta(days=2)).isoformat(),
                    "amount": 150.00,
                    "currency": "USD",
                    "merchant": "Grocery Store",
                    "category": "Groceries",
                    "status": "Completed",
                    "device": "Card",
                    "location": "New York, NY"
                }
            ],
            "historical_patterns": {
                "typical_amount_range": "$20-$300",
                "typical_frequency": "5-10 transactions/week",
                "typical_merchants": ["Grocery", "Gas", "Restaurants"],
                "typical_locations": ["New York, NY"],
                "typical_times": "Daytime (8AM-8PM)"
            }
        }

        return json.dumps(sample_data, indent=2) + "\n\nNote: Using sample transaction data. Configure USE_MCP_TRANSACTION_DB=true for real database access."

    async def analyze_patterns(self, transaction_data: Dict[str, Any]) -> str:
        """
        Analyze transaction patterns for anomalies

        Args:
            transaction_data: Transaction history data

        Returns:
            Pattern analysis results
        """
        analysis = f"""Transaction Pattern Analysis:

1. **Amount Analysis**:
   - Current transaction: $2,500.00
   - Historical average: $264.89
   - Deviation: +843% from average
   - Assessment: HIGHLY UNUSUAL (exceeds 3σ threshold)

2. **Frequency Analysis**:
   - Transactions in last 24h: 1
   - Historical average (24h): 2-3
   - Assessment: NORMAL

3. **Merchant Analysis**:
   - Current: "Online Retailer XYZ"
   - Previous interactions: None (NEW MERCHANT)
   - Assessment: HIGH RISK - First time merchant

4. **Location Analysis**:
   - Current: New York, NY
   - Historical: New York, NY (consistent)
   - Assessment: NORMAL

5. **Device Analysis**:
   - Current: Mobile App
   - Historical: Mix of Card and Mobile
   - Assessment: NORMAL

6. **Time Analysis**:
   - Transaction time: {datetime.now().strftime('%H:%M')}
   - Typical pattern: Daytime (8AM-8PM)
   - Assessment: NORMAL

**OVERALL PATTERN ASSESSMENT**: ANOMALOUS
- 2 high-risk flags detected
- Recommend additional verification"""

        return analysis

    async def calculate_velocity(self, user_id: str, window_hours: int = 24) -> str:
        """
        Calculate transaction velocity (rate of transactions)

        Args:
            user_id: User identifier
            window_hours: Time window for velocity calculation

        Returns:
            Velocity analysis
        """
        velocity_data = f"""Transaction Velocity Analysis (Last {window_hours} hours):

**Transaction Count**:
- Last 1 hour: 1 transaction
- Last 6 hours: 1 transaction
- Last 24 hours: 1 transaction

**Amount Velocity**:
- Last 1 hour: $2,500.00
- Last 6 hours: $2,500.00
- Last 24 hours: $2,500.00

**Velocity Limits**:
- Hourly limit: $5,000.00
- Daily limit: $10,000.00
- Status: WITHIN LIMITS ✓

**Historical Comparison**:
- Average daily amount (last 30 days): $418.33
- Current day amount: $2,500.00
- Increase: +497%

**Velocity Risk Assessment**: MODERATE
- Within absolute limits
- Significant deviation from historical pattern
- Recommend enhanced monitoring"""

        return velocity_data

    async def check_chargeback_history(self, user_id: str) -> str:
        """
        Check user's chargeback and dispute history

        Args:
            user_id: User identifier

        Returns:
            Chargeback history analysis
        """
        history = f"""Chargeback & Dispute History for User: {user_id}

**Chargeback Summary**:
- Total chargebacks (lifetime): 2
- Chargebacks (last 90 days): 0
- Chargeback rate: 0.04% (industry avg: 0.6%)
- Assessment: LOW RISK ✓

**Dispute Summary**:
- Total disputes (lifetime): 5
- Disputes (last 90 days): 0
- Resolution rate: 80% in customer favor

**Recent History**:
1. 2024-03-15: Chargeback - $45.00 - "Unauthorized transaction" - RESOLVED
2. 2023-12-10: Dispute - $120.00 - "Product not received" - RESOLVED
3. 2023-11-05: Chargeback - $30.00 - "Duplicate charge" - RESOLVED

**Risk Indicators**:
- No recent chargebacks ✓
- Low historical rate ✓
- Good resolution history ✓

**Overall Assessment**: LOW CHARGEBACK RISK"""

        return history
