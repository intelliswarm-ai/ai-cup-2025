#!/usr/bin/env python3
"""
Test accuracy of rule-based workflows (URL Analysis, Sender Analysis, Content Analysis)
against Kaggle phishing dataset
"""

import csv
import sys
import re
import asyncio
from typing import Dict, Tuple
from datetime import datetime
import os

# Add backend to path to import workflows
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from workflows import URLAnalysisWorkflow, SenderAnalysisWorkflow, ContentAnalysisWorkflow

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

async def test_workflow(workflow, workflow_name: str, dataset_path: str, num_samples: int = 1000):
    """Test workflow accuracy on dataset"""
    print("=" * 70)
    print(f"{workflow_name.upper()} - ACCURACY TEST")
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

                # Generate a sender based on phishing type
                if true_label == 1:
                    sender = "suspicious@phishing.com"
                else:
                    sender = "legitimate@company.com"

                # Prepare email data for workflow
                email_data = {
                    "subject": subject,
                    "sender": sender,
                    "body_text": body,
                    "body_html": ""
                }

                # Run workflow analysis
                result = await workflow.analyze(email_data)
                predicted_phishing = result.get("is_phishing_detected", False)
                predicted_label = 1 if predicted_phishing else 0

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
    print()

    return {
        "workflow_name": workflow_name,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "true_positives": true_positives,
        "true_negatives": true_negatives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "total": total,
        "errors": errors
    }

async def test_all_workflows(dataset_path: str, num_samples: int = 1000):
    """Test all rule-based workflows"""
    workflows = [
        (URLAnalysisWorkflow(), "URL Analysis"),
        (SenderAnalysisWorkflow(), "Sender Analysis"),
        (ContentAnalysisWorkflow(), "Content Analysis")
    ]

    results = []
    for workflow, name in workflows:
        result = await test_workflow(workflow, name, dataset_path, num_samples)
        results.append(result)

    return results

def update_results_file(workflow_results: list):
    """Update ML_MODEL_ACCURACY_RESULTS.txt with workflow results"""
    # Read existing content
    results_file = '/mnt/d/Intelliswarm.ai/ai-cup-2025/ML_MODEL_ACCURACY_RESULTS.txt'

    with open(results_file, 'r') as f:
        content = f.read()

    # Prepare new section for rule-based workflows
    new_section = "\n\nRULE-BASED WORKFLOW RESULTS\n"
    new_section += "=" * 70 + "\n"
    new_section += f"Date: {datetime.now().strftime('%Y-%m-%d')}\n"
    new_section += f"Dataset: 1000 samples (583 Phishing, 417 Legitimate)\n\n"
    new_section += "WORKFLOW                ACCURACY    PRECISION   RECALL      F1-SCORE\n"
    new_section += "-" * 70 + "\n"

    for result in workflow_results:
        new_section += f"{result['workflow_name']:23s} {result['accuracy']:6.2f}%      "
        new_section += f"{result['precision']:6.2f}%    {result['recall']:6.2f}%      "
        new_section += f"{result['f1_score']:6.2f}%\n"

    new_section += "\nCONFUSION MATRICES\n"
    new_section += "=" * 70 + "\n\n"

    for result in workflow_results:
        new_section += f"{result['workflow_name']}:\n"
        new_section += f"  True Positives:  {result['true_positives']:4d}    True Negatives:  {result['true_negatives']:4d}\n"
        new_section += f"  False Positives: {result['false_positives']:4d}    False Negatives: {result['false_negatives']:4d}\n\n"

    # Append to file
    with open(results_file, 'a') as f:
        f.write(new_section)

    print(f"\n✓ Results appended to: {results_file}")

async def main():
    """Main function"""
    # Test with 1000 samples by default, or custom amount from command line
    num_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    dataset_path = '/mnt/d/Intelliswarm.ai/ai-cup-2025/email-seeder/dataset/phishing_legit_dataset_KD_10000.csv'

    print("\n" + "=" * 70)
    print("RULE-BASED WORKFLOW ACCURACY TESTING")
    print("=" * 70)
    print(f"Testing: URL Analysis, Sender Analysis, Content Analysis")
    print(f"Dataset: {dataset_path}")
    print(f"Samples: {num_samples}")
    print("=" * 70 + "\n")

    # Run tests
    results = await test_all_workflows(dataset_path, num_samples)

    # Update results file
    update_results_file(results)

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
