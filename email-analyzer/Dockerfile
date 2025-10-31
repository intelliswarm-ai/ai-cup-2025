FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=1000 --retries=10 -r requirements.txt

# Copy analyzer script
COPY analyze_emails.py .
RUN chmod +x analyze_emails.py

# Run the analyzer
CMD ["python", "-u", "analyze_emails.py"]
