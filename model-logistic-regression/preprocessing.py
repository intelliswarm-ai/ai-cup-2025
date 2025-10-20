"""
Email preprocessing utilities for spam/phishing detection
Extracted from inbox-sentinel project
"""

import re
import string
from typing import Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler


class EmailPreprocessor:
    """Preprocess emails for ML models"""

    def __init__(self, max_features: int = 1000):
        self.max_features = max_features
        self.tfidf_vectorizer = TfidfVectorizer(max_features=max_features, stop_words='english')
        self.scaler = StandardScaler()
        self.is_fitted = False

    def clean_text(self, text: str) -> str:
        """Clean email text"""
        # Convert to lowercase
        text = text.lower()

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', ' URL ', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', ' EMAIL ', text)

        # Remove numbers
        text = re.sub(r'\d+', ' NUMBER ', text)

        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def extract_features(self, email_content: str, subject: str, sender: str) -> Dict[str, float]:
        """Extract manual features from email"""
        full_text = f"{subject} {email_content}"

        features = {
            # Length features
            'content_length': len(email_content),
            'subject_length': len(subject),
            'word_count': len(full_text.split()),

            # Character features
            'exclamation_count': full_text.count('!'),
            'question_count': full_text.count('?'),
            'uppercase_ratio': sum(1 for c in full_text if c.isupper()) / max(len(full_text), 1),

            # URL features
            'url_count': len(re.findall(r'http[s]?://', full_text)),
            'short_url_count': len(re.findall(r'(bit\.ly|tinyurl|short\.link)', full_text.lower())),

            # Suspicious patterns
            'money_symbols': len(re.findall(r'[$£€¥]', full_text)),
            'percentage_symbols': full_text.count('%'),

            # Keywords
            'urgent_words': len(re.findall(r'\b(urgent|immediate|act now|expire|suspend)\b', full_text.lower())),
            'winner_words': len(re.findall(r'\b(winner|congratulations|prize|lottery|selected)\b', full_text.lower())),
            'verify_words': len(re.findall(r'\b(verify|confirm|update|validate|click here)\b', full_text.lower())),

            # Sender features
            'sender_has_numbers': 1 if any(c.isdigit() for c in sender) else 0,
            'sender_domain_suspicious': 1 if re.search(r'\.(tk|ml|ga|cf)$', sender) else 0,
        }

        return features

    def transform(self, email_content: str, subject: str, sender: str) -> np.ndarray:
        """Transform email into feature vector"""
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before transform")

        # Clean text
        cleaned_text = self.clean_text(f"{subject} {email_content}")

        # TF-IDF features
        tfidf_features = self.tfidf_vectorizer.transform([cleaned_text]).toarray()[0]

        # Manual features
        manual_features_dict = self.extract_features(email_content, subject, sender)
        manual_features = np.array(list(manual_features_dict.values()))
        manual_features_scaled = self.scaler.transform([manual_features])[0]

        # Combined features
        combined_features = np.concatenate([tfidf_features, manual_features_scaled])

        return combined_features
