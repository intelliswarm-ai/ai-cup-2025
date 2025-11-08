"""
Risk Tools for fraud detection
Provides risk scoring and device analysis capabilities
"""

import os
import hashlib
import httpx
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskTools:
    """Tools for calculating fraud risk scores and device analysis"""

    def __init__(self):
        self.use_mcp_memory = os.getenv("USE_MCP_MEMORY", "false").lower() == "true"
        self.ipgeolocation_api_key = os.getenv("IPGEOLOCATION_API_KEY", "")

    async def calculate_fraud_score(
        self,
        transaction_data: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> str:
        """
        Calculate comprehensive fraud risk score

        Args:
            transaction_data: Current transaction details
            user_data: User profile and history

        Returns:
            Fraud risk score and breakdown
        """
        # Simulate risk scoring algorithm
        risk_factors = {
            "amount_risk": 35,  # High amount compared to history
            "merchant_risk": 25,  # New/unknown merchant
            "device_risk": 5,    # Known device
            "location_risk": 0,  # Normal location
            "velocity_risk": 15, # Slightly elevated
            "behavioral_risk": 10,  # Some deviation from pattern
            "account_age_risk": 0,  # Established account
            "historical_fraud_risk": 0  # No fraud history
        }

        total_score = sum(risk_factors.values())

        score_analysis = f"""Fraud Risk Score Calculation:

**OVERALL RISK SCORE**: {total_score}/100

**Risk Level**: {"HIGH" if total_score >= 70 else "MEDIUM" if total_score >= 40 else "LOW"}

**Score Breakdown**:
1. Amount Risk: {risk_factors['amount_risk']}/100
   - Transaction: $2,500 vs Historical Avg: $265
   - Deviation: 843% above average
   - Weight: HIGH

2. Merchant Risk: {risk_factors['merchant_risk']}/100
   - First transaction with this merchant
   - Merchant reputation: Unknown
   - Weight: MEDIUM-HIGH

3. Device Risk: {risk_factors['device_risk']}/100
   - Device fingerprint: Known/Trusted
   - Device history: 45 days old
   - Weight: LOW

4. Location Risk: {risk_factors['location_risk']}/100
   - Location matches historical pattern
   - IP geolocation: Consistent
   - Weight: NONE

5. Velocity Risk: {risk_factors['velocity_risk']}/100
   - Transaction frequency: Normal
   - Amount velocity: Elevated but within limits
   - Weight: LOW-MEDIUM

6. Behavioral Risk: {risk_factors['behavioral_risk']}/100
   - Time of day: Normal
   - Transaction type: Slightly unusual
   - Weight: LOW

7. Account Age Risk: {risk_factors['account_age_risk']}/100
   - Account age: 3 years (established)
   - Good standing
   - Weight: NONE

8. Historical Fraud Risk: {risk_factors['historical_fraud_risk']}/100
   - Previous fraud incidents: 0
   - Chargeback rate: 0.04%
   - Weight: NONE

**RISK ASSESSMENT**: MEDIUM-HIGH RISK ({total_score}/100)

**Recommendation**: MANUAL REVIEW REQUIRED
- High amount risk triggers review threshold
- New merchant adds uncertainty
- Overall profile is good, but transaction is anomalous

**Suggested Actions**:
1. Request additional authentication (2FA)
2. Contact user to verify transaction
3. Temporary hold for 24-hour review period
4. Flag for fraud analyst attention"""

        return score_analysis

    async def check_device_fingerprint(self, device_id: str, user_id: str) -> str:
        """
        Analyze device fingerprint and reputation

        Args:
            device_id: Device identifier
            user_id: User identifier

        Returns:
            Device analysis results
        """
        # Simulate device fingerprint check
        device_hash = hashlib.md5(device_id.encode()).hexdigest()[:8]

        analysis = f"""Device Fingerprint Analysis:

**Device ID**: {device_hash}... (hashed)
**Device Type**: Mobile App (iOS)
**User Association**: {user_id}

**Device History**:
- First seen: 2024-11-20 (45 days ago)
- Total transactions: 23
- Last transaction: 2 days ago
- Status: TRUSTED ✓

**Device Characteristics**:
- OS: iOS 17.1
- App version: 2.5.3 (latest)
- Screen resolution: 1170x2532 (iPhone 13 Pro)
- Browser: Native App
- Timezone: EST (UTC-5)

**Network Analysis**:
- Current IP: 192.168.1.100
- IP reputation: Clean ✓
- VPN/Proxy detected: NO ✓
- IP location: New York, NY

**Behavioral Patterns**:
- Typical usage time: 10AM-8PM
- Current time: {datetime.now().strftime('%I:%M %p')}
- Pattern match: NORMAL ✓

**Risk Indicators**:
- Device jailbreak/root: NOT DETECTED ✓
- Emulator detected: NO ✓
- Known fraud device: NO ✓
- Suspicious changes: NO ✓

**Historical Success Rate**:
- Total transactions from device: 23
- Successful: 23 (100%)
- Declined: 0
- Chargebacks: 0

**DEVICE RISK ASSESSMENT**: LOW RISK
- Established device with good history
- No suspicious characteristics
- Consistent behavior patterns

**Recommendation**: APPROVE device verification"""

        return analysis

    async def analyze_geolocation(self, ip_address: str, location_data: Dict = None) -> str:
        """
        Analyze IP and geolocation data using real IP intelligence API

        Args:
            ip_address: IP address to analyze
            location_data: Optional location information (for fallback)

        Returns:
            Geolocation analysis
        """
        # Try real API first
        if self.ipgeolocation_api_key:
            try:
                return await self._analyze_geolocation_real(ip_address, location_data)
            except Exception as e:
                logger.warning(f"ipgeolocation.io API error: {e}, falling back to mock")
                return await self._analyze_geolocation_mock(ip_address, location_data)
        else:
            logger.info("IPGEOLOCATION_API_KEY not configured, using mock data")
            return await self._analyze_geolocation_mock(ip_address, location_data)

    async def _analyze_geolocation_real(self, ip_address: str, location_data: Dict = None) -> str:
        """
        Real IP geolocation analysis using ipgeolocation.io API
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.ipgeolocation.io/ipgeo",
                params={
                    "apiKey": self.ipgeolocation_api_key,
                    "ip": ip_address,
                    "fields": "geo,security,currency,time_zone"
                }
            )

            if response.status_code != 200:
                raise Exception(f"API returned status {response.status_code}")

            data = response.json()

            # Parse security data
            security = data.get("security", {})
            is_vpn = security.get("is_proxy", False) or security.get("is_vpn", False)
            is_tor = security.get("is_tor", False)
            is_anonymous = security.get("is_anonymous", False)
            is_known_attacker = security.get("is_known_attacker", False)
            is_cloud = security.get("is_cloud_provider", False)
            threat_score = security.get("threat_score", 0)

            # Determine risk level based on threat intelligence
            if is_tor or is_known_attacker:
                ip_risk_level = "CRITICAL"
            elif is_vpn or is_anonymous or threat_score > 70:
                ip_risk_level = "HIGH"
            elif is_cloud or threat_score > 40:
                ip_risk_level = "MEDIUM"
            else:
                ip_risk_level = "LOW"

            # Build comprehensive analysis
            analysis = f"""Geolocation & IP Analysis (REAL-TIME INTELLIGENCE):

**IP Address**: {ip_address}
**Location**: {data.get('city', 'Unknown')}, {data.get('state_prov', '')}, {data.get('country_name', 'Unknown')}

**🔴 LIVE THREAT INTELLIGENCE** (ipgeolocation.io):
- Overall Threat Score: {threat_score}/100 {'⚠️' if threat_score > 50 else '✓'}
- VPN/Proxy Detected: {'YES ⚠️' if is_vpn else 'NO ✓'}
- TOR Exit Node: {'YES 🚨' if is_tor else 'NO ✓'}
- Anonymous Network: {'YES ⚠️' if is_anonymous else 'NO ✓'}
- Known Attacker: {'YES 🚨' if is_known_attacker else 'NO ✓'}
- Cloud/Hosting IP: {'YES ⚠️' if is_cloud else 'NO ✓'}

**IP Reputation Check**:
- Reputation score: {100 - threat_score}/100 {'(Good)' if threat_score < 30 else '(Poor)' if threat_score > 70 else '(Fair)'}
- Known proxy/VPN: {'YES ⚠️' if is_vpn else 'NO ✓'}
- TOR exit node: {'YES 🚨' if is_tor else 'NO ✓'}
- Known fraud IP: {'YES 🚨' if is_known_attacker else 'NO ✓'}
- Datacenter IP: {'YES ⚠️' if is_cloud else 'NO ✓'}
- Residential IP: {'NO' if is_cloud or is_vpn else 'YES ✓'}

**Geolocation Details**:
- Country: {data.get('country_name', 'Unknown')} ({data.get('country_code2', 'XX')})
- Region: {data.get('state_prov', 'Unknown')}
- City: {data.get('city', 'Unknown')}
- Postal Code: {data.get('zipcode', 'Unknown')}
- Latitude/Longitude: {data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')}
- ISP: {data.get('isp', 'Unknown')}
- Organization: {data.get('organization', 'Unknown')}
- Connection type: {data.get('connection_type', 'Unknown')}
- Timezone: {data.get('time_zone', {}).get('name', 'Unknown')}

**Currency & Locale**:
- Currency: {data.get('currency', {}).get('name', 'Unknown')} ({data.get('currency', {}).get('code', 'XXX')})
- Languages: {data.get('languages', 'Unknown')}
- Calling Code: +{data.get('calling_code', 'N/A')}

**Risk Factors Detected**:
{f"- 🚨 TOR Network (CRITICAL RISK)" if is_tor else ""}
{f"- 🚨 Known Attacker IP (CRITICAL RISK)" if is_known_attacker else ""}
{f"- ⚠️  VPN/Proxy Detected (HIGH RISK)" if is_vpn else ""}
{f"- ⚠️  Anonymous Network (HIGH RISK)" if is_anonymous else ""}
{f"- ⚠️  Cloud/Datacenter IP (MEDIUM RISK)" if is_cloud else ""}
{f"- ⚠️  High Threat Score ({threat_score}/100)" if threat_score > 50 else ""}
{"- ✓ Clean residential IP (LOW RISK)" if not (is_vpn or is_tor or is_cloud or threat_score > 30) else ""}

**GEOLOCATION RISK**: {ip_risk_level}
**Recommendation**: {'BLOCK - High risk IP detected' if ip_risk_level in ['CRITICAL', 'HIGH'] else 'MANUAL REVIEW - Elevated risk' if ip_risk_level == 'MEDIUM' else 'Location verification PASSED'}

**Data Source**: ipgeolocation.io (Real-Time Threat Intelligence)"""

            return analysis

    async def _analyze_geolocation_mock(self, ip_address: str, location_data: Dict = None) -> str:
        """
        Fallback mock geolocation analysis
        """
        if location_data is None:
            location_data = {}

        analysis = f"""Geolocation & IP Analysis (MOCK DATA - Configure IPGEOLOCATION_API_KEY for real intelligence):

**IP Address**: {ip_address}
**Location**: {location_data.get('city', 'New York')}, {location_data.get('state', 'NY')}

**IP Reputation Check**:
- Reputation score: 95/100 (Good)
- Known proxy/VPN: NO ✓
- TOR exit node: NO ✓
- Known fraud IP: NO ✓
- Datacenter IP: NO ✓
- Residential IP: YES ✓

**Geolocation Details**:
- Country: United States
- Region: New York
- City: New York
- ISP: Verizon Fios
- Connection type: Cable/DSL
- Timezone: America/New_York

**Distance Analysis**:
- Previous transaction location: New York, NY
- Distance from last transaction: 2.3 miles
- Assessment: NORMAL (same city)

**Historical Pattern**:
- Typical locations: New York, NY
- Travel detected: NO
- Location consistency: HIGH ✓

**Velocity Check**:
- Last transaction: 48 hours ago in New York, NY
- Time to travel: N/A (same location)
- Physically possible: YES ✓

**Risk Factors**:
- IP reputation: CLEAN ✓
- Location consistency: GOOD ✓
- No impossible travel detected ✓
- ISP matches historical pattern ✓

**GEOLOCATION RISK**: LOW
**Recommendation**: Location verification PASSED"""

        return analysis

    async def check_historical_patterns(self, user_id: str) -> str:
        """
        Check historical fraud patterns using MCP memory or fallback

        Args:
            user_id: User identifier

        Returns:
            Historical pattern analysis
        """
        if self.use_mcp_memory:
            # Would query MCP memory server for similar patterns
            return "MCP Memory: Would query historical fraud patterns"

        analysis = f"""Historical Pattern Analysis for User: {user_id}

**Account Overview**:
- Account age: 3 years, 4 months
- Total transactions: 1,247
- Total volume: $187,450
- Average transaction: $150.28

**Pattern Evolution**:
- Year 1: Small purchases ($50-$200)
- Year 2: Moderate growth ($100-$500)
- Year 3: Stable pattern ($50-$300)
- Current: Unusual spike detected

**Spending Categories**:
- Groceries: 35%
- Restaurants: 20%
- Gas: 15%
- Shopping: 10%
- Other: 20%

**Fraud History**:
- Previous fraud incidents: 0 ✓
- Chargebacks filed: 2 (both legitimate)
- Disputes: 5 (resolved favorably)
- Account suspensions: 0 ✓

**Similar Pattern Search**:
- Searching for similar unusual transactions...
- Found 3 similar cases in database:
  1. Case #4521: Large purchase after stable period → FRAUD
  2. Case #4892: New merchant, high amount → LEGITIMATE (verified)
  3. Case #5234: Amount spike → FRAUD

**Pattern Match Analysis**:
- Current transaction resembles: Case #4521 (60% match)
- Risk indication: ELEVATED
- Historical false positive rate: 40%

**Behavioral Consistency**:
- Time patterns: CONSISTENT ✓
- Location patterns: CONSISTENT ✓
- Amount patterns: INCONSISTENT ⚠️
- Merchant patterns: NEW MERCHANT ⚠️

**PATTERN RISK ASSESSMENT**: MODERATE-HIGH
- 2 out of 4 key patterns are anomalous
- Historical similar cases: 67% fraud rate
- Recommend: Enhanced verification

**Memory Note**: Configure USE_MCP_MEMORY=true for enhanced pattern matching"""

        return analysis
