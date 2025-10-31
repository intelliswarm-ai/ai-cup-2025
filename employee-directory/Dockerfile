FROM python:3.11-slim

# Install curl for health checks and API calls
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=1000 --retries=10 -r requirements.txt

COPY . .

# Make scripts executable
RUN chmod +x /app/entrypoint.sh /app/init_employees.sh /app/generate_employees_from_db.py

EXPOSE 8100

ENTRYPOINT ["/app/entrypoint.sh"]
