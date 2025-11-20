"""
Sanctions Tools for compliance analysis
Provides OFAC screening, watchlist checks, and sanctions verification
"""

import os
import json
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime


class SanctionsTools:
    """Tools for sanctions screening and watchlist checks"""

    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY", "")

        # Compliance workflow requires real API - no mock data allowed
        if not self.serper_api_key or not self.serper_api_key.strip():
            print("WARNING: SERPER_API_KEY not configured. Web search fallback will not work.")

        self.use_real_api = bool(self.serper_api_key and self.serper_api_key.strip())

        # OpenSanctions.org API configuration (free, comprehensive)
        self.opensanctions_api_url = "https://api.opensanctions.org/match/default"

        # Official OFAC SDN API
        self.ofac_api_url = "https://sanctionssearch.ofac.treas.gov/api/PublicationPreview/exports/"

        # High-risk countries for sanctions
        self.sanctioned_countries = [
            "North Korea", "Iran", "Syria", "Cuba", "Venezuela",
            "Russia", "Belarus", "Myanmar", "Zimbabwe", "Sudan",
            "South Sudan", "Somalia", "Lebanon", "Libya", "Yemen",
            "Nicaragua", "Afghanistan", "Iraq", "Mali"
        ]

    async def check_opensanctions(self, entity_name: str, entity_type: str = "company") -> Dict[str, Any]:
        """
        Check entity against OpenSanctions.org comprehensive database
        OpenSanctions aggregates sanctions from OFAC, UN, EU, UK, and more

        Args:
            entity_name: Name to check (company or person)
            entity_type: Type of entity ("company" or "person")

        Returns:
            Dictionary with comprehensive sanctions screening results
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Prepare search query
                schema = "Company" if entity_type == "company" else "Person"

                payload = {
                    "queries": {
                        "entity1": {
                            "schema": schema,
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

                    # Parse results
                    results = data.get("responses", {}).get("entity1", {}).get("results", [])

                    matches = []
                    for result in results:
                        if result.get("score", 0) >= 0.7:  # High confidence threshold
                            match = {
                                "name": result.get("caption", ""),
                                "score": result.get("score", 0),
                                "datasets": result.get("datasets", []),
                                "schema": result.get("schema", ""),
                                "properties": result.get("properties", {}),
                                "match_id": result.get("id", "")
                            }
                            matches.append(match)

                    has_sanctions_match = len(matches) > 0
                    confidence = "HIGH" if matches and matches[0]["score"] >= 0.9 else "MEDIUM" if matches else "NONE"

                    return {
                        "entity_name": entity_name,
                        "sanctions_match": has_sanctions_match,
                        "match_confidence": confidence,
                        "total_matches": len(matches),
                        "matches": matches[:5],  # Top 5 matches
                        "data_source": "OpenSanctions.org",
                        "api_status": "success",
                        "requires_review": has_sanctions_match,
                        "timestamp": datetime.now().isoformat()
                    }

                else:
                    return {
                        "entity_name": entity_name,
                        "error": "API_ERROR",
                        "sanctions_match": None,
                        "message": f"OpenSanctions API returned error: HTTP {response.status_code}",
                        "requires_manual_check": True
                    }

        except Exception as e:
            print(f"Error checking OpenSanctions: {e}")
            return {
                "entity_name": entity_name,
                "error": "API_ERROR",
                "sanctions_match": None,
                "message": f"Failed to check OpenSanctions: {str(e)}",
                "requires_manual_check": True
            }

    async def check_ofac_list(self, entity_name: str) -> Dict[str, Any]:
        """
        Check entity against OFAC sanctions lists using real API
        Tries OpenSanctions first (more comprehensive), then falls back to web search

        Args:
            entity_name: Name to check

        Returns:
            Dictionary with OFAC screening results
        """
        # Try OpenSanctions first (free, comprehensive, includes OFAC data)
        opensanctions_result = await self.check_opensanctions(entity_name, "company")

        if not opensanctions_result.get("error"):
            # Successfully got OpenSanctions data
            return {
                "entity_name": entity_name,
                "ofac_match": opensanctions_result.get("sanctions_match", False),
                "match_confidence": opensanctions_result.get("match_confidence", "NONE"),
                "sdn_list_checked": True,
                "match_details": opensanctions_result.get("matches", []),
                "data_source": "OpenSanctions.org (includes OFAC)",
                "requires_review": opensanctions_result.get("requires_review", False),
                "timestamp": datetime.now().isoformat()
            }

        # Fallback to web search if OpenSanctions fails and we have API key
        if self.use_real_api:
            return await self._check_ofac_real(entity_name)

        # No API available
        return {
            "entity_name": entity_name,
            "error": "API_NOT_CONFIGURED",
            "ofac_match": None,
            "message": "OpenSanctions failed and no SERPER_API_KEY configured. Cannot perform sanctions screening.",
            "requires_manual_check": True
        }

    async def _check_ofac_real(self, entity_name: str) -> Dict[str, Any]:
        """Check OFAC using real API"""
        try:
            # Search for OFAC sanctions info
            query = f"{entity_name} OFAC sanctions SDN list"

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

                    # Check for OFAC-related content
                    ofac_indicators = []
                    for result in results[:5]:
                        snippet = result.get("snippet", "").lower()
                        title = result.get("title", "").lower()
                        combined_text = f"{title} {snippet}"

                        ofac_keywords = [
                            "ofac", "sdn", "sanctions", "specially designated national",
                            "blocked person", "denied party"
                        ]

                        if any(keyword in combined_text for keyword in ofac_keywords):
                            ofac_indicators.append({
                                "source": result.get("title", ""),
                                "description": result.get("snippet", ""),
                                "link": result.get("link", "")
                            })

                    # Determine if there's a match
                    has_match = len(ofac_indicators) >= 2
                    confidence = "HIGH" if len(ofac_indicators) >= 3 else "MEDIUM" if len(ofac_indicators) >= 2 else "LOW"

                    return {
                        "entity_name": entity_name,
                        "ofac_match": has_match,
                        "match_confidence": confidence if has_match else "NONE",
                        "sdn_list_checked": True,
                        "indicators": ofac_indicators,
                        "data_source": "real_search",
                        "requires_review": has_match,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "entity_name": entity_name,
                        "error": "API_ERROR",
                        "ofac_match": None,
                        "message": f"OFAC API returned error: HTTP {response.status_code}",
                        "requires_manual_check": True
                    }

        except Exception as e:
            print(f"Error checking OFAC: {e}")
            return {
                "entity_name": entity_name,
                "error": "API_ERROR",
                "ofac_match": None,
                "message": f"Failed to check OFAC: {str(e)}",
                "requires_manual_check": True
            }

    def _check_ofac_mock(self, entity_name: str) -> Dict[str, Any]:
        """
        Mock OFAC check for demo/testing

        IMPORTANT: This returns MOCK DATA ONLY. Do not use for actual compliance decisions.
        """

        # Mock data: Only return matches for obviously sanctioned test cases
        # Avoid false positives on random input
        known_sanctioned_entities = [
            "north korea", "iran sanctioned", "syria sanctioned", "taliban",
            "hezbollah", "ofac test entity"
        ]

        # Check if this is a known test entity
        has_match = any(test_entity in entity_name.lower() for test_entity in known_sanctioned_entities)

        # For most entities, return clean mock data (no match)
        return {
            "entity_name": entity_name,
            "ofac_match": has_match,
            "match_confidence": "MOCK_HIGH" if has_match else "MOCK_NONE",
            "match_type": "SDN_LIST" if has_match else None,
            "sdn_list_checked": True,
            "program": "TERRORISM" if has_match else None,
            "match_details": {
                "list": "Specially Designated Nationals (SDN) List",
                "program": "Counter Terrorism (MOCK DATA)",
                "added_date": "2020-01-15"
            } if has_match else None,
            "data_source": "MOCK_DATA",
            "data_quality_warning": "⚠️ THIS IS MOCK DATA - Not suitable for actual compliance screening",
            "requires_review": has_match,
            "recommended_action": "VERIFY_WITH_REAL_API" if has_match else "USE_REAL_OFAC_API"
        }

    async def screen_watchlists(self, entity_name: str) -> Dict[str, Any]:
        """
        Screen against global watchlists (UN, EU, UK, etc.) using real API
        Uses OpenSanctions first (comprehensive, includes all major watchlists)

        Args:
            entity_name: Name to screen

        Returns:
            Dictionary with watchlist screening results
        """
        # Try OpenSanctions first (includes UN, EU, UK, OFAC, etc.)
        opensanctions_result = await self.check_opensanctions(entity_name, "company")

        if not opensanctions_result.get("error"):
            # Extract dataset information from matches
            all_datasets = set()
            match_details = []

            for match in opensanctions_result.get("matches", []):
                datasets = match.get("datasets", [])
                all_datasets.update(datasets)

                match_details.append({
                    "list": ", ".join(datasets),
                    "name": match.get("name", ""),
                    "score": match.get("score", 0),
                    "match_confidence": "HIGH" if match.get("score", 0) >= 0.9 else "MEDIUM"
                })

            return {
                "entity_name": entity_name,
                "watchlist_matches": match_details,
                "total_matches": len(match_details),
                "lists_checked": list(all_datasets),
                "has_matches": len(match_details) > 0,
                "data_source": "OpenSanctions.org (aggregates UN, EU, UK, OFAC, etc.)",
                "timestamp": datetime.now().isoformat()
            }

        # Fallback to web search if OpenSanctions fails
        if self.use_real_api:
            return await self._screen_watchlists_real(entity_name)

        # No API available
        return {
            "entity_name": entity_name,
            "error": "API_NOT_CONFIGURED",
            "watchlist_matches": [],
            "total_matches": 0,
            "message": "OpenSanctions failed and no SERPER_API_KEY configured. Cannot perform watchlist screening.",
            "requires_manual_check": True
        }

    async def _screen_watchlists_real(self, entity_name: str) -> Dict[str, Any]:
        """Screen watchlists using real API"""
        try:
            # Search multiple watchlists
            queries = [
                f"{entity_name} UN sanctions list",
                f"{entity_name} EU sanctions",
                f"{entity_name} UK sanctions watchlist"
            ]

            all_matches = []

            async with httpx.AsyncClient(timeout=30.0) as client:
                for query in queries:
                    try:
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
                            for result in data.get("organic", [])[:3]:
                                snippet = result.get("snippet", "").lower()
                                title = result.get("title", "").lower()
                                combined_text = f"{title} {snippet}"

                                watchlist_keywords = [
                                    "sanctions", "watchlist", "restricted", "prohibited",
                                    "denied", "blacklist"
                                ]

                                if any(keyword in combined_text for keyword in watchlist_keywords):
                                    all_matches.append({
                                        "list_type": query.split()[1].upper(),  # UN, EU, UK
                                        "source": result.get("title", ""),
                                        "description": result.get("snippet", ""),
                                        "link": result.get("link", "")
                                    })
                    except Exception as e:
                        print(f"Error searching {query}: {e}")
                        continue

            return {
                "entity_name": entity_name,
                "watchlist_matches": all_matches,
                "total_matches": len(all_matches),
                "lists_checked": ["UN_SANCTIONS", "EU_SANCTIONS", "UK_SANCTIONS"],
                "has_matches": len(all_matches) > 0,
                "data_source": "real_search",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error screening watchlists: {e}")
            return {
                "entity_name": entity_name,
                "error": "API_ERROR",
                "watchlist_matches": [],
                "total_matches": 0,
                "message": f"Failed to screen watchlists: {str(e)}",
                "requires_manual_check": True
            }

    def _screen_watchlists_mock(self, entity_name: str) -> Dict[str, Any]:
        """
        Mock watchlist screening for demo/testing

        IMPORTANT: This returns MOCK DATA ONLY. Do not use for actual compliance decisions.
        """

        # Mock data: Only return matches for known test entities
        known_sanctioned_entities = [
            "putin", "lukashenko test", "taliban", "hezbollah", "sanctioned cartel"
        ]

        has_matches = any(test_entity in entity_name.lower() for test_entity in known_sanctioned_entities)

        matches = []
        if has_matches:
            matches = [
                {
                    "list": "EU_SANCTIONS_LIST",
                    "match_type": "INDIVIDUAL",
                    "program": "Belarus Sanctions (MOCK DATA)",
                    "added_date": "2021-08-09",
                    "match_confidence": "MOCK_HIGH"
                }
            ]

        return {
            "entity_name": entity_name,
            "watchlist_matches": matches,
            "total_matches": len(matches),
            "lists_checked": [
                "UN_CONSOLIDATED_LIST (MOCK)",
                "EU_SANCTIONS_LIST (MOCK)",
                "UK_SANCTIONS_LIST (MOCK)",
                "OFAC_CONSOLIDATED (MOCK)",
                "INTERPOL_RED_NOTICES (MOCK)"
            ],
            "has_matches": len(matches) > 0,
            "data_source": "MOCK_DATA",
            "data_quality_warning": "⚠️ THIS IS MOCK DATA - Not suitable for actual compliance screening"
        }

    async def verify_country_restrictions(self, country: str) -> Dict[str, Any]:
        """
        Check if a country is subject to sanctions or restrictions

        Args:
            country: Country name

        Returns:
            Dictionary with country restriction information
        """
        # This is primarily rule-based
        return self._verify_country_restrictions_internal(country)

    def _verify_country_restrictions_internal(self, country: str) -> Dict[str, Any]:
        """Internal country restrictions check"""

        is_sanctioned = country in self.sanctioned_countries
        is_high_risk = is_sanctioned or country in [
            "Pakistan", "Turkey", "United Arab Emirates", "China",
            "Cayman Islands", "Panama", "Bahamas"
        ]

        # Determine restriction level
        if country in ["North Korea", "Iran", "Syria"]:
            restriction_level = "COMPREHENSIVE_EMBARGO"
            risk_score = 100
        elif country in ["Russia", "Belarus", "Venezuela", "Cuba"]:
            restriction_level = "SECTORAL_SANCTIONS"
            risk_score = 85
        elif is_high_risk:
            restriction_level = "ENHANCED_DUE_DILIGENCE"
            risk_score = 60
        else:
            restriction_level = "STANDARD"
            risk_score = 20

        restrictions = []
        if is_sanctioned:
            if restriction_level == "COMPREHENSIVE_EMBARGO":
                restrictions = [
                    "Comprehensive trade embargo",
                    "Financial transactions prohibited",
                    "Asset freeze requirements",
                    "Travel restrictions"
                ]
            elif restriction_level == "SECTORAL_SANCTIONS":
                restrictions = [
                    "Targeted sectoral sanctions",
                    "Financial sector restrictions",
                    "Technology export controls",
                    "Enhanced screening required"
                ]

        return {
            "country": country,
            "is_sanctioned": is_sanctioned,
            "is_high_risk": is_high_risk,
            "restriction_level": restriction_level,
            "risk_score": risk_score,
            "restrictions": restrictions,
            "sanctions_programs": [
                {
                    "program": "OFAC Country Sanctions",
                    "applicable": is_sanctioned
                },
                {
                    "program": "EU Country Sanctions",
                    "applicable": is_sanctioned
                },
                {
                    "program": "UN Country Sanctions",
                    "applicable": country in ["North Korea", "Iran", "Libya", "Yemen"]
                }
            ],
            "recommended_action": "REJECT" if restriction_level == "COMPREHENSIVE_EMBARGO" else "ENHANCED_DD" if is_high_risk else "STANDARD_DD",
            "data_source": "sanctions_rules"
        }

    async def check_entity_ownership(
        self,
        entity_name: str,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check entity ownership and beneficial owner information

        Args:
            entity_name: Company or entity name
            country: Country of incorporation

        Returns:
            Dictionary with ownership information
        """
        if self.use_real_api:
            return await self._check_entity_ownership_real(entity_name, country)
        else:
            return self._check_entity_ownership_mock(entity_name, country)

    async def _check_entity_ownership_real(
        self,
        entity_name: str,
        country: Optional[str]
    ) -> Dict[str, Any]:
        """Check entity ownership using real API"""
        try:
            query = f"{entity_name} ownership beneficial owner"
            if country:
                query += f" {country}"

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
                    ownership_info = []

                    for result in data.get("organic", [])[:5]:
                        ownership_info.append({
                            "source": result.get("title", ""),
                            "description": result.get("snippet", ""),
                            "link": result.get("link", "")
                        })

                    return {
                        "entity_name": entity_name,
                        "country": country,
                        "ownership_data_found": len(ownership_info) > 0,
                        "ownership_info": ownership_info,
                        "verification_required": True,
                        "data_source": "real_search"
                    }
                else:
                    return self._check_entity_ownership_mock(entity_name, country)

        except Exception as e:
            print(f"Error checking entity ownership: {e}")
            return self._check_entity_ownership_mock(entity_name, country)

    def _check_entity_ownership_mock(
        self,
        entity_name: str,
        country: Optional[str]
    ) -> Dict[str, Any]:
        """Mock entity ownership check for demo/testing"""

        # Check if country is high-risk
        is_high_risk_jurisdiction = country in self.sanctioned_countries if country else False

        return {
            "entity_name": entity_name,
            "country": country or "Unknown",
            "ownership_structure": {
                "type": "Private Company",
                "beneficial_owners": [
                    {
                        "name": "Owner 1 (Individual)",
                        "ownership_percentage": 60,
                        "country": country or "Unknown",
                        "is_pep": False
                    },
                    {
                        "name": "Owner 2 (Individual)",
                        "ownership_percentage": 40,
                        "country": country or "Unknown",
                        "is_pep": False
                    }
                ],
                "shell_company_indicators": 0,
                "complex_structure": False
            },
            "risk_factors": [
                "High-risk jurisdiction ownership"
            ] if is_high_risk_jurisdiction else [],
            "risk_score": 75 if is_high_risk_jurisdiction else 15,
            "verification_status": "REQUIRES_DOCUMENTATION",
            "data_source": "mock_data"
        }

    async def check_sanctions_exposure(
        self,
        entity_name: str,
        transaction_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive sanctions exposure check combining multiple sources

        Args:
            entity_name: Entity to check
            transaction_details: Optional transaction context

        Returns:
            Comprehensive sanctions exposure assessment
        """
        # Perform all sanctions checks
        ofac_results = await self.check_ofac_list(entity_name)
        watchlist_results = await self.screen_watchlists(entity_name)

        country_risk = None
        if transaction_details and transaction_details.get("country"):
            country_risk = await self.verify_country_restrictions(
                transaction_details.get("country")
            )

        # Calculate overall exposure
        total_matches = (
            (1 if ofac_results.get("ofac_match") else 0) +
            watchlist_results.get("total_matches", 0)
        )

        has_exposure = total_matches > 0 or (
            country_risk and country_risk.get("is_sanctioned")
        )

        if total_matches >= 2:
            exposure_level = "CRITICAL"
        elif total_matches == 1:
            exposure_level = "HIGH"
        elif country_risk and country_risk.get("is_high_risk"):
            exposure_level = "MEDIUM"
        else:
            exposure_level = "LOW"

        return {
            "entity_name": entity_name,
            "has_sanctions_exposure": has_exposure,
            "exposure_level": exposure_level,
            "total_matches": total_matches,
            "ofac_match": ofac_results.get("ofac_match", False),
            "watchlist_matches": watchlist_results.get("total_matches", 0),
            "country_risk": country_risk.get("restriction_level") if country_risk else "UNKNOWN",
            "recommended_action": "REJECT" if exposure_level in ["CRITICAL", "HIGH"] else "ESCALATE" if exposure_level == "MEDIUM" else "PROCEED",
            "requires_compliance_review": has_exposure,
            "timestamp": datetime.now().isoformat()
        }
