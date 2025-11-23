"""
AML (Anti-Money Laundering) Tools for compliance analysis
Provides KYC verification, PEP screening, and transaction pattern analysis
"""

import os
import json
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class AMLTools:
    """Tools for Anti-Money Laundering and Know Your Customer checks"""

    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY", "")

        # Compliance workflow requires real API - no mock data allowed
        if not self.serper_api_key or not self.serper_api_key.strip():
            print("WARNING: SERPER_API_KEY not configured. Web search fallback will not work.")

        self.use_real_api = bool(self.serper_api_key and self.serper_api_key.strip())

        # OpenSanctions.org API configuration (free, includes PEP data)
        self.opensanctions_api_url = "https://api.opensanctions.org/match/default"

    async def verify_identity(
        self,
        entity_name: str,
        entity_type: str,
        additional_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify entity identity and perform KYC checks using real API only

        Args:
            entity_name: Name of entity (person or company)
            entity_type: Type of entity
            additional_info: Additional data (address, DOB, ID numbers, etc.)

        Returns:
            Dictionary with identity verification results
        """
        if not self.use_real_api:
            return {
                "entity_name": entity_name,
                "entity_type": entity_type,
                "error": "API_NOT_CONFIGURED",
                "verification_status": "FAILED",
                "message": "SERPER_API_KEY not configured. Cannot perform real identity verification.",
                "requires_manual_check": True
            }

        return await self._verify_identity_real(entity_name, entity_type, additional_info)

    async def _verify_identity_real(
        self,
        entity_name: str,
        entity_type: str,
        additional_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify identity using real API"""
        try:
            # Search for entity information
            query_parts = [entity_name]
            if additional_info.get("country"):
                query_parts.append(additional_info["country"])
            if entity_type == "company":
                query_parts.append("company registration")
            elif entity_type == "individual":
                query_parts.append("professional profile")

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
                    identity_data = []

                    for result in data.get("organic", [])[:5]:
                        identity_data.append({
                            "source": result.get("title", ""),
                            "description": result.get("snippet", ""),
                            "link": result.get("link", "")
                        })

                    # Basic verification based on search results
                    verification_confidence = "MEDIUM" if len(identity_data) >= 3 else "LOW"

                    return {
                        "entity_name": entity_name,
                        "entity_type": entity_type,
                        "verification_method": "DOCUMENT_SEARCH",
                        "verification_confidence": verification_confidence,
                        "identity_data": identity_data,
                        "data_sources_found": len(identity_data),
                        "data_source": "real_search",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "entity_name": entity_name,
                        "entity_type": entity_type,
                        "error": "API_ERROR",
                        "verification_status": "FAILED",
                        "message": f"Identity verification API returned error: HTTP {response.status_code}",
                        "requires_manual_check": True
                    }

        except Exception as e:
            print(f"Error verifying identity: {e}")
            return {
                "entity_name": entity_name,
                "entity_type": entity_type,
                "error": "API_ERROR",
                "verification_status": "FAILED",
                "message": f"Failed to verify identity: {str(e)}",
                "requires_manual_check": True
            }

    def _verify_identity_mock(
        self,
        entity_name: str,
        entity_type: str,
        additional_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mock identity verification for demo/testing

        IMPORTANT: This returns MOCK DATA ONLY. Do not use for actual compliance decisions.
        """

        if entity_type == "company":
            return {
                "entity_name": entity_name,
                "entity_type": "company",
                "verification_method": "REGISTRY_CHECK (MOCK)",
                "verification_status": "UNVERIFIED",
                "verification_confidence": "MOCK_DATA",
                "company_details": {
                    "registration_number": "MOCK-REG-123456",
                    "incorporation_date": "Mock Data",
                    "jurisdiction": additional_info.get("country", "Unknown"),
                    "business_type": additional_info.get("industry", "Unknown"),
                    "status": "MOCK_DATA"
                },
                "beneficial_owners": [],
                "risk_indicators": ["Using mock data - actual verification required"],
                "data_source": "MOCK_DATA",
                "data_quality_warning": "⚠️ THIS IS MOCK DATA - Not suitable for actual compliance screening"
            }
        else:  # individual
            return {
                "entity_name": entity_name,
                "entity_type": "individual",
                "verification_method": "ID_VERIFICATION (MOCK)",
                "verification_status": "UNVERIFIED",
                "verification_confidence": "MOCK_DATA",
                "identity_details": {
                    "date_of_birth": "Mock Data",
                    "nationality": additional_info.get("country", "Unknown"),
                    "address": "Mock Data",
                    "id_type": "Mock",
                    "id_verified": False
                },
                "employment": {
                    "status": "Unknown",
                    "occupation": additional_info.get("occupation", "Unknown"),
                    "income_range": "Unknown"
                },
                "risk_indicators": ["Using mock data - actual verification required"],
                "data_source": "MOCK_DATA",
                "data_quality_warning": "⚠️ THIS IS MOCK DATA - Not suitable for actual compliance screening"
            }

    async def check_opensanctions_pep(self, entity_name: str) -> Dict[str, Any]:
        """
        Check PEP status using OpenSanctions.org API
        OpenSanctions includes comprehensive PEP databases

        Args:
            entity_name: Name of individual

        Returns:
            Dictionary with PEP status
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "queries": {
                        "entity1": {
                            "schema": "Person",
                            "properties": {
                                "name": [entity_name]
                            }
                        }
                    }
                }

                response = await client.post(
                    self.opensanctions_api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("responses", {}).get("entity1", {}).get("results", [])

                    # Check for PEP indicators in results
                    pep_matches = []
                    for result in results:
                        if result.get("score", 0) >= 0.7:
                            # Check if datasets or properties indicate PEP status
                            datasets = result.get("datasets", [])
                            properties = result.get("properties", {})
                            topics = properties.get("topics", [])

                            is_pep_match = any(
                                keyword in str(datasets + topics).lower()
                                for keyword in ["pep", "political", "government", "official"]
                            )

                            if is_pep_match or "pep" in result.get("schema", "").lower():
                                pep_matches.append({
                                    "name": result.get("caption", ""),
                                    "score": result.get("score", 0),
                                    "datasets": datasets,
                                    "topics": topics,
                                    "countries": properties.get("country", [])
                                })

                    is_pep = len(pep_matches) > 0
                    confidence = "HIGH" if pep_matches and pep_matches[0]["score"] >= 0.9 else "MEDIUM" if pep_matches else "NONE"

                    return {
                        "entity_name": entity_name,
                        "is_pep": is_pep,
                        "pep_confidence": confidence,
                        "pep_matches": pep_matches,
                        "risk_level": "HIGH" if is_pep else "LOW",
                        "data_source": "OpenSanctions.org",
                        "requires_enhanced_dd": is_pep
                    }

                else:
                    return {
                        "entity_name": entity_name,
                        "error": "API_ERROR",
                        "is_pep": None,
                        "message": f"OpenSanctions API returned error: HTTP {response.status_code}",
                        "requires_manual_check": True
                    }

        except Exception as e:
            print(f"Error checking OpenSanctions PEP: {e}")
            return {
                "entity_name": entity_name,
                "error": "API_ERROR",
                "is_pep": None,
                "message": f"Failed to check OpenSanctions PEP: {str(e)}",
                "requires_manual_check": True
            }

    async def check_pep_status(self, entity_name: str) -> Dict[str, Any]:
        """
        Check if entity is a Politically Exposed Person (PEP) using real API
        Tries OpenSanctions first, then falls back to web search

        Args:
            entity_name: Name of individual or company

        Returns:
            Dictionary with PEP status and details
        """
        # Try OpenSanctions first (free, comprehensive PEP database)
        opensanctions_result = await self.check_opensanctions_pep(entity_name)

        if not opensanctions_result.get("error"):
            return opensanctions_result

        # Fallback to web search if OpenSanctions fails
        if self.use_real_api:
            return await self._check_pep_real(entity_name)

        # No API available
        return {
            "entity_name": entity_name,
            "error": "API_NOT_CONFIGURED",
            "is_pep": None,
            "message": "OpenSanctions failed and no SERPER_API_KEY configured. Cannot perform PEP screening.",
            "requires_manual_check": True
        }

    async def _check_pep_real(self, entity_name: str) -> Dict[str, Any]:
        """Check PEP status using real API"""
        try:
            query = f"{entity_name} political position government official"

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
                    results = data.get("organic", [])

                    # Basic PEP detection based on keywords
                    pep_indicators = []
                    for result in results[:5]:
                        snippet = result.get("snippet", "").lower()
                        title = result.get("title", "").lower()
                        combined_text = f"{title} {snippet}"

                        political_keywords = [
                            "government", "minister", "senator", "congressman",
                            "official", "ambassador", "governor", "mayor",
                            "political", "parliament", "legislator"
                        ]

                        if any(keyword in combined_text for keyword in political_keywords):
                            pep_indicators.append({
                                "source": result.get("title", ""),
                                "description": result.get("snippet", ""),
                                "link": result.get("link", "")
                            })

                    is_pep = len(pep_indicators) >= 2
                    confidence = "HIGH" if len(pep_indicators) >= 3 else "MEDIUM" if len(pep_indicators) >= 2 else "LOW"

                    return {
                        "entity_name": entity_name,
                        "is_pep": is_pep,
                        "pep_confidence": confidence if is_pep else "N/A",
                        "pep_indicators": pep_indicators,
                        "risk_level": "HIGH" if is_pep else "LOW",
                        "data_source": "real_search",
                        "requires_enhanced_dd": is_pep
                    }
                else:
                    return {
                        "entity_name": entity_name,
                        "error": "API_ERROR",
                        "is_pep": None,
                        "message": f"PEP API returned error: HTTP {response.status_code}",
                        "requires_manual_check": True
                    }

        except Exception as e:
            print(f"Error checking PEP status: {e}")
            return {
                "entity_name": entity_name,
                "error": "API_ERROR",
                "is_pep": None,
                "message": f"Failed to check PEP status: {str(e)}",
                "requires_manual_check": True
            }

    def _check_pep_mock(self, entity_name: str) -> Dict[str, Any]:
        """
        Mock PEP check for demo/testing

        IMPORTANT: This returns MOCK DATA ONLY. Do not use for actual compliance decisions.
        """
        # Mock data: Only return PEP for obvious test cases
        known_pep_keywords = ["senator test", "minister test", "president test", "pep test"]
        is_pep = any(keyword in entity_name.lower() for keyword in known_pep_keywords)

        if is_pep:
            return {
                "entity_name": entity_name,
                "is_pep": True,
                "pep_category": "DOMESTIC_PEP",
                "pep_position": "Government Official (MOCK DATA)",
                "pep_level": "HIGH",
                "jurisdiction": "United States",
                "in_office": True,
                "family_members": [],
                "close_associates": [],
                "risk_level": "HIGH",
                "enhanced_dd_required": True,
                "data_source": "MOCK_DATA",
                "data_quality_warning": "⚠️ THIS IS MOCK DATA - Not suitable for actual compliance screening"
            }
        else:
            return {
                "entity_name": entity_name,
                "is_pep": False,
                "pep_category": "NOT_PEP",
                "risk_level": "LOW",
                "enhanced_dd_required": False,
                "data_source": "MOCK_DATA",
                "data_quality_warning": "⚠️ THIS IS MOCK DATA - Not suitable for actual compliance screening"
            }

    async def analyze_transaction_patterns(
        self,
        entity_name: str,
        additional_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze transaction patterns for suspicious activity

        Args:
            entity_name: Name of entity
            additional_info: Transaction data (amounts, patterns, frequency, etc.)

        Returns:
            Dictionary with transaction analysis and SAR triggers
        """
        # This is primarily rule-based analysis
        return self._analyze_transaction_patterns_internal(entity_name, additional_info)

    def _analyze_transaction_patterns_internal(
        self,
        entity_name: str,
        additional_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Internal transaction pattern analysis"""

        transaction_amount = additional_info.get("transaction_amount", 0)
        transaction_frequency = additional_info.get("transaction_frequency", "normal")
        transaction_type = additional_info.get("transaction_type", "wire_transfer")
        destination_country = additional_info.get("destination_country", "Unknown")

        # SAR trigger thresholds
        HIGH_VALUE_THRESHOLD = 10000  # $10,000 reporting threshold
        STRUCTURING_THRESHOLD = 9000  # Just below reporting threshold

        suspicious_indicators = []
        sar_triggers = []
        risk_score = 0

        # Rule 1: High value transactions
        if transaction_amount >= HIGH_VALUE_THRESHOLD:
            suspicious_indicators.append(f"High value transaction: ${transaction_amount:,.2f}")
            sar_triggers.append("CTR_THRESHOLD_EXCEEDED")
            risk_score += 30

        # Rule 2: Structuring (transactions just below reporting threshold)
        if STRUCTURING_THRESHOLD <= transaction_amount < HIGH_VALUE_THRESHOLD:
            suspicious_indicators.append(f"Potential structuring: ${transaction_amount:,.2f} (just below $10,000 threshold)")
            sar_triggers.append("POTENTIAL_STRUCTURING")
            risk_score += 50

        # Rule 3: High frequency transactions
        if transaction_frequency in ["high", "very_high", "unusual"]:
            suspicious_indicators.append(f"Unusual transaction frequency: {transaction_frequency}")
            sar_triggers.append("UNUSUAL_FREQUENCY")
            risk_score += 25

        # Rule 4: High-risk countries
        high_risk_countries = [
            "Iran", "North Korea", "Syria", "Cuba", "Venezuela",
            "Afghanistan", "Myanmar", "Belarus"
        ]
        if destination_country in high_risk_countries:
            suspicious_indicators.append(f"Transaction to high-risk jurisdiction: {destination_country}")
            sar_triggers.append("HIGH_RISK_JURISDICTION")
            risk_score += 40

        # Rule 5: Cash-intensive patterns
        if transaction_type in ["cash_deposit", "cash_withdrawal", "cash_exchange"]:
            suspicious_indicators.append(f"Cash-intensive transaction: {transaction_type}")
            sar_triggers.append("CASH_INTENSIVE")
            risk_score += 20

        # Determine risk level
        if risk_score >= 70:
            risk_level = "HIGH"
            sar_recommended = True
        elif risk_score >= 40:
            risk_level = "MEDIUM"
            sar_recommended = True
        else:
            risk_level = "LOW"
            sar_recommended = False

        return {
            "entity_name": entity_name,
            "transaction_amount": transaction_amount,
            "transaction_type": transaction_type,
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "suspicious_indicators": suspicious_indicators,
            "sar_triggers": sar_triggers,
            "sar_recommended": sar_recommended,
            "analysis_summary": f"Transaction analysis revealed {len(suspicious_indicators)} suspicious indicator(s)",
            "recommended_action": "FILE_SAR" if sar_recommended else "CONTINUE_MONITORING",
            "data_source": "rule_based_analysis"
        }

    async def check_adverse_media(self, entity_name: str) -> Dict[str, Any]:
        """
        Check for adverse media mentions using real API only

        Args:
            entity_name: Name of entity

        Returns:
            Dictionary with adverse media findings
        """
        if not self.use_real_api:
            return {
                "entity_name": entity_name,
                "error": "API_NOT_CONFIGURED",
                "adverse_media_found": None,
                "message": "SERPER_API_KEY not configured. Cannot perform real adverse media check.",
                "requires_manual_check": True
            }

        return await self._check_adverse_media_real(entity_name)

    async def _check_adverse_media_real(self, entity_name: str) -> Dict[str, Any]:
        """Check adverse media using real API"""
        try:
            query = f"{entity_name} fraud scandal investigation conviction money laundering"

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
                    adverse_findings = []

                    for result in data.get("organic", [])[:5]:
                        snippet = result.get("snippet", "").lower()
                        title = result.get("title", "").lower()
                        combined_text = f"{title} {snippet}"

                        # Check for adverse keywords
                        adverse_keywords = [
                            "fraud", "scandal", "investigation", "conviction",
                            "lawsuit", "fine", "penalty", "money laundering",
                            "corruption", "bribery", "embezzlement"
                        ]

                        if any(keyword in combined_text for keyword in adverse_keywords):
                            adverse_findings.append({
                                "title": result.get("title", ""),
                                "description": result.get("snippet", ""),
                                "source": result.get("link", ""),
                                "date": result.get("date", "Unknown")
                            })

                    return {
                        "entity_name": entity_name,
                        "adverse_media_found": len(adverse_findings) > 0,
                        "findings_count": len(adverse_findings),
                        "adverse_findings": adverse_findings,
                        "risk_level": "HIGH" if len(adverse_findings) >= 2 else "MEDIUM" if len(adverse_findings) == 1 else "LOW",
                        "data_source": "real_search"
                    }
                else:
                    return {
                        "entity_name": entity_name,
                        "error": "API_ERROR",
                        "adverse_media_found": None,
                        "message": f"Adverse media API returned error: HTTP {response.status_code}",
                        "requires_manual_check": True
                    }

        except Exception as e:
            print(f"Error checking adverse media: {e}")
            return {
                "entity_name": entity_name,
                "error": "API_ERROR",
                "adverse_media_found": None,
                "message": f"Failed to check adverse media: {str(e)}",
                "requires_manual_check": True
            }

    def _check_adverse_media_mock(self, entity_name: str) -> Dict[str, Any]:
        """Mock adverse media check for demo/testing"""
        return {
            "entity_name": entity_name,
            "adverse_media_found": False,
            "findings_count": 0,
            "adverse_findings": [],
            "risk_level": "LOW",
            "data_source": "mock_data",
            "note": "No adverse media found in mock data"
        }
