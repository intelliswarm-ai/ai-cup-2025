#!/usr/bin/env python3
"""
Test accuracy of Fine-tuned LLM (DistilBERT) model against Kaggle phishing dataset
"""

import csv
import sys
import re
import requests
import json
from typing import Tuple
from datetime import datetime

API_URL = "http://localhost:8006/predict"

def extract_email_content(text: str) -> Tuple[str, str]:
    """Extract subject and body from email text"""
    # Try to extract subject
    subject_match = re.match(r'Subject:\s*(.+?)\n\n', text, re.DOTALL)
    if subject_match:
        subject = subject_match.group(1).strip()
        body = text[subject_match.end():].strip()
    else:
        subject = ""
        body = text

    return subject, body

def predict_phishing(subject: str, body: str, sender: str) -> Tuple[bool, float]:
    """Call the Fine-tuned LLM API to predict if email is phishing"""
    try:
        payload = {
            "subject": subject,
            "sender": sender,
            "body_text": body
        }

        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        is_phishing = result.get('is_phishing', False)
        confidence = result.get('confidence_score', 0.0)

        return is_phishing, confidence

    except Exception as e:
        print(f"API Error: {e}")
        # Return False and 0 confidence on error
        return False, 0.0

def test_model(dataset_path: str, num_samples: int = 1000):
    """Test model accuracy on dataset"""
    print("=" * 70)
    print("FINE-TUNED LLM (DistilBERT) MODEL - ACCURACY TEST")
    print("=" * 70)
    print(f"Dataset: {dataset_path}")
    print(f"Test samples: {num_samples}")
    print(f"API URL: {API_URL}")
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)

    # Test API connectivity first
    try:
        test_response = requests.get("http://localhost:8006/health", timeout=5)
        if test_response.status_code != 200:
            print("ERROR: Fine-tuned LLM API is not responding correctly!")
            print("Please ensure the model container is running on port 8006")
            sys.exit(1)
        print("✓ API connectivity confirmed")
        print("-" * 70)
    except Exception as e:
        print(f"ERROR: Cannot connect to Fine-tuned LLM API: {e}")
        print("Please ensure the model container is running on port 8006")
        sys.exit(1)

    true_positives = 0  # Correctly identified phishing
    true_negatives = 0  # Correctly identified legitimate
    false_positives = 0  # Legitimate marked as phishing
    false_negatives = 0  # Phishing marked as legitimate

    tested = 0
    errors = 0

    total_confidence = 0.0

    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if tested >= num_samples:
                break

            try:
                # Extract email data
                text = row['text']
                true_label = int(row['label'])  # 1 = phishing, 0 = legitimate
                phishing_type = row['phishing_type']

                subject, body = extract_email_content(text)

                # Generate a sender based on phishing type (similar to seeder logic)
                if true_label == 1:
                    sender = "suspicious@phishing.com"
                else:
                    sender = "legitimate@company.com"

                # Make prediction via API
                is_phishing, confidence = predict_phishing(subject, body, sender)
                predicted_label = 1 if is_phishing else 0

                total_confidence += confidence

                # Update confusion matrix
                if true_label == 1 and predicted_label == 1:
                    true_positives += 1
                elif true_label == 0 and predicted_label == 0:
                    true_negatives += 1
                elif true_label == 0 and predicted_label == 1:
                    false_positives += 1
                elif true_label == 1 and predicted_label == 0:
                    false_negatives += 1

                tested += 1

                # Progress indicator
                if tested % 100 == 0:
                    accuracy = (true_positives + true_negatives) / tested * 100
                    avg_conf = total_confidence / tested
                    print(f"Tested: {tested}/{num_samples} | Accuracy: {accuracy:.2f}% | Avg Confidence: {avg_conf:.2f}%")

            except Exception as e:
                errors += 1
                if errors <= 5:  # Only print first 5 errors
                    print(f"Error processing sample {i}: {e}")

    # Calculate metrics
    total = tested
    accuracy = (true_positives + true_negatives) / total * 100 if total > 0 else 0
    avg_confidence = total_confidence / total if total > 0 else 0

    # Precision: Of all predicted phishing, how many were actually phishing?
    precision = true_positives / (true_positives + false_positives) * 100 if (true_positives + false_positives) > 0 else 0

    # Recall: Of all actual phishing, how many did we catch?
    recall = true_positives / (true_positives + false_negatives) * 100 if (true_positives + false_negatives) > 0 else 0

    # F1-Score: Harmonic mean of precision and recall
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Print results
    print("=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print(f"Total emails tested: {total}")
    print(f"Errors encountered: {errors}")
    print(f"Average confidence: {avg_confidence:.2f}%")
    print("-" * 70)
    print("CONFUSION MATRIX:")
    print(f"  True Positives (Phishing → Phishing):     {true_positives:4d}")
    print(f"  True Negatives (Legitimate → Legitimate): {true_negatives:4d}")
    print(f"  False Positives (Legitimate → Phishing):  {false_positives:4d}")
    print(f"  False Negatives (Phishing → Legitimate):  {false_negatives:4d}")
    print("-" * 70)
    print("PERFORMANCE METRICS:")
    print(f"  Accuracy:  {accuracy:6.2f}%")
    print(f"  Precision: {precision:6.2f}%")
    print(f"  Recall:    {recall:6.2f}%")
    print(f"  F1-Score:  {f1_score:6.2f}%")
    print("=" * 70)
    print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Save results to file
    with open('accuracy_results.txt', 'w') as f:
        f.write("FINE-TUNED LLM (DistilBERT) MODEL - ACCURACY TEST RESULTS\n")
        f.write("=" * 70 + "\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Dataset: {dataset_path}\n")
        f.write(f"Samples Tested: {total}\n")
        f.write(f"Errors: {errors}\n")
        f.write(f"Average Confidence: {avg_confidence:.2f}%\n")
        f.write("\nConfusion Matrix:\n")
        f.write(f"  True Positives:  {true_positives}\n")
        f.write(f"  True Negatives:  {true_negatives}\n")
        f.write(f"  False Positives: {false_positives}\n")
        f.write(f"  False Negatives: {false_negatives}\n")
        f.write("\nPerformance Metrics:\n")
        f.write(f"  Accuracy:  {accuracy:.2f}%\n")
        f.write(f"  Precision: {precision:.2f}%\n")
        f.write(f"  Recall:    {recall:.2f}%\n")
        f.write(f"  F1-Score:  {f1_score:.2f}%\n")

    print("\nResults saved to: accuracy_results.txt")

    # Return results for programmatic use
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'confusion_matrix': {
            'tp': true_positives,
            'tn': true_negatives,
            'fp': false_positives,
            'fn': false_negatives
        }
    }

if __name__ == "__main__":
    # Test with 1000 samples by default, or custom amount from command line
    num_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    test_model('data/phishing_legit_dataset_KD_10000.csv', num_samples)
