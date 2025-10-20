"""
Logistic Regression Phishing Detection Service
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional
from load_model_compat import PickleCompatLoader
import numpy as np

app = FastAPI(title="Neural Network Phishing Detector")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = None
tfidf_vectorizer = None
scaler = None

class EmailRequest(BaseModel):
    subject: str
    sender: str
    body_text: str
    body_html: Optional[str] = None

class PredictionResponse(BaseModel):
    is_phishing: bool
    confidence_score: float
    spam_probability: float
    ham_probability: float
    model_name: str

@app.on_event("startup")
async def load_model():
    global model, tfidf_vectorizer, scaler
    try:
        logger.info("Loading Logistic Regression model...")
        model_data = PickleCompatLoader.load("neural_network_model.pkl")
        model = model_data['model']
        preprocessor = model_data['preprocessor']
        # Extract sklearn components from preprocessor
        tfidf_vectorizer = preprocessor.tfidf_vectorizer
        scaler = model_data.get('scaler', preprocessor.scaler if hasattr(preprocessor, 'scaler') else None)
        logger.info("Model loaded successfully!")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "Neural Network", "loaded": model is not None}

@app.post("/predict", response_model=PredictionResponse)
async def predict(email: EmailRequest):
    if model is None or tfidf_vectorizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        # Simple text preprocessing
        text = f"{email.subject} {email.body_text}".lower()
        
        # Transform with TF-IDF
        features = tfidf_vectorizer.transform([text]).toarray()
        
        # Add basic manual features (15 features to match training)
        manual_features = np.array([
            len(email.body_text),  # content_length
            len(email.subject),     # subject_length
            len(text.split()),      # word_count
            text.count('!'),        # exclamation_count
            text.count('?'),        # question_count
            sum(1 for c in text if c.isupper()) / max(len(text), 1),  # uppercase_ratio
            text.count('http://') + text.count('https://'),  # url_count
            int('bit.ly' in text or 'tinyurl' in text),  # short_url_count
            text.count('$') + text.count('£'),  # money_symbols
            text.count('%'),        # percentage_symbols
            sum(1 for word in ['urgent', 'immediate', 'expire', 'suspend'] if word in text),  # urgent_words
            sum(1 for word in ['winner', 'prize', 'lottery'] if word in text),  # winner_words
            sum(1 for word in ['verify', 'confirm', 'update', 'click here'] if word in text),  # verify_words
            int(any(c.isdigit() for c in email.sender)),  # sender_has_numbers
            0  # sender_domain_suspicious
        ])

        # Combine features first (TF-IDF + manual)
        X = np.concatenate([features[0], manual_features]).reshape(1, -1)

        # Scale the combined features
        if scaler is not None:
            X = scaler.transform(X)
        
        # Get prediction
        prediction = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]
        confidence = abs(probabilities[1] - probabilities[0]) * 100
        
        return PredictionResponse(
            is_phishing=bool(prediction == 1),
            confidence_score=float(confidence),
            spam_probability=float(probabilities[1] * 100),
            ham_probability=float(probabilities[0] * 100),
            model_name="Neural Network"
        )
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/")
async def root():
    return {"service": "Neural Network Phishing Detector", "status": "running"}
