"""
Regulatory Tools for compliance analysis
Provides regulatory research, licensing verification, and policy lookup capabilities
"""

import os
import json
import httpx
from typing import List, Dict, Any, Optional


class RegulatoryTools:
    """Tools for regulatory compliance checks and research"""

    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY", "")

        # Compliance workflow requires real API - no mock data allowed
        if not self.serper_api_key or not self.serper_api_key.strip():
            print("WARNING: SERPER_API_KEY not configured. Regulatory tools will not work.")

        self.use_real_api = bool(self.serper_api_key and self.serper_api_key.strip())

    async def search_regulations(
        self,
        entity_name: str,
        entity_type: str,
        country: Optional[str] = None,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for applicable regulations based on entity details using real API only

        Args:
            entity_name: Name of entity
            entity_type: Type of entity (individual, company, transaction)
            country: Country of operation
            industry: Industry sector

        Returns:
            Dictionary with regulatory requirements
        """
        if not self.use_real_api:
            return {
                "entity_name": entity_name,
                "error": "API_NOT_CONFIGURED",
                "applicable_regulations": [],
                "message": "SERPER_API_KEY not configured. Cannot perform real regulatory search.",
                "requires_manual_check": True
            }

        return await self._search_regulations_real(entity_name, entity_type, country, industry)

    async def _search_regulations_real(
        self,
        entity_name: str,
        entity_type: str,
        country: Optional[str],
        industry: Optional[str]
    ) -> Dict[str, Any]:
        """Search regulations using real API"""
        try:
            # Build search query
            query_parts = [entity_name]
            if country:
                query_parts.append(f"{country} regulations")
            if industry:
                query_parts.append(f"{industry} compliance")
            query_parts.extend(["regulatory requirements", "licensing"])

            query = " ".join(query_parts)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.serper_api_key,
                        "Content-Type": "application/json"
                    },
                    json={"q": query, "num": 5}
                )

                if response.status_code == 200:
                    data = response.json()
                    regulations = []

                    for result in data.get("organic", [])[:5]:
                        regulations.append({
                            "title": result.get("title", ""),
                            "description": result.get("snippet", ""),
                            "source": result.get("link", "")
                        })

                    return {
                        "applicable_regulations": regulations,
                        "country": country or "Unknown",
                        "industry": industry or "General",
                        "data_source": "real_search",
                        "search_query": query
                    }
                else:
                    return {
                        "entity_name": entity_name,
                        "error": "API_ERROR",
                        "applicable_regulations": [],
                        "message": f"Regulatory API returned error: HTTP {response.status_code}",
                        "requires_manual_check": True
                    }

        except Exception as e:
            print(f"Error searching regulations: {e}")
            return {
                "entity_name": entity_name,
                "error": "API_ERROR",
                "applicable_regulations": [],
                "message": f"Failed to search regulations: {str(e)}",
                "requires_manual_check": True
            }

    def _search_regulations_mock(
        self,
        entity_name: str,
        entity_type: str,
        country: Optional[str],
        industry: Optional[str]
    ) -> Dict[str, Any]:
        """Mock regulatory search for demo/testing"""
        country = country or "United States"
        industry = industry or "Financial Services"

        # Mock regulatory requirements based on entity type and industry
        regulations = []

        if entity_type == "company":
            regulations.extend([
                {
                    "regulation": "Bank Secrecy Act (BSA)",
                    "jurisdiction": country,
                    "description": "Requires financial institutions to assist government agencies in detecting and preventing money laundering",
                    "applicability": "HIGH" if "financial" in industry.lower() else "MEDIUM"
                },
                {
                    "regulation": "Know Your Customer (KYC) Requirements",
                    "jurisdiction": country,
                    "description": "Customer due diligence and identity verification requirements",
                    "applicability": "HIGH"
                },
                {
                    "regulation": "Anti-Money Laundering (AML) Regulations",
                    "jurisdiction": country,
                    "description": "Compliance program requirements to prevent money laundering",
                    "applicability": "HIGH"
                }
            ])

            if country.lower() in ["united states", "usa", "us"]:
                regulations.append({
                    "regulation": "USA PATRIOT Act",
                    "jurisdiction": "United States",
                    "description": "Enhanced due diligence and customer identification requirements",
                    "applicability": "HIGH"
                })

            if "financial" in industry.lower():
                regulations.extend([
                    {
                        "regulation": "Dodd-Frank Wall Street Reform Act",
                        "jurisdiction": "United States",
                        "description": "Financial regulation and consumer protection",
                        "applicability": "HIGH"
                    },
                    {
                        "regulation": "FINRA Regulations",
                        "jurisdiction": "United States",
                        "description": "Securities industry regulations and compliance",
                        "applicability": "HIGH"
                    }
                ])

        elif entity_type == "individual":
            regulations.extend([
                {
                    "regulation": "KYC/CIP Requirements",
                    "jurisdiction": country,
                    "description": "Customer Identification Program requirements for individuals",
                    "applicability": "HIGH"
                },
                {
                    "regulation": "PEP Screening",
                    "jurisdiction": "Global",
                    "description": "Politically Exposed Person screening requirements",
                    "applicability": "MEDIUM"
                }
            ])

        return {
            "applicable_regulations": regulations,
            "country": country,
            "industry": industry,
            "entity_type": entity_type,
            "total_regulations": len(regulations),
            "data_source": "mock_data",
            "note": "This is mock data for demonstration. Real implementation would query regulatory databases."
        }

    async def check_licensing(
        self,
        entity_name: str,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check business licenses and registrations using real API only

        Args:
            entity_name: Company name
            country: Country of registration

        Returns:
            Dictionary with licensing information
        """
        if not self.use_real_api:
            return {
                "entity_name": entity_name,
                "error": "API_NOT_CONFIGURED",
                "licenses_found": [],
                "message": "SERPER_API_KEY not configured. Cannot perform real licensing check.",
                "requires_manual_check": True
            }

        return await self._check_licensing_real(entity_name, country)

    async def _check_licensing_real(
        self,
        entity_name: str,
        country: Optional[str]
    ) -> Dict[str, Any]:
        """Check licensing using real API"""
        try:
            query = f"{entity_name} business license registration {country or ''}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.serper_api_key,
                        "Content-Type": "application/json"
                    },
                    json={"q": query, "num": 3}
                )

                if response.status_code == 200:
                    data = response.json()
                    licenses = []

                    for result in data.get("organic", [])[:3]:
                        licenses.append({
                            "title": result.get("title", ""),
                            "description": result.get("snippet", ""),
                            "source": result.get("link", "")
                        })

                    return {
                        "entity_name": entity_name,
                        "country": country or "Unknown",
                        "licenses_found": licenses,
                        "verification_status": "REQUIRES_MANUAL_REVIEW",
                        "data_source": "real_search"
                    }
                else:
                    return {
                        "entity_name": entity_name,
                        "error": "API_ERROR",
                        "licenses_found": [],
                        "message": f"Licensing API returned error: HTTP {response.status_code}",
                        "requires_manual_check": True
                    }

        except Exception as e:
            print(f"Error checking licensing: {e}")
            return {
                "entity_name": entity_name,
                "error": "API_ERROR",
                "licenses_found": [],
                "message": f"Failed to check licensing: {str(e)}",
                "requires_manual_check": True
            }

    def _check_licensing_mock(
        self,
        entity_name: str,
        country: Optional[str]
    ) -> Dict[str, Any]:
        """Mock licensing check for demo/testing"""
        country = country or "United States"

        # Mock licensing status
        licenses = [
            {
                "license_type": "Business License",
                "issuing_authority": f"{country} Business Registry",
                "status": "ACTIVE",
                "issue_date": "2020-01-15",
                "expiration_date": "2025-01-15",
                "license_number": "BL-2020-12345"
            },
            {
                "license_type": "Financial Services License",
                "issuing_authority": f"{country} Financial Regulatory Authority",
                "status": "ACTIVE",
                "issue_date": "2020-03-01",
                "expiration_date": "2025-03-01",
                "license_number": "FSL-2020-67890"
            }
        ]

        return {
            "entity_name": entity_name,
            "country": country,
            "licenses": licenses,
            "total_licenses": len(licenses),
            "verification_status": "VERIFIED",
            "compliance_status": "COMPLIANT",
            "data_source": "mock_data",
            "note": "Mock licensing data for demonstration. Real implementation would query official registries."
        }

    async def get_regulatory_updates(
        self,
        jurisdiction: str,
        industry: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get recent regulatory updates and changes

        Args:
            jurisdiction: Country or region
            industry: Industry sector (optional)
            days: Number of days to look back

        Returns:
            Dictionary with recent regulatory changes
        """
        if self.use_real_api:
            return await self._get_regulatory_updates_real(jurisdiction, industry, days)
        else:
            return self._get_regulatory_updates_mock(jurisdiction, industry, days)

    async def _get_regulatory_updates_real(
        self,
        jurisdiction: str,
        industry: Optional[str],
        days: int
    ) -> Dict[str, Any]:
        """Get regulatory updates using real API"""
        try:
            query_parts = [jurisdiction, "regulatory changes", "compliance updates"]
            if industry:
                query_parts.append(industry)
            query = " ".join(query_parts)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.serper_api_key,
                        "Content-Type": "application/json"
                    },
                    json={"q": query, "num": 5}
                )

                if response.status_code == 200:
                    data = response.json()
                    updates = []

                    for result in data.get("organic", [])[:5]:
                        updates.append({
                            "title": result.get("title", ""),
                            "description": result.get("snippet", ""),
                            "source": result.get("link", ""),
                            "date": result.get("date", "Recent")
                        })

                    return {
                        "jurisdiction": jurisdiction,
                        "industry": industry or "All",
                        "updates": updates,
                        "data_source": "real_search"
                    }
                else:
                    return self._get_regulatory_updates_mock(jurisdiction, industry, days)

        except Exception as e:
            print(f"Error getting regulatory updates: {e}")
            return self._get_regulatory_updates_mock(jurisdiction, industry, days)

    def _get_regulatory_updates_mock(
        self,
        jurisdiction: str,
        industry: Optional[str],
        days: int
    ) -> Dict[str, Any]:
        """Mock regulatory updates for demo/testing"""
        updates = [
            {
                "date": "2024-01-15",
                "title": "Enhanced AML Reporting Requirements",
                "description": "New requirements for beneficial ownership disclosure and transaction monitoring thresholds",
                "impact": "HIGH",
                "effective_date": "2024-04-01"
            },
            {
                "date": "2024-01-10",
                "title": "Updated KYC Guidelines",
                "description": "Strengthened customer due diligence requirements for high-risk jurisdictions",
                "impact": "MEDIUM",
                "effective_date": "2024-03-01"
            }
        ]

        return {
            "jurisdiction": jurisdiction,
            "industry": industry or "All",
            "updates": updates,
            "total_updates": len(updates),
            "period_days": days,
            "data_source": "mock_data",
            "note": "Mock regulatory updates for demonstration"
        }
