import re
from typing import Dict, List
import random
import httpx
import logging

logger = logging.getLogger(__name__)

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

class MLModelWorkflow(PhishingDetectionWorkflow):
    """Base class for ML model workflows that call external model services"""

    def __init__(self, name: str, model_url: str):
        super().__init__(name)
        self.model_url = model_url

    async def analyze(self, email_data: Dict) -> Dict:
        """Call the ML model service to analyze email"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.model_url}/predict",
                    json={
                        "subject": email_data.get("subject", ""),
                        "sender": email_data.get("sender", ""),
                        "body_text": email_data.get("body_text", ""),
                        "body_html": email_data.get("body_html", "")
                    }
                )
                response.raise_for_status()
                result = response.json()

                return {
                    "workflow": self.name,
                    "is_phishing_detected": result.get("is_phishing", False),
                    "confidence_score": int(result.get("confidence_score", 0)),
                    "risk_indicators": [
                        f"Spam probability: {result.get('spam_probability', 0):.1f}%"
                    ] if result.get("is_phishing") else [],
                    "details": {
                        "model": result.get("model_name", self.name),
                        "spam_probability": result.get("spam_probability", 0),
                        "ham_probability": result.get("ham_probability", 0)
                    }
                }
        except Exception as e:
            logger.error(f"ML model {self.name} error: {e}")
            return {
                "workflow": self.name,
                "is_phishing_detected": False,
                "confidence_score": 0,
                "risk_indicators": [],
                "error": str(e),
                "details": {}
            }


class LogisticRegressionWorkflow(MLModelWorkflow):
    """Logistic Regression ML model workflow"""
    def __init__(self):
        super().__init__("ML: Logistic Regression", "http://model-logistic-regression:8001")


class NaiveBayesWorkflow(MLModelWorkflow):
    """Naive Bayes ML model workflow"""
    def __init__(self):
        super().__init__("ML: Naive Bayes", "http://model-naive-bayes:8002")


class NeuralNetworkWorkflow(MLModelWorkflow):
    """Neural Network ML model workflow"""
    def __init__(self):
        super().__init__("ML: Neural Network", "http://model-neural-network:8003")


class RandomForestWorkflow(MLModelWorkflow):
    """Random Forest ML model workflow"""
    def __init__(self):
        super().__init__("ML: Random Forest", "http://model-random-forest:8004")


class SVMWorkflow(MLModelWorkflow):
    """Support Vector Machine ML model workflow"""
    def __init__(self):
        super().__init__("ML: SVM", "http://model-svm:8005")


class FineTunedLLMWorkflow(MLModelWorkflow):
    """Fine-tuned DistilBERT LLM model workflow"""
    def __init__(self):
        super().__init__("ML: Fine-tuned LLM (DistilBERT)", "http://model-fine-tuned-llm:8006")


class WorkflowEngine:
    """Manages and executes multiple analysis workflows"""

    def __init__(self):
        # Only keep models with meaningful performance (>50% F1-score)
        # Removed based on accuracy tests:
        # - URL Analysis: 0% precision/recall/F1
        # - Sender Analysis: 0% precision/recall/F1
        # - Content Analysis: 7.91% F1-score
        # - Logistic Regression: 0% precision/recall/F1
        # - Neural Network: 0% precision/recall/F1
        # - SVM: 0% precision/recall/F1
        self.workflows = [
            NaiveBayesWorkflow(),          # 76.50% accuracy, 74.81% F1
            RandomForestWorkflow(),         # 71.70% accuracy, 78.45% F1
            FineTunedLLMWorkflow()          # 59.00% accuracy, 45.77% F1
        ]

    async def run_all_workflows(self, email_data: Dict) -> List[Dict]:
        """Run all workflows on an email in parallel for better performance"""
        import asyncio

        # Run all workflows in parallel using asyncio.gather
        tasks = [workflow.analyze(email_data) for workflow in self.workflows]
        results = await asyncio.gather(*tasks)

        return list(results)

    async def run_workflow(self, workflow_name: str, email_data: Dict) -> Dict:
        """Run a specific workflow"""
        for workflow in self.workflows:
            if workflow.name == workflow_name:
                return await workflow.analyze(email_data)
        raise ValueError(f"Workflow '{workflow_name}' not found")
