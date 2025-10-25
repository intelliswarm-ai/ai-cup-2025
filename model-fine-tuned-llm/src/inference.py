import torch
from transformers import DistilBertTokenizer
import numpy as np
from typing import List, Dict, Union, Optional
import re

from model import DistilBertForPhishingDetection


class PhishingDetector:
    def __init__(self, checkpoint_path: str, device: Optional[torch.device] = None):
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device
            
        self.model = self._load_model(checkpoint_path)
        self.model.eval()
        
        self.tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
        self.max_length = 512
        
    def _load_model(self, checkpoint_path: str) -> DistilBertForPhishingDetection:
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        config = checkpoint['config']
        
        model = DistilBertForPhishingDetection(
            model_name=config['model_name'],
            num_labels=config['num_labels'],
            dropout_rate=config['dropout_rate']
        )
        
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        
        return model
    
    def clean_text(self, text: str) -> str:
        text = str(text).lower()
        text = re.sub(r'http\S+', ' [URL] ', text)
        text = re.sub(r'\S+@\S+', ' [EMAIL] ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def predict_single(self, email_text: str) -> Dict[str, Union[str, float, Dict[str, float]]]:
        cleaned_text = self.clean_text(email_text)
        
        encoding = self.tokenizer(
            cleaned_text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            
            probs = torch.softmax(outputs['logits'], dim=-1)
            prediction = torch.argmax(outputs['logits'], dim=-1)
        
        prediction_label = 'phishing' if prediction.item() == 1 else 'legitimate'
        confidence = probs[0, prediction.item()].item()
        
        return {
            'prediction': prediction_label,
            'confidence': confidence,
            'probabilities': {
                'legitimate': probs[0, 0].item(),
                'phishing': probs[0, 1].item()
            }
        }
    
    def predict_batch(self, email_texts: List[str]) -> List[Dict[str, Union[str, float, Dict[str, float]]]]:
        results = []
        
        for text in email_texts:
            result = self.predict_single(text)
            results.append(result)
        
        return results
    
    def get_risk_level(self, phishing_probability: float) -> str:
        if phishing_probability < 0.3:
            return "Low Risk"
        elif phishing_probability < 0.7:
            return "Medium Risk"
        else:
            return "High Risk"
    
    def analyze_email(self, email_text: str) -> Dict[str, Union[str, float, Dict[str, float]]]:
        result = self.predict_single(email_text)
        
        phishing_prob = result['probabilities']['phishing']
        risk_level = self.get_risk_level(phishing_prob)
        
        suspicious_patterns = []
        
        if re.search(r'http\S+', email_text.lower()):
            suspicious_patterns.append("Contains URLs")
        if re.search(r'urgent|immediate|act now|limited time', email_text.lower()):
            suspicious_patterns.append("Urgency indicators")
        if re.search(r'verify|confirm|update|suspend', email_text.lower()):
            suspicious_patterns.append("Action requests")
        if re.search(r'prize|winner|congratulations|lottery', email_text.lower()):
            suspicious_patterns.append("Prize/lottery mentions")
        if re.search(r'click here|click below', email_text.lower()):
            suspicious_patterns.append("Click requests")
        
        analysis = {
            **result,
            'risk_level': risk_level,
            'suspicious_patterns': suspicious_patterns,
            'recommendation': self._get_recommendation(phishing_prob, suspicious_patterns)
        }
        
        return analysis
    
    def _get_recommendation(self, phishing_prob: float, patterns: List[str]) -> str:
        if phishing_prob > 0.8:
            return "HIGH RISK: This email appears to be phishing. Do not click any links or provide personal information."
        elif phishing_prob > 0.5:
            return "CAUTION: This email shows signs of potential phishing. Verify the sender before taking any action."
        elif len(patterns) > 2:
            return "BE CAREFUL: While classified as legitimate, this email contains suspicious patterns. Verify authenticity."
        else:
            return "LIKELY SAFE: This email appears to be legitimate, but always exercise caution with unexpected emails."


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Phishing email detection inference')
    parser.add_argument('--checkpoint', type=str, required=True,
                       help='Path to model checkpoint')
    parser.add_argument('--email', type=str, 
                       help='Email text to analyze')
    parser.add_argument('--file', type=str,
                       help='Path to file containing email text')
    
    args = parser.parse_args()
    
    detector = PhishingDetector(args.checkpoint)
    
    if args.email:
        email_text = args.email
    elif args.file:
        with open(args.file, 'r') as f:
            email_text = f.read()
    else:
        print("Please provide either --email or --file argument")
        return
    
    print("\nAnalyzing email...")
    print("-" * 50)
    
    analysis = detector.analyze_email(email_text)
    
    print(f"\nPrediction: {analysis['prediction'].upper()}")
    print(f"Confidence: {analysis['confidence']:.2%}")
    print(f"Risk Level: {analysis['risk_level']}")
    print(f"\nProbabilities:")
    print(f"  - Legitimate: {analysis['probabilities']['legitimate']:.2%}")
    print(f"  - Phishing: {analysis['probabilities']['phishing']:.2%}")
    
    if analysis['suspicious_patterns']:
        print(f"\nSuspicious Patterns Detected:")
        for pattern in analysis['suspicious_patterns']:
            print(f"  - {pattern}")
    
    print(f"\nRecommendation: {analysis['recommendation']}")


if __name__ == "__main__":
    main()