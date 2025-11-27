"""
Tool Discovery Module
Automatically discovers and exposes tool capabilities from tool classes
"""

import os
import inspect
from typing import Dict, List, Any
from tools.search_tools import SearchTools
from tools.browser_tools import BrowserTools
from tools.sec_tools import SECTools
from tools.investigation_tools import InvestigationTools
from tools.risk_tools import RiskTools
from tools.transaction_tools import TransactionTools
from tools.calculator_tools import CalculatorTools


def get_tool_methods(tool_class) -> List[Dict[str, Any]]:
    """Extract public methods from a tool class"""
    methods = []
    for name, method in inspect.getmembers(tool_class, predicate=inspect.ismethod):
        if not name.startswith('_'):  # Only public methods
            # Get method signature and docstring
            doc = inspect.getdoc(method) or "No description available"
            signature = inspect.signature(method)

            # Extract first line of docstring as description
            description = doc.split('\n\n')[0].replace('\n', ' ').strip()

            methods.append({
                "name": name,
                "description": description,
                "signature": str(signature)
            })

    return methods


def get_investment_tools() -> List[Dict[str, Any]]:
    """Get ONLY high-value tools for investment team (filtered to real data, free APIs)"""
    tools = []

    # Search Tools (Serper API) - ✅ KEEP
    search_tools = SearchTools()
    tools.append({
        "name": "Internet Search (Serper API)",
        "type": "api",
        "description": "Market research, news, company information (FREE tier: 2,500 searches/month)",
        "provider": "Serper.dev (Free)",
        "isActive": bool(os.getenv("SERPER_API_KEY")),
        "configuration": {
            "api_endpoint": "https://google.serper.dev/search",
            "api_key": os.getenv("SERPER_API_KEY", "")[:10] + "..." if os.getenv("SERPER_API_KEY") else "not_configured",
            "search_type": "google",
            "free_tier": "2,500 searches/month"
        },
        "methods": get_tool_methods(search_tools)
    })

    # SEC Tools - ✅ KEEP (switch to free Edgar API)
    sec_tools = SECTools()
    tools.append({
        "name": "SEC Filings (Edgar API)",
        "type": "api",
        "description": "Official SEC company filings (10-K, 10-Q, 8-K) - 100% FREE, unlimited",
        "provider": "SEC.gov (Free)",
        "isActive": True,  # Always active - no API key needed
        "configuration": {
            "api_endpoint": "https://www.sec.gov/cgi-bin/browse-edgar",
            "forms": "10-K,10-Q,8-K",
            "free": True,
            "no_api_key_required": True
        },
        "methods": get_tool_methods(sec_tools)
    })

    # Stock Data API - 🆕 NEW - CRITICAL NEED
    # Note: Implementation file needs to be created (tools/stock_data_tools.py)
    if os.getenv("ALPHA_VANTAGE_API_KEY"):
        tools.append({
            "name": "Real-Time Stock Data (Alpha Vantage)",
            "type": "api",
            "description": "Real-time stock prices, fundamentals, financials (FREE tier: 500 calls/day)",
            "provider": "Alpha Vantage (Free)",
            "isActive": bool(os.getenv("ALPHA_VANTAGE_API_KEY")),
            "configuration": {
                "api_endpoint": "https://www.alphavantage.co/query",
                "api_key": os.getenv("ALPHA_VANTAGE_API_KEY", "")[:10] + "..." if os.getenv("ALPHA_VANTAGE_API_KEY") else "not_configured",
                "free_tier": "500 calls/day",
                "functions": "TIME_SERIES_DAILY, OVERVIEW, INCOME_STATEMENT"
            },
            "methods": [
                {"name": "get_current_price", "description": "Get current stock price", "signature": "(ticker: str)"},
                {"name": "get_company_fundamentals", "description": "Get P/E, market cap, financials", "signature": "(ticker: str)"}
            ]
        })

    # REMOVED: Browserless (expensive, unclear value)
    # REMOVED: Financial Calculator (no real data)
    # REMOVED: MCP Integration (unused, see MCP_INVESTIGATION_REPORT.md)

    return tools


def get_fraud_tools() -> List[Dict[str, Any]]:
    """Get ONLY high-value tools for fraud team (filtered to real data, free APIs)"""
    tools = []

    # Email Validation - ✅ KEEP
    tools.append({
        "name": "Email Validation (AbstractAPI)",
        "type": "api",
        "description": "Email verification and risk assessment (FREE tier: 100 validations/month)",
        "provider": "AbstractAPI (Free)",
        "isActive": bool(os.getenv("ABSTRACTAPI_EMAIL_KEY")),
        "configuration": {
            "api_endpoint": "https://emailvalidation.abstractapi.com/v1/",
            "api_key": os.getenv("ABSTRACTAPI_EMAIL_KEY", "")[:10] + "..." if os.getenv("ABSTRACTAPI_EMAIL_KEY") else "not_configured",
            "checks": "format, deliverability, disposable, quality score",
            "free_tier": "100 validations/month"
        },
        "methods": [
            {
                "name": "validate_email",
                "description": "Validate email address and check for fraud indicators",
                "signature": "(email: str)"
            }
        ]
    })

    # OFAC Sanctions - ✅ KEEP
    tools.append({
        "name": "OFAC Sanctions (OpenSanctions)",
        "type": "api",
        "description": "Sanctions and watchlist screening - 100% FREE, unlimited",
        "provider": "OpenSanctions.org (Free)",
        "isActive": True,  # No API key needed
        "configuration": {
            "api_endpoint": "https://api.opensanctions.org/search/default",
            "databases": "OFAC SDN, UN, EU, UK Sanctions, PEP",
            "free": True,
            "no_api_key_required": True
        },
        "methods": [
            {
                "name": "check_ofac_sanctions",
                "description": "Check OFAC sanctions lists and global watchlists",
                "signature": "(name: str = None, email: str = None, country: str = None)"
            }
        ]
    })

    # Public Records Search - ✅ KEEP (uses Serper API)
    tools.append({
        "name": "Public Records Search (Serper API)",
        "type": "api",
        "description": "Web research and public records (FREE tier: 2,500 searches/month)",
        "provider": "Serper.dev (Free)",
        "isActive": bool(os.getenv("SERPER_API_KEY")),
        "configuration": {
            "api_endpoint": "https://google.serper.dev/search",
            "api_key": os.getenv("SERPER_API_KEY", "")[:10] + "..." if os.getenv("SERPER_API_KEY") else "not_configured",
            "free_tier": "2,500 searches/month"
        },
        "methods": [
            {
                "name": "search_public_records",
                "description": "Search public records using web search",
                "signature": "(query: str)"
            }
        ]
    })

    # IP Intelligence - 🆕 NEW - HIGH VALUE
    if os.getenv("IPQUALITYSCORE_API_KEY"):
        tools.append({
            "name": "IP Intelligence (IPQualityScore)",
            "type": "api",
            "description": "IP risk scoring, proxy/VPN detection (FREE tier: 5,000 lookups/month)",
            "provider": "IPQualityScore (Free)",
            "isActive": bool(os.getenv("IPQUALITYSCORE_API_KEY")),
            "configuration": {
                "api_endpoint": "https://ipqualityscore.com/api/json/ip",
                "api_key": os.getenv("IPQUALITYSCORE_API_KEY", "")[:10] + "..." if os.getenv("IPQUALITYSCORE_API_KEY") else "not_configured",
                "free_tier": "5,000 lookups/month",
                "features": "proxy, VPN, bot detection, fraud score"
            },
            "methods": [
                {"name": "check_ip_risk", "description": "Check IP risk and fraud score", "signature": "(ip_address: str)"},
                {"name": "get_fraud_score", "description": "Get fraud score 0-100", "signature": "(ip_address: str)"}
            ]
        })

    # URL Scanning - 🆕 NEW - CRITICAL FOR PHISHING
    if os.getenv("GOOGLE_SAFE_BROWSING_API_KEY"):
        tools.append({
            "name": "URL Scanning (Google Safe Browsing)",
            "type": "api",
            "description": "Malicious URL and phishing detection - 100% FREE (10,000 lookups/day)",
            "provider": "Google (Free)",
            "isActive": bool(os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")),
            "configuration": {
                "api_endpoint": "https://safebrowsing.googleapis.com/v4/threatMatches:find",
                "api_key": os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", "")[:10] + "..." if os.getenv("GOOGLE_SAFE_BROWSING_API_KEY") else "not_configured",
                "free_tier": "10,000 lookups/day",
                "threat_types": "MALWARE, SOCIAL_ENGINEERING, UNWANTED_SOFTWARE"
            },
            "methods": [
                {"name": "scan_url", "description": "Check if URL is malicious", "signature": "(url: str)"},
                {"name": "check_phishing_site", "description": "Detect phishing sites", "signature": "(url: str)"}
            ]
        })

    # REMOVED: Transaction Pattern Analysis (100% mock data - see TOOL_AUDIT_REPORT.md)
    # REMOVED: Risk Scoring & Device Analysis (100% mock data - see TOOL_AUDIT_REPORT.md)
    # REMOVED: Investigation Tools fraud database methods (100% mock data - see TOOL_AUDIT_REPORT.md)
    # REMOVED: IP Geolocation (replaced with IPQualityScore which has better fraud detection)
    # REMOVED: MCP Integration (unused, see MCP_INVESTIGATION_REPORT.md)

    return tools


def get_compliance_tools() -> List[Dict[str, Any]]:
    """Get ONLY high-value tools for compliance team (filtered to real data, free APIs)"""
    tools = []

    # OFAC & Sanctions Screening - ✅ KEEP
    tools.append({
        "name": "OFAC & Sanctions Screening (OpenSanctions)",
        "type": "api",
        "description": "Comprehensive sanctions and watchlist checks - 100% FREE, unlimited",
        "provider": "OpenSanctions.org (Free)",
        "isActive": True,  # No API key needed
        "configuration": {
            "api_endpoint": "https://api.opensanctions.org/search/default",
            "databases": "OFAC SDN, UN, EU, UK Sanctions, PEP",
            "real_time": True,
            "free": True,
            "no_api_key_required": True
        },
        "methods": [
            {
                "name": "check_ofac_sanctions",
                "description": "Check OFAC sanctions lists and global watchlists",
                "signature": "(name: str = None, email: str = None, country: str = None)"
            }
        ]
    })

    # Business Verification - ✅ KEEP (uses Serper API)
    tools.append({
        "name": "Business Verification (Serper API)",
        "type": "api",
        "description": "Business registration and reputation research (FREE tier: 2,500 searches/month)",
        "provider": "Serper.dev (Free)",
        "isActive": bool(os.getenv("SERPER_API_KEY")),
        "configuration": {
            "api_endpoint": "https://google.serper.dev/search",
            "api_key": os.getenv("SERPER_API_KEY", "")[:10] + "..." if os.getenv("SERPER_API_KEY") else "not_configured",
            "free_tier": "2,500 searches/month",
            "checks": "registration, BBB, fraud reports, reputation"
        },
        "methods": [
            {
                "name": "verify_business_registration",
                "description": "Verify business using web search",
                "signature": "(business_name: str, country_code: str = 'us', state_code: str = None)"
            }
        ]
    })

    # REMOVED: Document Analysis (not implemented, isActive: false)
    # REMOVED: MCP Integration (unused, see MCP_INVESTIGATION_REPORT.md)

    return tools


def get_team_tools(team_key: str) -> List[Dict[str, Any]]:
    """Get tools for a specific team"""
    if team_key == "investments":
        return get_investment_tools()
    elif team_key == "fraud":
        return get_fraud_tools()
    elif team_key == "compliance":
        return get_compliance_tools()
    else:
        return []
