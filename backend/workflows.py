import re
from typing import Dict, List
import random

class PhishingDetectionWorkflow:
    """Base class for phishing detection workflows"""

    def __init__(self, name: str):
        self.name = name

    async def analyze(self, email_data: Dict) -> Dict:
        """Analyze email for phishing indicators"""
        raise NotImplementedError

class URLAnalysisWorkflow(PhishingDetectionWorkflow):
    """Analyzes URLs in email for suspicious patterns"""

    def __init__(self):
        super().__init__("URL Analysis")
        self.suspicious_domains = [
            "bit.ly", "tinyurl.com", "secure-bank", "verify-account",
            "update-info", "confirm-details", "banking-security"
        ]

    async def analyze(self, email_data: Dict) -> Dict:
        text = email_data.get("body_text", "") + email_data.get("body_html", "")

        # Extract URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)

        risk_indicators = []
        confidence = 0

        for url in urls:
            # Check for suspicious domains
            if any(domain in url.lower() for domain in self.suspicious_domains):
                risk_indicators.append(f"Suspicious domain in URL: {url}")
                confidence += 30

            # Check for IP addresses in URLs
            if re.search(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
                risk_indicators.append(f"IP address used instead of domain: {url}")
                confidence += 25

            # Check for URL shorteners
            if any(shortener in url for shortener in ["bit.ly", "tinyurl", "goo.gl"]):
                risk_indicators.append(f"URL shortener detected: {url}")
                confidence += 20

        is_phishing = confidence > 50
        confidence = min(confidence, 100)

        return {
            "workflow": self.name,
            "is_phishing_detected": is_phishing,
            "confidence_score": confidence,
            "risk_indicators": risk_indicators,
            "urls_found": len(urls),
            "details": {
                "urls_analyzed": urls
            }
        }

class SenderAnalysisWorkflow(PhishingDetectionWorkflow):
    """Analyzes sender information for spoofing attempts"""

    def __init__(self):
        super().__init__("Sender Analysis")
        self.legitimate_domains = ["@bank.com", "@customerservice.bank.com"]

    async def analyze(self, email_data: Dict) -> Dict:
        sender = email_data.get("sender", "")
        subject = email_data.get("subject", "")

        risk_indicators = []
        confidence = 0

        # Check if sender claims to be from bank but uses different domain
        if "bank" in subject.lower() or "account" in subject.lower():
            if not any(domain in sender.lower() for domain in self.legitimate_domains):
                risk_indicators.append(f"Sender domain doesn't match expected bank domain")
                confidence += 40

        # Check for common spoofing patterns
        if "noreply" in sender.lower() or "no-reply" in sender.lower():
            risk_indicators.append("Generic no-reply sender address")
            confidence += 15

        # Check for numbers in sender domain (common in phishing)
        domain_match = re.search(r'@([^\s>]+)', sender)
        if domain_match:
            domain = domain_match.group(1)
            if re.search(r'\d{3,}', domain):
                risk_indicators.append(f"Suspicious numbers in domain: {domain}")
                confidence += 25

        is_phishing = confidence > 40
        confidence = min(confidence, 100)

        return {
            "workflow": self.name,
            "is_phishing_detected": is_phishing,
            "confidence_score": confidence,
            "risk_indicators": risk_indicators,
            "details": {
                "sender": sender
            }
        }

class ContentAnalysisWorkflow(PhishingDetectionWorkflow):
    """Analyzes email content for phishing language patterns"""

    def __init__(self):
        super().__init__("Content Analysis")
        self.urgency_keywords = [
            "urgent", "immediately", "action required", "verify now",
            "suspended", "locked", "expired", "confirm", "update",
            "unusual activity", "suspicious activity", "unauthorized"
        ]
        self.personal_info_requests = [
            "password", "ssn", "social security", "credit card",
            "pin", "account number", "routing number", "cvv"
        ]

    async def analyze(self, email_data: Dict) -> Dict:
        text = (email_data.get("body_text", "") + " " +
                email_data.get("subject", "")).lower()

        risk_indicators = []
        confidence = 0

        # Check for urgency language
        urgency_count = sum(1 for keyword in self.urgency_keywords if keyword in text)
        if urgency_count >= 2:
            risk_indicators.append(f"Multiple urgency keywords detected ({urgency_count})")
            confidence += urgency_count * 15

        # Check for personal information requests
        info_requests = [kw for kw in self.personal_info_requests if kw in text]
        if info_requests:
            risk_indicators.append(f"Requests for sensitive information: {', '.join(info_requests)}")
            confidence += len(info_requests) * 20

        # Check for generic greetings (phishing often doesn't personalize)
        if any(greeting in text for greeting in ["dear customer", "dear user", "dear member"]):
            risk_indicators.append("Generic greeting used instead of personalized")
            confidence += 15

        is_phishing = confidence > 45
        confidence = min(confidence, 100)

        return {
            "workflow": self.name,
            "is_phishing_detected": is_phishing,
            "confidence_score": confidence,
            "risk_indicators": risk_indicators,
            "details": {
                "urgency_keywords_found": urgency_count,
                "sensitive_info_requests": len(info_requests)
            }
        }

class WorkflowEngine:
    """Manages and executes multiple analysis workflows"""

    def __init__(self):
        self.workflows = [
            URLAnalysisWorkflow(),
            SenderAnalysisWorkflow(),
            ContentAnalysisWorkflow()
        ]

    async def run_all_workflows(self, email_data: Dict) -> List[Dict]:
        """Run all workflows on an email"""
        results = []
        for workflow in self.workflows:
            result = await workflow.analyze(email_data)
            results.append(result)
        return results

    async def run_workflow(self, workflow_name: str, email_data: Dict) -> Dict:
        """Run a specific workflow"""
        for workflow in self.workflows:
            if workflow.name == workflow_name:
                return await workflow.analyze(email_data)
        raise ValueError(f"Workflow '{workflow_name}' not found")
