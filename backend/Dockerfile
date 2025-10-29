FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Java for Liquibase
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    wget \
    curl \
    openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install Liquibase
ENV LIQUIBASE_VERSION=4.25.0
RUN wget -q https://github.com/liquibase/liquibase/releases/download/v${LIQUIBASE_VERSION}/liquibase-${LIQUIBASE_VERSION}.tar.gz \
    && mkdir /liquibase \
    && tar -xzf liquibase-${LIQUIBASE_VERSION}.tar.gz -C /liquibase \
    && rm liquibase-${LIQUIBASE_VERSION}.tar.gz \
    && chmod +x /liquibase/liquibase

# Download PostgreSQL JDBC driver to liquibase directory
RUN wget -q https://jdbc.postgresql.org/download/postgresql-42.6.0.jar -O /liquibase/postgresql-42.6.0.jar

ENV PATH="/liquibase:${PATH}"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy startup script and ensure it's executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose port
EXPOSE 8000

# Run the application using bash (doesn't rely on execute bit from volume mount)
CMD ["bash", "/app/start.sh"]
