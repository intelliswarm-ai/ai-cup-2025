"""
Policy Compliance Tools for email analysis
Checks if emails comply with company policies, detects direction (incoming/outgoing)
"""

import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import AsyncOpenAI


class PolicyComplianceTools:
    """Tools for checking email compliance with company policies"""

    def __init__(self):
        # Initialize OpenAI for policy analysis
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Company domains (configurable)
        self.company_domains = self._load_company_domains()

        # Policy categories
        self.policy_categories = [
            "data_leakage",
            "confidential_info",
            "inappropriate_content",
            "regulatory_compliance",
            "communication_standards",
            "security_protocols"
        ]

    def _load_company_domains(self) -> List[str]:
        """Load company email domains from environment or config"""
        # Default company domains (can be configured via env)
        env_domains = os.getenv("COMPANY_DOMAINS", "")

        if env_domains:
            return [d.strip() for d in env_domains.split(",")]

        # Default demo domains
        return [
            "example.com",
            "company.com",
            "corp.com",
            "internal.com"
        ]

    def detect_email_direction(
        self,
        sender: str,
        recipient: Optional[str] = None,
        email_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Detect if email is incoming or outgoing based on sender/recipient domains

        Args:
            sender: Email sender address
            recipient: Email recipient address (optional)
            email_headers: Email headers for additional context

        Returns:
            Dictionary with email direction information
        """
        sender_lower = sender.lower() if sender else ""
        recipient_lower = recipient.lower() if recipient else ""

        # Extract domain from email address
        def extract_domain(email: str) -> str:
            if "@" in email:
                return email.split("@")[1].strip()
            return ""

        sender_domain = extract_domain(sender_lower)
        recipient_domain = extract_domain(recipient_lower) if recipient else None

        # Check if sender is from company
        is_sender_internal = any(
            domain in sender_domain for domain in self.company_domains
        )

        # Check if recipient is from company
        is_recipient_internal = False
        if recipient_domain:
            is_recipient_internal = any(
                domain in recipient_domain for domain in self.company_domains
            )

        # Determine direction
        if is_sender_internal and not is_recipient_internal:
            direction = "outgoing"
            description = "Email sent from company to external party"
            risk_level = "MEDIUM"  # Outgoing emails have data leakage risk
        elif not is_sender_internal and is_recipient_internal:
            direction = "incoming"
            description = "Email received from external party"
            risk_level = "LOW"  # Incoming emails have lower policy risk
        elif is_sender_internal and is_recipient_internal:
            direction = "internal"
            description = "Email between company employees"
            risk_level = "LOW"
        else:
            direction = "external"
            description = "Email between external parties (forwarded/monitored)"
            risk_level = "LOW"

        return {
            "direction": direction,
            "description": description,
            "risk_level": risk_level,
            "sender_domain": sender_domain,
            "recipient_domain": recipient_domain,
            "is_sender_internal": is_sender_internal,
            "is_recipient_internal": is_recipient_internal,
            "company_domains": self.company_domains
        }

    async def check_policy_compliance(
        self,
        subject: str,
        body: str,
        sender: str,
        recipient: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Check if email complies with company policies

        Args:
            subject: Email subject
            body: Email body content
            sender: Email sender
            recipient: Email recipient (optional)
            attachments: List of attachment filenames (optional)

        Returns:
            Dictionary with policy compliance assessment
        """
        # Detect email direction first
        direction_info = self.detect_email_direction(sender, recipient)

        # Different policy checks based on direction
        if direction_info["direction"] == "outgoing":
            # More strict checks for outgoing emails
            return await self._check_outgoing_policy_compliance(
                subject, body, sender, recipient, attachments, direction_info
            )
        elif direction_info["direction"] == "incoming":
            # Check incoming emails for security/phishing
            return await self._check_incoming_policy_compliance(
                subject, body, sender, direction_info
            )
        else:
            # Internal emails - basic checks
            return await self._check_internal_policy_compliance(
                subject, body, direction_info
            )

    async def _check_outgoing_policy_compliance(
        self,
        subject: str,
        body: str,
        sender: str,
        recipient: Optional[str],
        attachments: Optional[List[str]],
        direction_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check outgoing email for policy compliance"""

        # Pattern-based checks
        violations = []
        risk_indicators = []

        # Check for sensitive data patterns
        patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "api_key": r"(api[_-]?key|token)[\"']?\s*[:=]\s*[\"']?[\w\-]{20,}",
            "password": r"(password|pwd)[\"']?\s*[:=]\s*[\"']?[\w@#$%^&*]{8,}",
            "confidential": r"\b(confidential|secret|internal only|proprietary)\b",
        }

        combined_text = f"{subject} {body}".lower()

        for pattern_name, pattern in patterns.items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                violations.append({
                    "type": "data_leakage",
                    "severity": "HIGH" if pattern_name in ["ssn", "credit_card", "api_key", "password"] else "MEDIUM",
                    "description": f"Potential {pattern_name.replace('_', ' ')} detected in email content",
                    "policy": "Data Protection Policy"
                })
                risk_indicators.append(f"Contains potential {pattern_name}")

        # Check attachments for sensitive file types
        if attachments:
            sensitive_extensions = [".xlsx", ".xls", ".csv", ".db", ".sql", ".key", ".pem"]
            for attachment in attachments:
                if any(attachment.lower().endswith(ext) for ext in sensitive_extensions):
                    violations.append({
                        "type": "data_leakage",
                        "severity": "MEDIUM",
                        "description": f"Sensitive file type attached: {attachment}",
                        "policy": "Data Protection Policy"
                    })
                    risk_indicators.append(f"Sensitive attachment: {attachment}")

        # LLM-based policy analysis for complex violations
        llm_analysis = await self._llm_policy_analysis(
            subject, body, "outgoing", violations
        )

        # Combine results
        all_violations = violations + llm_analysis.get("additional_violations", [])

        # Determine compliance status
        if any(v["severity"] == "HIGH" for v in all_violations):
            compliance_status = "NON_COMPLIANT"
            overall_risk = "HIGH"
        elif any(v["severity"] == "MEDIUM" for v in all_violations):
            compliance_status = "REQUIRES_REVIEW"
            overall_risk = "MEDIUM"
        else:
            compliance_status = "COMPLIANT"
            overall_risk = "LOW"

        return {
            "compliance_status": compliance_status,
            "email_direction": direction_info["direction"],
            "overall_risk": overall_risk,
            "violations": all_violations,
            "risk_indicators": risk_indicators,
            "policy_categories_checked": self.policy_categories,
            "recommendations": self._generate_recommendations(all_violations),
            "direction_info": direction_info,
            "requires_approval": compliance_status in ["NON_COMPLIANT", "REQUIRES_REVIEW"],
            "timestamp": datetime.now().isoformat()
        }

    async def _check_incoming_policy_compliance(
        self,
        subject: str,
        body: str,
        sender: str,
        direction_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check incoming email for policy compliance (mainly security)"""

        violations = []
        risk_indicators = []

        # Check for phishing indicators
        phishing_keywords = [
            "urgent", "verify your account", "suspended", "click here immediately",
            "confirm your password", "unusual activity", "expire", "locked"
        ]

        combined_text = f"{subject} {body}".lower()

        for keyword in phishing_keywords:
            if keyword in combined_text:
                risk_indicators.append(f"Phishing indicator: {keyword}")

        # Check for suspicious links
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, body)

        if urls:
            # Check for URL shorteners or suspicious domains
            suspicious_domains = ["bit.ly", "tinyurl", "t.co", "goo.gl"]
            for url in urls:
                if any(domain in url for domain in suspicious_domains):
                    violations.append({
                        "type": "security",
                        "severity": "MEDIUM",
                        "description": f"Suspicious shortened URL detected: {url[:50]}...",
                        "policy": "Email Security Policy"
                    })

        # LLM analysis for incoming emails
        llm_analysis = await self._llm_policy_analysis(
            subject, body, "incoming", violations
        )

        all_violations = violations + llm_analysis.get("additional_violations", [])

        # For incoming emails, focus on security rather than data leakage
        if any(v["severity"] == "HIGH" for v in all_violations):
            compliance_status = "POTENTIAL_THREAT"
            overall_risk = "HIGH"
        elif any(v["severity"] == "MEDIUM" for v in all_violations):
            compliance_status = "REQUIRES_REVIEW"
            overall_risk = "MEDIUM"
        else:
            compliance_status = "COMPLIANT"
            overall_risk = "LOW"

        return {
            "compliance_status": compliance_status,
            "email_direction": direction_info["direction"],
            "overall_risk": overall_risk,
            "violations": all_violations,
            "risk_indicators": risk_indicators,
            "policy_categories_checked": ["security_protocols", "phishing_prevention"],
            "recommendations": self._generate_recommendations(all_violations),
            "direction_info": direction_info,
            "requires_review": len(risk_indicators) > 0,
            "timestamp": datetime.now().isoformat()
        }

    async def _check_internal_policy_compliance(
        self,
        subject: str,
        body: str,
        direction_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check internal email for basic policy compliance"""

        violations = []

        # Basic checks for internal emails
        if "confidential" in f"{subject} {body}".lower():
            violations.append({
                "type": "information_classification",
                "severity": "LOW",
                "description": "Email marked as confidential - ensure proper handling",
                "policy": "Information Classification Policy"
            })

        return {
            "compliance_status": "COMPLIANT",
            "email_direction": direction_info["direction"],
            "overall_risk": "LOW",
            "violations": violations,
            "risk_indicators": [],
            "policy_categories_checked": ["communication_standards"],
            "recommendations": [],
            "direction_info": direction_info,
            "requires_review": False,
            "timestamp": datetime.now().isoformat()
        }

    async def _llm_policy_analysis(
        self,
        subject: str,
        body: str,
        direction: str,
        existing_violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use LLM to detect complex policy violations"""

        try:
            prompt = f"""You are a compliance officer reviewing an email for policy violations.

Email Direction: {direction}
Subject: {subject}
Body: {body[:1000]}  # First 1000 chars

Existing violations detected: {len(existing_violations)}

Analyze this email for the following policy violations:
1. **Inappropriate Content**: Unprofessional language, harassment, discrimination
2. **Regulatory Violations**: GDPR violations, financial regulations, industry-specific rules
3. **Communication Standards**: Poor professionalism, unauthorized disclosures
4. **Security Risks**: Sharing credentials, internal system details, architecture info

Focus on violations NOT already detected by pattern matching.

Return ONLY a JSON object:
{{
    "additional_violations": [
        {{
            "type": "category",
            "severity": "HIGH|MEDIUM|LOW",
            "description": "specific violation description",
            "policy": "policy name violated"
        }}
    ],
    "overall_assessment": "brief summary"
}}

If no additional violations, return empty array."""

            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"additional_violations": [], "overall_assessment": "Analysis completed"}

        except Exception as e:
            print(f"Error in LLM policy analysis: {e}")
            return {"additional_violations": [], "overall_assessment": "Analysis failed"}

    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on violations"""

        recommendations = []

        for violation in violations:
            violation_type = violation.get("type", "")
            severity = violation.get("severity", "")

            if violation_type == "data_leakage":
                if severity == "HIGH":
                    recommendations.append("Block email - contains sensitive data (SSN/credit card/password)")
                    recommendations.append("Contact sender to use secure file transfer")
                else:
                    recommendations.append("Review email for data sensitivity before sending")
                    recommendations.append("Consider using encryption or secure channels")

            elif violation_type == "security":
                recommendations.append("Warn user about potential phishing attempt")
                recommendations.append("Do not click links or download attachments")

            elif violation_type == "inappropriate_content":
                recommendations.append("Review content for professionalism")
                recommendations.append("Escalate to HR if necessary")

        # Remove duplicates
        return list(set(recommendations))
