"""
Logistic Regression Phishing Detection Service
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional
from load_model_compat import PickleCompatLoader
import numpy as np

app = FastAPI(title="Naive Bayes Phishing Detector")
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
        model_data = PickleCompatLoader.load("naive_bayes_model.pkl")
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
    return {"status": "healthy", "model": "Naive Bayes", "loaded": model is not None}

@app.post("/predict", response_model=PredictionResponse)
async def predict(email: EmailRequest):
    if model is None or tfidf_vectorizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        # Simple text preprocessing
        text = f"{email.subject} {email.body_text}".lower()
        
        # Transform with TF-IDF
        features = tfidf_vectorizer.transform([text]).toarray()

        # Naive Bayes was trained with ONLY TF-IDF features (5000), no manual features
        # So we use features directly without adding manual features
        X = features
        
        # Get prediction
        prediction = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]
        confidence = abs(probabilities[1] - probabilities[0]) * 100
        
        return PredictionResponse(
            is_phishing=bool(prediction == 1),
            confidence_score=float(confidence),
            spam_probability=float(probabilities[1] * 100),
            ham_probability=float(probabilities[0] * 100),
            model_name="Naive Bayes"
        )
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/")
async def root():
    return {"service": "Naive Bayes Phishing Detector", "status": "running"}
