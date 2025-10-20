#!/usr/bin/env python3
"""
Test accuracy of Logistic Regression model against Kaggle phishing dataset
"""

import csv
import sys
import re
from typing import Dict, Tuple
from datetime import datetime
from load_model_compat import PickleCompatLoader
import numpy as np

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

def preprocess_email(subject: str, body: str, sender: str) -> np.ndarray:
    """Preprocess email for prediction"""
    text = f"{subject} {body}".lower()

    # Transform with TF-IDF
    features = tfidf_vectorizer.transform([text]).toarray()

    # Add basic manual features (15 features)
    manual_features = np.array([
        len(body),  # content_length
        len(subject),  # subject_length
        len(text.split()),  # word_count
        text.count('!'),  # exclamation_count
        text.count('?'),  # question_count
        sum(1 for c in text if c.isupper()) / max(len(text), 1),  # uppercase_ratio
        text.count('http://') + text.count('https://'),  # url_count
        int('bit.ly' in text or 'tinyurl' in text),  # short_url_count
        text.count('$') + text.count('£'),  # money_symbols
        text.count('%'),  # percentage_symbols
        sum(1 for word in ['urgent', 'immediate', 'expire', 'suspend'] if word in text),  # urgent_words
        sum(1 for word in ['winner', 'prize', 'lottery'] if word in text),  # winner_words
        sum(1 for word in ['verify', 'confirm', 'update', 'click here'] if word in text),  # verify_words
        int(any(c.isdigit() for c in sender)),  # sender_has_numbers
        0  # sender_domain_suspicious
    ])

    # Combine features first (TF-IDF + manual)
    X = np.concatenate([features[0], manual_features]).reshape(1, -1)

    # Scale the combined features
    if scaler is not None:
        X = scaler.transform(X)
    return X

def test_model(dataset_path: str, num_samples: int = 1000):
    """Test model accuracy on dataset"""
    print("=" * 70)
    print("LOGISTIC REGRESSION MODEL - ACCURACY TEST")
    print("=" * 70)
    print(f"Dataset: {dataset_path}")
    print(f"Test samples: {num_samples}")
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)

    true_positives = 0  # Correctly identified phishing
    true_negatives = 0  # Correctly identified legitimate
    false_positives = 0  # Legitimate marked as phishing
    false_negatives = 0  # Phishing marked as legitimate

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
                true_label = int(row['label'])  # 1 = phishing, 0 = legitimate
                phishing_type = row['phishing_type']

                subject, body = extract_email_content(text)

                # Generate a sender based on phishing type (similar to seeder logic)
                if true_label == 1:
                    sender = "suspicious@phishing.com"
                else:
                    sender = "legitimate@company.com"

                # Make prediction
                X = preprocess_email(subject, body, sender)
                prediction = model.predict(X)[0]
                predicted_label = int(prediction)

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
                    print(f"Tested: {tested}/{num_samples} | Accuracy so far: {accuracy:.2f}%")

            except Exception as e:
                errors += 1
                if errors <= 5:  # Only print first 5 errors
                    print(f"Error processing sample {i}: {e}")

    # Calculate metrics
    total = tested
    accuracy = (true_positives + true_negatives) / total * 100 if total > 0 else 0

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
        f.write("LOGISTIC REGRESSION MODEL - ACCURACY TEST RESULTS\n")
        f.write("=" * 70 + "\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Dataset: {dataset_path}\n")
        f.write(f"Samples Tested: {total}\n")
        f.write(f"Errors: {errors}\n")
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

if __name__ == "__main__":
    # Load model
    print("Loading model...")
    model_data = PickleCompatLoader.load("neural_network_model.pkl")
    model = model_data['model']
    preprocessor = model_data['preprocessor']
    tfidf_vectorizer = preprocessor.tfidf_vectorizer
    scaler = model_data.get('scaler', preprocessor.scaler if hasattr(preprocessor, 'scaler') else None)
    print("Model loaded successfully!\n")

    # Test with 1000 samples by default, or custom amount from command line
    num_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    test_model('data/phishing_legit_dataset_KD_10000.csv', num_samples)
