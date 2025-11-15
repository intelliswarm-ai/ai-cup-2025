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
    """Get all investment team tools"""
    tools = []

    # Search Tools (Serper API)
    search_tools = SearchTools()
    tools.append({
        "name": "Internet Search (Serper API)",
        "type": "api",
        "description": "Google search via Serper API for market research and financial news",
        "provider": "Serper.dev",
        "isActive": bool(os.getenv("SERPER_API_KEY")),
        "configuration": {
            "api_endpoint": "https://google.serper.dev/search",
            "api_key": os.getenv("SERPER_API_KEY", "")[:10] + "..." if os.getenv("SERPER_API_KEY") else "not_configured",
            "search_type": "google"
        },
        "methods": get_tool_methods(search_tools)
    })

    # Browser Tools (Browserless)
    browser_tools = BrowserTools()
    tools.append({
        "name": "Web Scraping (Browserless)",
        "type": "api",
        "description": "JavaScript-enabled web scraping for financial data and company websites",
        "provider": "Browserless.io",
        "isActive": bool(os.getenv("BROWSERLESS_API_KEY")),
        "configuration": {
            "api_endpoint": "https://chrome.browserless.io",
            "api_key": os.getenv("BROWSERLESS_API_KEY", "")[:10] + "..." if os.getenv("BROWSERLESS_API_KEY") else "not_configured",
            "headless": True,
            "timeout": 60000
        },
        "methods": get_tool_methods(browser_tools)
    })

    # SEC Tools
    sec_tools = SECTools()
    tools.append({
        "name": "SEC Filings Database",
        "type": "api",
        "description": "Access to SEC company filings and reports (10-K, 10-Q, 8-K)",
        "provider": "SEC-API.io",
        "isActive": bool(os.getenv("SEC_API_KEY")),
        "configuration": {
            "api_endpoint": "https://api.sec-api.io",
            "api_key": os.getenv("SEC_API_KEY", "")[:10] + "..." if os.getenv("SEC_API_KEY") else "not_configured",
            "forms": "10-K,10-Q,8-K",
            "fallback": "SEC EDGAR (free)"
        },
        "methods": get_tool_methods(sec_tools)
    })

    # Calculator Tools
    calculator_tools = CalculatorTools()
    tools.append({
        "name": "Financial Calculator",
        "type": "proprietary",
        "description": "Built-in financial calculations (P/E ratio, CAGR, ROE, etc.)",
        "provider": "Internal",
        "isActive": True,
        "configuration": {
            "calculations": "P/E, CAGR, ROE, D/E, Dividend Yield",
            "built_in": True
        },
        "methods": get_tool_methods(calculator_tools)
    })

    # MCP Integration
    if os.getenv("MCP_ENABLED", "").lower() == "true":
        tools.append({
            "name": "MCP Integration",
            "type": "mcp",
            "description": "Model Context Protocol server integration for extended capabilities",
            "provider": "MCP",
            "isActive": True,
            "configuration": {
                "mcp_enabled": True,
                "mcp_protocol": "stdio",
                "note": "MCP servers can be added via configuration"
            },
            "methods": []
        })

    return tools


def get_fraud_tools() -> List[Dict[str, Any]]:
    """Get all fraud team tools"""
    tools = []

    # Transaction Tools
    transaction_tools = TransactionTools()
    tools.append({
        "name": "Transaction Pattern Analysis",
        "type": "proprietary",
        "description": "Analyze transaction patterns, velocity, and historical data for fraud detection",
        "provider": "Internal",
        "isActive": True,
        "configuration": {
            "capabilities": "pattern analysis, velocity checks, chargeback history",
            "mcp_integration": os.getenv("USE_MCP_TRANSACTION_DB", "false")
        },
        "methods": get_tool_methods(transaction_tools)
    })

    # Risk Tools
    risk_tools = RiskTools()
    tools.append({
        "name": "Risk Scoring & Device Analysis",
        "type": "proprietary",
        "description": "Calculate fraud risk scores and analyze device fingerprints",
        "provider": "Internal",
        "isActive": True,
        "configuration": {
            "capabilities": "fraud scoring, device fingerprinting, geolocation analysis",
            "mcp_memory": os.getenv("USE_MCP_MEMORY", "false")
        },
        "methods": get_tool_methods(risk_tools)
    })

    # Investigation Tools
    investigation_tools = InvestigationTools()
    tools.append({
        "name": "Investigation & Intelligence Tools",
        "type": "api",
        "description": "Deep investigation including OFAC sanctions, business verification, email validation",
        "provider": "Multiple APIs",
        "isActive": True,
        "configuration": {
            "serper_search": bool(os.getenv("SERPER_API_KEY")),
            "email_validation": bool(os.getenv("ABSTRACTAPI_EMAIL_KEY")),
            "ofac_sanctions": "OpenSanctions (free)",
            "business_verification": "Web search"
        },
        "methods": get_tool_methods(investigation_tools)
    })

    # IP Geolocation (from RiskTools)
    tools.append({
        "name": "IP Geolocation Analysis",
        "type": "api",
        "description": "Real-time IP intelligence and threat detection",
        "provider": "IPGeolocation.io",
        "isActive": bool(os.getenv("IPGEOLOCATION_API_KEY")),
        "configuration": {
            "api_endpoint": "https://api.ipgeolocation.io/ipgeo",
            "api_key": os.getenv("IPGEOLOCATION_API_KEY", "")[:10] + "..." if os.getenv("IPGEOLOCATION_API_KEY") else "not_configured",
            "features": "geo,security,timezone,currency"
        },
        "methods": [
            {
                "name": "analyze_geolocation",
                "description": "Analyze IP and geolocation data using real IP intelligence API",
                "signature": "(ip_address: str, location_data: Dict = None)"
            }
        ]
    })

    # Email Validation (from InvestigationTools)
    tools.append({
        "name": "Email Validation & Risk Analysis",
        "type": "api",
        "description": "Email verification, deliverability check, and fraud risk assessment",
        "provider": "AbstractAPI",
        "isActive": bool(os.getenv("ABSTRACTAPI_EMAIL_KEY")),
        "configuration": {
            "api_endpoint": "https://emailvalidation.abstractapi.com/v1/",
            "api_key": os.getenv("ABSTRACTAPI_EMAIL_KEY", "")[:10] + "..." if os.getenv("ABSTRACTAPI_EMAIL_KEY") else "not_configured",
            "checks": "format, deliverability, disposable, quality score"
        },
        "methods": [
            {
                "name": "validate_email",
                "description": "Validate email address and check for fraud indicators",
                "signature": "(email: str)"
            }
        ]
    })

    # MCP Integration
    if os.getenv("MCP_ENABLED", "").lower() == "true":
        tools.append({
            "name": "MCP Integration",
            "type": "mcp",
            "description": "Model Context Protocol server integration for extended capabilities",
            "provider": "MCP",
            "isActive": True,
            "configuration": {
                "mcp_enabled": True,
                "mcp_protocol": "stdio",
                "mcp_filesystem": os.getenv("USE_MCP_FILESYSTEM", "false"),
                "mcp_memory": os.getenv("USE_MCP_MEMORY", "false")
            },
            "methods": []
        })

    return tools


def get_compliance_tools() -> List[Dict[str, Any]]:
    """Get all compliance team tools"""
    tools = []

    # Investigation Tools for compliance
    investigation_tools = InvestigationTools()
    tools.append({
        "name": "OFAC & Sanctions Screening",
        "type": "api",
        "description": "Check OFAC sanctions lists and global watchlists using OpenSanctions",
        "provider": "OpenSanctions.org",
        "isActive": True,  # Free API, no key required
        "configuration": {
            "api_endpoint": "https://api.opensanctions.org/search/default",
            "databases": "OFAC SDN, UN, EU, UK Sanctions, PEP",
            "real_time": True,
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

    # Business verification
    tools.append({
        "name": "Business Verification",
        "type": "api",
        "description": "Verify business registration and reputation using web search",
        "provider": "Web Search (Serper/DuckDuckGo)",
        "isActive": bool(os.getenv("SERPER_API_KEY")),
        "configuration": {
            "primary": "Serper API (if configured)",
            "fallback": "DuckDuckGo MCP",
            "checks": "registration, BBB, fraud reports, reputation"
        },
        "methods": [
            {
                "name": "verify_business_registration",
                "description": "Verify business using web search with redundant fallbacks",
                "signature": "(business_name: str, country_code: str = 'us', state_code: str = None)"
            }
        ]
    })

    # Document analysis (placeholder for future implementation)
    tools.append({
        "name": "Document Analysis",
        "type": "proprietary",
        "description": "Analyze compliance documents and regulatory filings",
        "provider": "Internal",
        "isActive": False,  # Not yet implemented
        "configuration": {
            "status": "planned",
            "capabilities": "Document classification, regulatory compliance checking"
        },
        "methods": []
    })

    # MCP Integration
    if os.getenv("MCP_ENABLED", "").lower() == "true":
        tools.append({
            "name": "MCP Integration",
            "type": "mcp",
            "description": "Model Context Protocol server integration for extended capabilities",
            "provider": "MCP",
            "isActive": True,
            "configuration": {
                "mcp_enabled": True,
                "mcp_protocol": "stdio"
            },
            "methods": []
        })

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
