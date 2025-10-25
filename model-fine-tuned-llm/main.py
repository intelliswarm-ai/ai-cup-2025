"""
Fine-tuned LLM (DistilBERT) Phishing Detection Service
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional
import torch
from pathlib import Path
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from inference import PhishingDetector

app = FastAPI(title="Fine-tuned LLM Phishing Detector")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

detector = None
CHECKPOINT_PATH = Path("models/checkpoint.pt")

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
    global detector
    try:
        logger.info("Loading Fine-tuned DistilBERT model...")

        if not CHECKPOINT_PATH.exists():
            logger.error(f"Model checkpoint not found at {CHECKPOINT_PATH}")
            logger.error("Please ensure the model checkpoint is downloaded.")
            raise FileNotFoundError(f"Model checkpoint not found at {CHECKPOINT_PATH}")

        # Initialize the PhishingDetector with the checkpoint
        detector = PhishingDetector(
            checkpoint_path=str(CHECKPOINT_PATH),
            device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        )

        logger.info("✓ Fine-tuned LLM model loaded successfully!")
        logger.info(f"  Using device: {detector.device}")

    except Exception as e:
        logger.error(f"✗ Error loading model: {e}")
        raise

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if detector is not None else "unhealthy",
        "model": "Fine-tuned DistilBERT",
        "loaded": detector is not None,
        "checkpoint": str(CHECKPOINT_PATH),
        "checkpoint_exists": CHECKPOINT_PATH.exists()
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(email: EmailRequest):
    if detector is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Combine email parts for analysis
        email_text = f"Subject: {email.subject}\n\n{email.body_text}"

        # Use the PhishingDetector's predict_single method
        result = detector.predict_single(email_text)

        # Extract probabilities
        phishing_prob = result['probabilities']['phishing']
        legitimate_prob = result['probabilities']['legitimate']

        # Determine if phishing (using threshold of 0.5)
        is_phishing = result['prediction'] == 'phishing'

        # Convert confidence to percentage (0-100)
        # Confidence is based on how certain the model is
        confidence = result['confidence'] * 100

        return PredictionResponse(
            is_phishing=is_phishing,
            confidence_score=float(confidence),
            spam_probability=float(phishing_prob * 100),
            ham_probability=float(legitimate_prob * 100),
            model_name="Fine-tuned DistilBERT"
        )

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/")
async def root():
    return {
        "service": "Fine-tuned LLM Phishing Detector",
        "model": "DistilBERT fine-tuned on phishing dataset",
        "status": "running"
    }
