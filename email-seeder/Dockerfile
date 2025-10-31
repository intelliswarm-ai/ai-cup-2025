FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --timeout=1000 --retries=10 -r requirements.txt

# Copy scripts
COPY . .

# Run the seeding script
CMD ["python", "seed_emails.py"]
