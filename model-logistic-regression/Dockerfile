FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=1000 --retries=10 -r requirements.txt

# Copy model files
COPY logistic_regression_model.pkl .
COPY preprocessing.py .
COPY load_model_compat.py .
COPY main.py .
COPY test_accuracy.py .
COPY data/ ./data/

# Expose port
EXPOSE 8001

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
