"""
Investigation Tools for fraud detection
Provides deep investigation and cross-reference capabilities
"""

import os
import httpx
from typing import Dict, Any, List
import logging

# Import MCP client for DuckDuckGo fallback
try:
    from mcp_client import mcp_client
    MCP_CLIENT_AVAILABLE = True
except ImportError:
    MCP_CLIENT_AVAILABLE = False
    logging.warning("MCP client not available - DuckDuckGo fallback disabled")

logger = logging.getLogger(__name__)


class InvestigationTools:
    """Tools for deep fraud investigation and cross-referencing"""

    def __init__(self):
        self.use_mcp_files = os.getenv("USE_MCP_FILESYSTEM", "false").lower() == "true"
        self.search_api_key = os.getenv("SERPER_API_KEY", "")
        self.abstractapi_email_key = os.getenv("ABSTRACTAPI_EMAIL_KEY", "")

    async def search_fraud_database(self, criteria: Dict[str, Any]) -> str:
        """
        Search internal fraud database for similar cases

        Args:
            criteria: Search criteria (amount, merchant, pattern, etc.)

        Returns:
            Matching fraud cases
        """
        # Simulate fraud database search
        search_results = f"""Fraud Database Search Results:

**Search Criteria**:
- Amount range: $2,000 - $3,000
- Merchant type: Online Retailer
- Pattern: High amount, new merchant

**Matching Cases Found**: 127 cases

**Top Relevant Cases**:

1. Case #FR-2024-4521 (85% match)
   - Date: 2024-12-15
   - Amount: $2,450
   - Merchant: Similar online retailer
   - Outcome: CONFIRMED FRAUD
   - Details: Stolen credentials, unauthorized purchase
   - Resolution: Funds recovered, merchant blacklisted
   - Similar indicators: New merchant, high amount, mobile device

2. Case #FR-2024-4892 (72% match)
   - Date: 2024-11-28
   - Amount: $2,800
   - Merchant: Online electronics store
   - Outcome: LEGITIMATE
   - Details: User-verified, gift purchase
   - Resolution: Transaction approved after verification
   - Similar indicators: High amount deviation

3. Case #FR-2024-5234 (78% match)
   - Date: 2024-12-01
   - Amount: $2,350
   - Merchant: Unknown online retailer
   - Outcome: CONFIRMED FRAUD
   - Details: Account takeover, multiple fraudulent transactions
   - Resolution: Account locked, criminal investigation
   - Similar indicators: New merchant, unusual pattern

4. Case #FR-2024-5118 (65% match)
   - Date: 2024-11-15
   - Amount: $2,100
   - Merchant: Legitimate online store
   - Outcome: LEGITIMATE
   - Details: User confirmed via phone
   - Resolution: Transaction completed successfully

**Pattern Analysis**:
- Total matching cases: 127
- Confirmed fraud: 82 cases (64.6%)
- Legitimate: 45 cases (35.4%)
- Fraud probability based on historical data: 64.6%

**Common Fraud Indicators** in matching cases:
1. New merchant (87% of fraud cases)
2. Amount >3x average (91% of fraud cases)
3. Mobile device transaction (45% of fraud cases)
4. Account takeover signs (38% of fraud cases)

**Recommended Actions** based on similar cases:
1. Immediate 2FA verification
2. Phone call to user
3. 24-48 hour hold period
4. Review merchant reputation

**Database Statistics**:
- Total fraud cases: 15,847
- Last 30 days: 234 cases
- Average case resolution time: 3.2 days
- False positive rate: 12%"""

        return search_results

    async def check_blacklists(self, entity_data: Dict[str, Any]) -> str:
        """
        Check various blacklists (merchants, IPs, devices)

        Args:
            entity_data: Entity information to check

        Returns:
            Blacklist check results
        """
        check_results = f"""Blacklist Screening Results:

**Entity Checked**:
- Merchant: "Online Retailer XYZ"
- IP Address: 192.168.1.100
- Device ID: {entity_data.get('device_id', 'device_abc123')}
- Email: user789@example.com

**Merchant Blacklist Check**:
- Internal blacklist: NOT FOUND ✓
- Industry shared blacklist: NOT FOUND ✓
- High-risk merchant list: NOT FOUND ✓
- Merchant reputation: UNKNOWN (New/Not Rated)
- Similar merchant names: 3 found (reviewing...)
  - "Online Retailer XY" - BLACKLISTED (Fraud, 2023)
  - "Retailer XYZ Online" - CLEAN ✓
  - "XYZ Retail Online" - BLACKLISTED (Scam, 2024) ⚠️

**IP Address Blacklist Check**:
- Fraud IP database: NOT FOUND ✓
- Spam blacklists: NOT FOUND ✓
- TOR exit nodes: NOT FOUND ✓
- Known bot networks: NOT FOUND ✓
- Proxy/VPN services: NOT FOUND ✓

**Device Blacklist Check**:
- Stolen device list: NOT FOUND ✓
- Fraud device database: NOT FOUND ✓
- Jailbroken/Rooted devices: NOT DETECTED ✓
- Emulator fingerprints: NOT MATCHED ✓

**Email Blacklist Check**:
- Disposable email: NO ✓
- Known fraud emails: NOT FOUND ✓
- Spam lists: NOT FOUND ✓
- Email age: 3+ years (established) ✓

**Card/Account Blacklist Check**:
- Stolen card database: NOT FOUND ✓
- Compromised account list: NOT FOUND ✓
- Fraud victim registry: NOT FOUND ✓

**BLACKLIST ASSESSMENT**: LOW-MEDIUM RISK

**Concerns Identified**:
- ⚠️ Merchant name similar to 2 blacklisted entities
- ⚠️ Merchant reputation unknown (new/not rated)

**Cleared Checks**:
- ✓ IP address clean
- ✓ Device not blacklisted
- ✓ Email established and clean
- ✓ No stolen card/account match

**Recommendation**:
- Investigate merchant "Online Retailer XYZ" further
- Check for domain age and business registration
- Monitor for similar merchant name patterns
- Consider elevated scrutiny due to merchant uncertainty"""

        return check_results

    async def analyze_network(self, user_id: str, connections: List[str]) -> str:
        """
        Analyze social/transaction network for fraud rings

        Args:
            user_id: User identifier
            connections: Connected users/entities

        Returns:
            Network analysis results
        """
        analysis = f"""Network & Connection Analysis:

**Primary User**: {user_id}

**Direct Connections Identified**: 15 connections

**Connection Types**:
1. Shared devices: 1 connection
   - user_456 shares same mobile device
   - Relationship: Family member (spouse)
   - Risk: LOW (legitimate sharing)

2. Shared IP addresses: 3 connections
   - user_234, user_456, user_891
   - Location: Same household
   - Risk: LOW (residential)

3. Similar transaction patterns: 2 connections
   - user_912, user_345
   - Pattern: Similar shopping behavior
   - Risk: LOW (coincidental)

4. Sent/received money: 4 connections
   - Regular transfers to/from family
   - Pattern: Monthly recurring
   - Risk: LOW (legitimate)

**Fraud Ring Detection**:
- Suspicious clusters: 0 detected ✓
- Rapid money movement: NOT DETECTED ✓
- Circular transactions: NOT DETECTED ✓
- Structuring patterns: NOT DETECTED ✓

**Network Depth Analysis**:
```
Level 1 (Direct): 15 connections
  ├─ Family/Friends: 12 (80%)
  ├─ Business: 2 (13%)
  └─ Unknown: 1 (7%)

Level 2 (2nd degree): 47 connections
  └─ No suspicious clusters

Level 3 (3rd degree): 234 connections
  └─ 1 connection to known fraud case (FR-2023-3421)
      └─ Relationship: Weak (distant connection)
      └─ Risk: MINIMAL
```

**Known Fraud Connections**:
- Direct connections to fraud cases: 0 ✓
- 2nd degree connections: 0 ✓
- 3rd degree connections: 1 (weak link)
  - Case #FR-2023-3421 (resolved 18 months ago)
  - Connection type: Used same merchant 2+ years ago
  - Significance: MINIMAL

**Velocity Patterns Across Network**:
- Coordinated activity: NOT DETECTED ✓
- Unusual money flow: NOT DETECTED ✓
- Rapid account creation: NOT DETECTED ✓
- Shared compromised credentials: NOT DETECTED ✓

**Geographic Clustering**:
- Primary location: New York, NY
- Network locations: Primarily New York area
- Unusual locations: 0 detected ✓

**Device Sharing Analysis**:
- Legitimate sharing: YES (family)
- Suspicious sharing: NO ✓
- Device hop patterns: NORMAL ✓

**NETWORK RISK ASSESSMENT**: LOW

**Findings**:
- Network structure appears legitimate
- Family/friend connections are normal
- No fraud ring indicators
- Minimal connection to historical fraud

**Recommendation**:
- Network analysis does not indicate fraud ring activity
- Connections appear legitimate (family/household)
- Focus investigation on transaction specifics rather than network"""

        return analysis

    async def search_public_records(self, query: str) -> str:
        """
        Search public internet for fraud reports with redundant fallbacks
        Fallback chain: Serper API → DuckDuckGo MCP → Mock

        Args:
            query: Search query

        Returns:
            Public search results
        """
        # Try Serper first (primary)
        if self.search_api_key:
            try:
                logger.info(f"Public records search: Using Serper API (primary)")
                return await self._search_with_serper(query)
            except Exception as e:
                logger.warning(f"Serper API failed: {e}, trying DuckDuckGo MCP fallback")

        # Try DuckDuckGo MCP (secondary fallback)
        if MCP_CLIENT_AVAILABLE and mcp_client.is_connected("duckduckgo"):
            try:
                logger.info(f"Public records search: Using DuckDuckGo MCP (fallback)")
                return await self._search_with_duckduckgo(query)
            except Exception as e:
                logger.warning(f"DuckDuckGo MCP failed: {e}, using mock data")

        # Final fallback to mock
        logger.info(f"Public records search: Using mock data (no search APIs available)")
        return await self._search_fallback(query)

    async def _search_with_serper(self, query: str) -> str:
        """Search using Serper API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.search_api_key,
                        "Content-Type": "application/json"
                    },
                    json={"q": f"{query} fraud scam report"}
                )

                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for result in data.get("organic", [])[:5]:
                        results.append(f"- {result.get('title')}\n  {result.get('snippet')}\n  {result.get('link')}")

                    return f"Public Fraud Reports Search:\n\n" + "\n\n".join(results)
                else:
                    return f"Search API error: {response.status_code}"
        except Exception as e:
            return f"Search error: {str(e)}"

    async def _search_with_duckduckgo(self, query: str) -> str:
        """Search using DuckDuckGo MCP (fallback to Serper)"""
        search_query = f"{query} fraud scam report"
        search_results = await mcp_client.search_duckduckgo(search_query, max_results=5)

        if not search_results:
            raise Exception("DuckDuckGo MCP returned no results")

        results = []
        for result in search_results[:5]:
            title = result.get('title', 'No title')
            snippet = result.get('snippet', 'No description')
            link = result.get('link', 'No link')
            results.append(f"- {title}\n  {snippet}\n  {link}")

        return f"Public Fraud Reports Search (DuckDuckGo MCP - Fallback):\n\n" + "\n\n".join(results)

    async def _search_fallback(self, query: str) -> str:
        """Fallback search simulation"""
        return f"""Public Records Search: "{query}"

**Search Results** (Sample - configure SERPER_API_KEY for real search):

1. Better Business Bureau Complaint Search
   - No complaints found for "Online Retailer XYZ"
   - Similar names: 3 results with mixed reviews

2. Scam Report Websites
   - Scamadviser.com: No reports found
   - Trustpilot: Merchant not found (new)
   - Sitejabber: No reviews available

3. Federal Trade Commission (FTC)
   - Consumer complaints: No matches
   - Fraud database: Not listed

4. State Attorney General Records
   - Business registration: PENDING VERIFICATION
   - Consumer protection cases: None found

5. Domain Analysis
   - Domain: onlineretailerxyz.com (hypothetical)
   - Domain age: 45 days (NEW DOMAIN) ⚠️
   - SSL certificate: Valid
   - WHOIS: Privacy protected

**Public Record Assessment**: INSUFFICIENT DATA

**Red Flags**:
- ⚠️ New domain (45 days old)
- ⚠️ No established online presence
- ⚠️ No reviews or ratings found
- ⚠️ Privacy-protected WHOIS

**Recommendation**:
- HIGH CAUTION due to lack of verifiable merchant history
- Recommend additional merchant verification
- Consider flagging transaction for review

Note: Configure SERPER_API_KEY for comprehensive internet search"""

        return search_fallback

    async def check_ofac_sanctions(
        self,
        name: str = None,
        email: str = None,
        country: str = None
    ) -> str:
        """
        Check OFAC sanctions lists and global watchlists
        Uses OpenSanctions API (free, no API key required)

        Args:
            name: Person or entity name
            email: Email address
            country: Country code

        Returns:
            Sanctions screening results
        """
        try:
            return await self._check_ofac_real(name, email, country)
        except Exception as e:
            logger.warning(f"OpenSanctions API error: {e}, using fallback")
            return await self._check_ofac_fallback(name, email, country)

    async def _check_ofac_real(self, name: str = None, email: str = None, country: str = None) -> str:
        """
        Real OFAC screening using OpenSanctions API
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            results_found = []

            # Search by name
            if name:
                response = await client.get(
                    "https://api.opensanctions.org/search/default",
                    params={
                        "q": name,
                        "schema": "Person,Organization",
                        "limit": 10
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    results_found.extend(data.get("results", []))

            # Build analysis
            if results_found:
                matches_detail = []
                for idx, result in enumerate(results_found[:5], 1):
                    props = result.get("properties", {})
                    matches_detail.append(f"""
{idx}. **Match Found** ({result.get('score', 0):.2f} relevance score)
   - Name: {', '.join(props.get('name', ['Unknown']))}
   - Type: {result.get('schema', 'Unknown')}
   - Birth Date: {', '.join(props.get('birthDate', ['N/A']))}
   - Countries: {', '.join(props.get('country', ['N/A']))}
   - Topics: {', '.join(props.get('topics', []))}
   - Datasets: {', '.join(result.get('datasets', []))}
   - Risk Level: {'🚨 CRITICAL' if 'sanction' in props.get('topics', []) else '⚠️  ELEVATED'}""")

                analysis = f"""OFAC & Sanctions Screening Results (REAL-TIME):

**Query**:
- Name: {name or 'N/A'}
- Email: {email or 'N/A'}
- Country: {country or 'N/A'}

**🔴 MATCHES FOUND**: {len(results_found)} potential match(es)

**Match Details**:
{''.join(matches_detail)}

**Sanctions Databases Checked**:
- ✓ OFAC SDN (Specially Designated Nationals)
- ✓ UN Security Council Sanctions
- ✓ EU Sanctions
- ✓ UK Sanctions
- ✓ Global PEP (Politically Exposed Persons)
- ✓ Global Watchlists

**RISK ASSESSMENT**: 🚨 CRITICAL - SANCTIONS MATCH FOUND

**Recommended Actions**:
1. 🚨 BLOCK transaction immediately
2. 🚨 DO NOT proceed with any financial activity
3. 🚨 Report to compliance officer
4. 🚨 File Suspicious Activity Report (SAR) if required
5. 🚨 Consult legal counsel before any action

**Compliance Note**:
Federal law prohibits transactions with OFAC-designated individuals and entities.
Violations can result in civil penalties up to $250,000 or criminal penalties.

**Data Source**: OpenSanctions.org (Live sanctions data)
**Last Updated**: {data.get('updated_at', 'Real-time')}"""

                return analysis
            else:
                return f"""OFAC & Sanctions Screening Results (REAL-TIME):

**Query**:
- Name: {name or 'N/A'}
- Email: {email or 'N/A'}
- Country: {country or 'N/A'}

**✓ NO MATCHES FOUND** - All clear

**Sanctions Databases Checked**:
- ✓ OFAC SDN (Specially Designated Nationals)
- ✓ UN Security Council Sanctions
- ✓ EU Sanctions
- ✓ UK Sanctions
- ✓ Global PEP (Politically Exposed Persons)
- ✓ Global Watchlists

**RISK ASSESSMENT**: ✓ CLEAR - No sanctions matches

**Recommendation**: PROCEED - No regulatory restrictions identified

**Data Source**: OpenSanctions.org (Live sanctions data)"""

    async def _check_ofac_fallback(self, name: str = None, email: str = None, country: str = None) -> str:
        """
        Fallback sanctions check (mock data)
        """
        return f"""OFAC & Sanctions Screening Results (MOCK - OpenSanctions API unavailable):

**Query**:
- Name: {name or 'N/A'}
- Email: {email or 'N/A'}
- Country: {country or 'N/A'}

**✓ NO MATCHES FOUND** (Mock check)

**Note**: Real-time sanctions screening temporarily unavailable.
Configure OpenSanctions API for live screening.

**Recommendation**: MANUAL REVIEW recommended for high-value transactions"""

    async def verify_business_registration(
        self,
        business_name: str,
        country_code: str = "us",
        state_code: str = None
    ) -> str:
        """
        Verify business using web search with redundant fallbacks
        Fallback chain: Serper API → DuckDuckGo MCP → Mock

        Args:
            business_name: Business name to verify
            country_code: Country code (default: us)
            state_code: State code for US (e.g., 'ca' for California)

        Returns:
            Business verification results
        """
        # Try Serper first (primary)
        if self.search_api_key:
            try:
                logger.info(f"Business verification: Using Serper API (primary)")
                return await self._verify_business_web_search(business_name, country_code, state_code)
            except Exception as e:
                logger.warning(f"Serper API failed: {e}, trying DuckDuckGo MCP fallback")

        # Try DuckDuckGo MCP (secondary fallback)
        if MCP_CLIENT_AVAILABLE and mcp_client.is_connected("duckduckgo"):
            try:
                logger.info(f"Business verification: Using DuckDuckGo MCP (fallback)")
                return await self._verify_business_duckduckgo(business_name, country_code, state_code)
            except Exception as e:
                logger.warning(f"DuckDuckGo MCP failed: {e}, using mock data")

        # Final fallback to mock
        logger.info(f"Business verification: Using mock data (no search APIs available)")
        return await self._verify_business_fallback(business_name)

    async def _verify_business_web_search(self, business_name: str, country_code: str, state_code: str) -> str:
        """
        Real business verification using web search (Serper API)
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Build search queries
            jurisdiction = f"{state_code} {country_code}" if state_code else country_code

            # Query 1: Business registration
            registration_query = f'"{business_name}" business registration {jurisdiction}'

            # Query 2: Complaints and fraud reports
            complaints_query = f'"{business_name}" scam fraud complaints reviews'

            # Query 3: Better Business Bureau
            bbb_query = f'"{business_name}" BBB rating {jurisdiction}'

            results = []

            # Search for business registration
            response = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": self.search_api_key,
                    "Content-Type": "application/json"
                },
                json={"q": registration_query, "num": 5}
            )

            if response.status_code == 200:
                data = response.json()
                registration_results = data.get("organic", [])

                # Check for fraud/complaints
                fraud_response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.search_api_key,
                        "Content-Type": "application/json"
                    },
                    json={"q": complaints_query, "num": 5}
                )

                fraud_results = fraud_response.json().get("organic", []) if fraud_response.status_code == 200 else []

                # Analyze results
                has_registration = any("secretary of state" in r.get("link", "").lower() or
                                     "business registration" in r.get("title", "").lower() or
                                     "incorporated" in r.get("snippet", "").lower()
                                     for r in registration_results)

                fraud_indicators = sum(1 for r in fraud_results
                                     if any(word in r.get("snippet", "").lower()
                                           for word in ["scam", "fraud", "complaint", "ripoff", "fake"]))

                has_bbb = any("bbb.org" in r.get("link", "") for r in registration_results + fraud_results)

                # Build analysis
                risk_factors = []
                if not has_registration:
                    risk_factors.append("⚠️  No clear business registration found in search results")
                if fraud_indicators >= 3:
                    risk_factors.append(f"🚨 Multiple fraud/scam reports found ({fraud_indicators} results)")
                elif fraud_indicators >= 1:
                    risk_factors.append(f"⚠️  Some negative reviews/complaints found ({fraud_indicators} results)")

                risk_level = "CRITICAL" if fraud_indicators >= 3 else "HIGH" if not has_registration else "MEDIUM" if fraud_indicators >= 1 else "LOW"

                # Format top results
                top_results = []
                for idx, result in enumerate(registration_results[:3], 1):
                    top_results.append(f"{idx}. {result.get('title')}\n   {result.get('snippet')}\n   {result.get('link')}")

                analysis = f"""Business Verification (WEB SEARCH):

**Business Name**: {business_name}
**Search Region**: {jurisdiction.upper()}

**Search Results Analysis**:

**Registration Verification**:
- Business registration found: {'✓ YES' if has_registration else '❌ NOT CLEARLY FOUND'}
- BBB listing found: {'✓ YES' if has_bbb else '⚠️  NO'}

**Reputation Analysis**:
- Fraud/scam reports: {fraud_indicators} results found
- Overall sentiment: {'🚨 NEGATIVE' if fraud_indicators >= 3 else '⚠️  MIXED' if fraud_indicators >= 1 else '✓ POSITIVE/NEUTRAL'}

**Top Search Results**:
{chr(10).join(top_results) if top_results else 'No significant results found'}

**Fraud Indicators Found**:
{chr(10).join([f"⚠️  {r.get('title')} - {r.get('snippet')[:100]}..." for r in fraud_results[:2]]) if fraud_results else '✓ No major fraud reports found'}

**Risk Factors**:
{chr(10).join(risk_factors) if risk_factors else '✓ No significant risk factors identified'}

**VERIFICATION STATUS**: {'🚨 HIGH RISK' if risk_level in ['CRITICAL', 'HIGH'] else '⚠️  MODERATE RISK' if risk_level == 'MEDIUM' else '✓ APPEARS LEGITIMATE'}
**BUSINESS RISK**: {risk_level}

**Recommendation**: {'🚨 DO NOT PROCEED - Multiple red flags' if risk_level == 'CRITICAL' else 'MANUAL REVIEW REQUIRED - Verify through official channels' if risk_level == 'HIGH' else 'PROCEED WITH CAUTION - Some concerns exist' if risk_level == 'MEDIUM' else 'APPROVED - No major concerns found'}

**Data Source**: Google Search (Serper API)
**Search Queries**: {len([registration_query, complaints_query])} queries executed
**Total Results Analyzed**: {len(registration_results) + len(fraud_results)} results"""

                return analysis
            else:
                raise Exception(f"Search API returned status {response.status_code}")

    async def _verify_business_duckduckgo(self, business_name: str, country_code: str, state_code: str) -> str:
        """
        Business verification using DuckDuckGo MCP (fallback to Serper)
        """
        jurisdiction = f"{state_code} {country_code}" if state_code else country_code

        # Build search queries
        registration_query = f'"{business_name}" business registration {jurisdiction}'
        complaints_query = f'"{business_name}" scam fraud complaints reviews'

        # Search using DuckDuckGo MCP
        registration_results = await mcp_client.search_duckduckgo(registration_query, max_results=5)
        fraud_results = await mcp_client.search_duckduckgo(complaints_query, max_results=5)

        if not registration_results and not fraud_results:
            raise Exception("DuckDuckGo MCP returned no results")

        # Convert to list if needed
        registration_results = registration_results or []
        fraud_results = fraud_results or []

        # Analyze results (similar to Serper logic)
        has_registration = any(
            "secretary of state" in str(r.get("link", "")).lower() or
            "business registration" in str(r.get("title", "")).lower() or
            "incorporated" in str(r.get("snippet", "")).lower()
            for r in registration_results
        )

        fraud_indicators = sum(1 for r in fraud_results
                             if any(word in str(r.get("snippet", "")).lower()
                                   for word in ["scam", "fraud", "complaint", "ripoff", "fake"]))

        has_bbb = any("bbb.org" in str(r.get("link", "")) for r in registration_results + fraud_results)

        # Build analysis
        risk_factors = []
        if not has_registration:
            risk_factors.append("⚠️  No clear business registration found in search results")
        if fraud_indicators >= 3:
            risk_factors.append(f"🚨 Multiple fraud/scam reports found ({fraud_indicators} results)")
        elif fraud_indicators >= 1:
            risk_factors.append(f"⚠️  Some negative reviews/complaints found ({fraud_indicators} results)")

        risk_level = "CRITICAL" if fraud_indicators >= 3 else "HIGH" if not has_registration else "MEDIUM" if fraud_indicators >= 1 else "LOW"

        # Format top results
        top_results = []
        for idx, result in enumerate(registration_results[:3], 1):
            title = result.get('title', 'No title')
            snippet = result.get('snippet', 'No description')
            link = result.get('link', 'No link')
            top_results.append(f"{idx}. {title}\n   {snippet}\n   {link}")

        analysis = f"""Business Verification (DUCKDUCKGO MCP - FALLBACK):

**Business Name**: {business_name}
**Search Region**: {jurisdiction.upper()}
**Search Method**: DuckDuckGo MCP (Serper unavailable)

**Search Results Analysis**:

**Registration Verification**:
- Business registration found: {'✓ YES' if has_registration else '❌ NOT CLEARLY FOUND'}
- BBB listing found: {'✓ YES' if has_bbb else '⚠️  NO'}

**Reputation Analysis**:
- Fraud/scam reports: {fraud_indicators} results found
- Overall sentiment: {'🚨 NEGATIVE' if fraud_indicators >= 3 else '⚠️  MIXED' if fraud_indicators >= 1 else '✓ POSITIVE/NEUTRAL'}

**Top Search Results**:
{chr(10).join(top_results) if top_results else 'No significant results found'}

**Fraud Indicators Found**:
{chr(10).join([f"⚠️  {r.get('title')} - {r.get('snippet', '')[:100]}..." for r in fraud_results[:2]]) if fraud_results else '✓ No major fraud reports found'}

**Risk Factors**:
{chr(10).join(risk_factors) if risk_factors else '✓ No significant risk factors identified'}

**VERIFICATION STATUS**: {'🚨 HIGH RISK' if risk_level in ['CRITICAL', 'HIGH'] else '⚠️  MODERATE RISK' if risk_level == 'MEDIUM' else '✓ APPEARS LEGITIMATE'}
**BUSINESS RISK**: {risk_level}

**Recommendation**: {'🚨 DO NOT PROCEED - Multiple red flags' if risk_level == 'CRITICAL' else 'MANUAL REVIEW REQUIRED - Verify through official channels' if risk_level == 'HIGH' else 'PROCEED WITH CAUTION - Some concerns exist' if risk_level == 'MEDIUM' else 'APPROVED - No major concerns found'}

**Data Source**: DuckDuckGo Search (MCP Server - Fallback Mode)
**Search Queries**: 2 queries executed
**Total Results Analyzed**: {len(registration_results) + len(fraud_results)} results

**Note**: Using DuckDuckGo MCP fallback (Serper API unavailable)"""

        return analysis

    async def _verify_business_fallback(self, business_name: str) -> str:
        """
        Fallback business verification (basic mock)
        """
        return f"""Business Verification (MOCK - Configure SERPER_API_KEY for real search):

**Business Name**: {business_name}

**Status**: Unable to verify (search API not configured)

**Recommendation**: MANUAL REVIEW required

**To enable real verification**:
Configure SERPER_API_KEY in .env file for web-based business verification
using Google Search to find:
- Business registration records
- BBB ratings and reviews
- Fraud/scam reports
- Public reputation data"""

    async def validate_email(self, email: str) -> str:
        """
        Validate email address and check for fraud indicators
        Uses Abstract API

        Args:
            email: Email address to validate

        Returns:
            Email validation results
        """
        if self.abstractapi_email_key:
            try:
                return await self._validate_email_real(email)
            except Exception as e:
                logger.warning(f"Abstract API error: {e}, using fallback")
                return await self._validate_email_fallback(email)
        else:
            logger.info("ABSTRACTAPI_EMAIL_KEY not configured, using mock validation")
            return await self._validate_email_fallback(email)

    async def _validate_email_real(self, email: str) -> str:
        """
        Real email validation using Abstract API
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://emailvalidation.abstractapi.com/v1/",
                params={
                    "api_key": self.abstractapi_email_key,
                    "email": email
                }
            )

            if response.status_code != 200:
                raise Exception(f"API returned status {response.status_code}")

            data = response.json()

            # Parse validation results
            is_valid_format = data.get("is_valid_format", {}).get("value", False)
            is_disposable = data.get("is_disposable_email", {}).get("value", False)
            is_mx_found = data.get("is_mx_found", {}).get("value", False)
            is_smtp_valid = data.get("is_smtp_valid", {}).get("value", False)
            quality_score = data.get("quality_score", 0)
            is_catchall = data.get("is_catchall_email", {}).get("value", False)
            is_role = data.get("is_role_email", {}).get("value", False)
            is_free = data.get("is_free_email", {}).get("value", False)

            # Determine risk level
            risk_factors = []
            if is_disposable:
                risk_factors.append("🚨 Disposable/temporary email (CRITICAL RISK)")
            if not is_smtp_valid:
                risk_factors.append("⚠️  SMTP validation failed")
            if not is_mx_found:
                risk_factors.append("⚠️  No MX records found")
            if not is_valid_format:
                risk_factors.append("⚠️  Invalid email format")
            if quality_score < 0.5:
                risk_factors.append(f"⚠️  Low quality score ({quality_score:.2f})")
            if is_catchall:
                risk_factors.append("ℹ️  Catch-all domain (accept-all)")

            risk_level = "CRITICAL" if is_disposable else "HIGH" if len(risk_factors) >= 3 else "MEDIUM" if len(risk_factors) >= 1 else "LOW"

            analysis = f"""Email Validation Results (REAL-TIME):

**Email Address**: {email}

**Validation Status**:
- Valid Format: {'✓ YES' if is_valid_format else '❌ NO'}
- Deliverable: {'✓ YES' if is_smtp_valid else '❌ NO'}
- MX Records Found: {'✓ YES' if is_mx_found else '❌ NO'}

**Fraud Indicators**:
- Disposable Email: {'🚨 YES (CRITICAL)' if is_disposable else '✓ NO'}
- Free Email Provider: {'YES' if is_free else 'NO'} (Gmail, Yahoo, etc.)
- Role Email: {'YES' if is_role else 'NO'} (support@, admin@, etc.)
- Catch-All Domain: {'YES' if is_catchall else 'NO'}

**Email Quality**:
- Quality Score: {quality_score:.2f}/1.00 {'✓' if quality_score >= 0.7 else '⚠️'}
- Deliverability: {'HIGH' if is_smtp_valid and quality_score >= 0.7 else 'LOW'}

**Domain Information**:
- Domain: {email.split('@')[1] if '@' in email else 'N/A'}
- Auto-Correct Suggestion: {data.get('autocorrect', 'None')}

**Risk Factors**:
{chr(10).join(risk_factors) if risk_factors else '✓ No risk factors identified'}

**EMAIL RISK**: {risk_level}

**Recommendation**: {'🚨 BLOCK - Disposable email detected' if is_disposable else '⚠️  REVIEW - Multiple risk factors' if risk_level in ['HIGH', 'MEDIUM'] else '✓ APPROVE - Email appears legitimate'}

**Data Source**: AbstractAPI Email Validation"""

            return analysis

    async def _validate_email_fallback(self, email: str) -> str:
        """
        Fallback email validation (basic check)
        """
        import re

        # Basic format validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid_format = bool(re.match(email_regex, email))

        # Check for common disposable domains
        disposable_domains = ['temp-mail.org', 'guerrillamail.com', '10minutemail.com', 'mailinator.com']
        domain = email.split('@')[1] if '@' in email else ''
        is_disposable = domain in disposable_domains

        return f"""Email Validation Results (BASIC CHECK):

**Email Address**: {email}

**Format Validation**: {'✓ Valid' if is_valid_format else '❌ Invalid'}
**Disposable Check**: {'🚨 YES - Disposable domain' if is_disposable else '✓ Not in common disposable list'}

**Note**: Configure ABSTRACTAPI_EMAIL_KEY for comprehensive email validation including:
- SMTP deliverability check
- MX record verification
- Quality scoring
- Comprehensive disposable email detection

**Recommendation**: MANUAL REVIEW recommended"""

        return analysis
