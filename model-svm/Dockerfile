FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=1000 --retries=10 -r requirements.txt

COPY svm_model.pkl .
COPY preprocessing.py .
COPY load_model_compat.py .
COPY main.py .
COPY test_accuracy.py .
COPY data/ ./data/

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
