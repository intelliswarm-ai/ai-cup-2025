FROM python:3.11-slim

# Install curl and PostgreSQL client
RUN apt-get update && \
    apt-get install -y curl postgresql-client && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the fetch script
COPY fetch_emails.sh .
RUN chmod +x fetch_emails.sh

# Run the fetch script
CMD ["./fetch_emails.sh"]
