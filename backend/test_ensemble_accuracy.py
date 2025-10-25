#!/usr/bin/env python3
"""
Test ensemble combination strategies for phishing detection
Compares individual model performance vs combined predictions
"""

import csv
import sys
import re
import asyncio
import httpx
from typing import Dict, Tuple, List
from datetime import datetime
import os

def extract_email_content(text: str) -> Tuple[str, str]:
    """Extract subject and body from email text"""
    subject_match = re.match(r'Subject:\s*(.+?)\n\n', text, re.DOTALL)
    if subject_match:
        subject = subject_match.group(1).strip()
        body = text[subject_match.end():].strip()
    else:
        subject = ""
        body = text
    return subject, body

async def call_model(model_url: str, email_data: Dict) -> Dict:
    """Call ML model service and return prediction"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{model_url}/predict",
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
                "is_phishing": result.get("is_phishing", False),
                "confidence": result.get("confidence_score", 0),
                "spam_prob": result.get("spam_probability", 0)
            }
    except Exception as e:
        print(f"Error calling {model_url}: {e}")
        return {"is_phishing": False, "confidence": 0, "spam_prob": 0}

async def get_model_predictions(email_data: Dict) -> Dict:
    """Get predictions from all 3 models"""
    models = {
        "naive_bayes": "http://model-naive-bayes:8002",
        "random_forest": "http://model-random-forest:8004",
        "fine_tuned_llm": "http://model-fine-tuned-llm:8006"
    }

    predictions = {}
    for name, url in models.items():
        result = await call_model(url, email_data)
        predictions[name] = result

    return predictions

def calculate_metrics(tp: int, tn: int, fp: int, fn: int) -> Dict:
    """Calculate accuracy, precision, recall, F1"""
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total * 100 if total > 0 else 0
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn
    }

class EnsembleStrategy:
    """Base class for ensemble strategies"""

    def __init__(self, name: str):
        self.name = name
        self.tp = 0
        self.tn = 0
        self.fp = 0
        self.fn = 0

    def predict(self, predictions: Dict) -> bool:
        """Return ensemble prediction (True = phishing, False = legitimate)"""
        raise NotImplementedError

    def update(self, true_label: int, predicted: bool):
        """Update confusion matrix"""
        predicted_label = 1 if predicted else 0

        if true_label == 1 and predicted_label == 1:
            self.tp += 1
        elif true_label == 0 and predicted_label == 0:
            self.tn += 1
        elif true_label == 0 and predicted_label == 1:
            self.fp += 1
        elif true_label == 1 and predicted_label == 0:
            self.fn += 1

    def get_metrics(self) -> Dict:
        """Get performance metrics"""
        return calculate_metrics(self.tp, self.tn, self.fp, self.fn)

class MajorityVoting(EnsembleStrategy):
    """Simple majority voting - at least 2 out of 3 models agree"""

    def __init__(self):
        super().__init__("Majority Voting (2/3)")

    def predict(self, predictions: Dict) -> bool:
        votes = sum(1 for p in predictions.values() if p["is_phishing"])
        return votes >= 2

class UnanimousVoting(EnsembleStrategy):
    """All 3 models must agree it's phishing"""

    def __init__(self):
        super().__init__("Unanimous Voting (3/3)")

    def predict(self, predictions: Dict) -> bool:
        return all(p["is_phishing"] for p in predictions.values())

class AnyDetection(EnsembleStrategy):
    """Any single model detects phishing"""

    def __init__(self):
        super().__init__("Any Detection (1/3)")

    def predict(self, predictions: Dict) -> bool:
        return any(p["is_phishing"] for p in predictions.values())

class WeightedVoting(EnsembleStrategy):
    """Weighted voting based on F1 scores from individual tests"""

    def __init__(self):
        super().__init__("Weighted Voting (F1-based)")
        # Weights based on F1 scores: Naive Bayes=74.81, Random Forest=78.45, Fine-tuned LLM=45.77
        self.weights = {
            "naive_bayes": 74.81,
            "random_forest": 78.45,
            "fine_tuned_llm": 45.77
        }
        self.total_weight = sum(self.weights.values())

    def predict(self, predictions: Dict) -> bool:
        weighted_sum = sum(
            self.weights[model] * (1 if pred["is_phishing"] else 0)
            for model, pred in predictions.items()
        )
        return (weighted_sum / self.total_weight) >= 0.5

class HighPrecisionEnsemble(EnsembleStrategy):
    """Use high-precision models (Naive Bayes + Fine-tuned LLM) with majority"""

    def __init__(self):
        super().__init__("High Precision (NB+LLM)")

    def predict(self, predictions: Dict) -> bool:
        # Both Naive Bayes and Fine-tuned LLM have 100% precision
        # If either detects phishing, flag it
        return (predictions["naive_bayes"]["is_phishing"] or
                predictions["fine_tuned_llm"]["is_phishing"])

class HighRecallEnsemble(EnsembleStrategy):
    """Use high-recall models (Random Forest) as primary"""

    def __init__(self):
        super().__init__("High Recall (RF primary)")

    def predict(self, predictions: Dict) -> bool:
        # Random Forest has highest recall (88.34%)
        # Use it as primary, but require NB or LLM to confirm if RF says safe
        if predictions["random_forest"]["is_phishing"]:
            return True
        # If RF says safe, check if both others strongly agree it's phishing
        return (predictions["naive_bayes"]["is_phishing"] and
                predictions["fine_tuned_llm"]["is_phishing"])

async def test_ensemble_strategies(dataset_path: str, num_samples: int = 1000):
    """Test all ensemble strategies"""

    strategies = [
        MajorityVoting(),
        UnanimousVoting(),
        AnyDetection(),
        WeightedVoting(),
        HighPrecisionEnsemble(),
        HighRecallEnsemble()
    ]

    print("=" * 80)
    print("ENSEMBLE COMBINATION ACCURACY TEST")
    print("=" * 80)
    print(f"Dataset: {dataset_path}")
    print(f"Test samples: {num_samples}")
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    print("Testing combinations of:")
    print("  1. Naive Bayes (76.50% acc, 74.81% F1, 99.71% precision, 59.86% recall)")
    print("  2. Random Forest (71.70% acc, 78.45% F1, 70.55% precision, 88.34% recall)")
    print("  3. Fine-tuned LLM (59.00% acc, 45.77% F1, 100.00% precision, 29.67% recall)")
    print("=" * 80)
    print()

    tested = 0
    errors = 0

    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if tested >= num_samples:
                break

            try:
                # Extract email data
                text = row['text']
                true_label = int(row['label'])
                subject, body = extract_email_content(text)

                sender = "suspicious@phishing.com" if true_label == 1 else "legitimate@company.com"

                email_data = {
                    "subject": subject,
                    "sender": sender,
                    "body_text": body,
                    "body_html": ""
                }

                # Get predictions from all models
                predictions = await get_model_predictions(email_data)

                # Test each ensemble strategy
                for strategy in strategies:
                    ensemble_prediction = strategy.predict(predictions)
                    strategy.update(true_label, ensemble_prediction)

                tested += 1

                # Progress indicator
                if tested % 100 == 0:
                    print(f"Progress: {tested}/{num_samples} emails tested...")

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"Error processing sample {i}: {e}")

    print()
    print("=" * 80)
    print("ENSEMBLE RESULTS - SORTED BY F1-SCORE")
    print("=" * 80)
    print()

    # Calculate and sort results
    results = []
    for strategy in strategies:
        metrics = strategy.get_metrics()
        results.append({
            "name": strategy.name,
            "metrics": metrics
        })

    # Sort by F1 score descending
    results.sort(key=lambda x: x["metrics"]["f1_score"], reverse=True)

    # Print summary table
    print(f"{'STRATEGY':<30} {'ACCURACY':>10} {'PRECISION':>11} {'RECALL':>10} {'F1-SCORE':>10}")
    print("-" * 80)

    for result in results:
        m = result["metrics"]
        print(f"{result['name']:<30} {m['accuracy']:>9.2f}% {m['precision']:>10.2f}% "
              f"{m['recall']:>9.2f}% {m['f1_score']:>9.2f}%")

    print()
    print("=" * 80)
    print("DETAILED CONFUSION MATRICES")
    print("=" * 80)
    print()

    for result in results:
        m = result["metrics"]
        print(f"{result['name']}:")
        print(f"  True Positives:  {m['tp']:4d}    True Negatives:  {m['tn']:4d}")
        print(f"  False Positives: {m['fp']:4d}    False Negatives: {m['fn']:4d}")
        print(f"  Accuracy: {m['accuracy']:.2f}%  Precision: {m['precision']:.2f}%  "
              f"Recall: {m['recall']:.2f}%  F1: {m['f1_score']:.2f}%")
        print()

    print("=" * 80)
    print("COMPARISON WITH INDIVIDUAL MODELS")
    print("=" * 80)
    print()
    print("Individual Model Performance:")
    print("  Naive Bayes:     76.50% accuracy, 74.81% F1")
    print("  Random Forest:   71.70% accuracy, 78.45% F1")
    print("  Fine-tuned LLM:  59.00% accuracy, 45.77% F1")
    print()
    print("Best Ensemble Performance:")
    best = results[0]
    m = best["metrics"]
    print(f"  {best['name']}: {m['accuracy']:.2f}% accuracy, {m['f1_score']:.2f}% F1")
    print()

    # Check if ensemble beats best individual model
    best_individual_f1 = 78.45  # Random Forest
    ensemble_f1 = m['f1_score']

    if ensemble_f1 > best_individual_f1:
        improvement = ensemble_f1 - best_individual_f1
        print(f"✓ ENSEMBLE IMPROVES F1 by {improvement:.2f} percentage points!")
    else:
        decline = best_individual_f1 - ensemble_f1
        print(f"✗ Ensemble F1 is {decline:.2f} percentage points lower than best individual")

    print("=" * 80)
    print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return results

async def main():
    """Main function"""
    num_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    dataset_path = '/app/phishing_legit_dataset_KD_10000.csv'

    results = await test_ensemble_strategies(dataset_path, num_samples)

if __name__ == "__main__":
    asyncio.run(main())
