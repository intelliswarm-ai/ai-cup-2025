FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY src/ ./src/
COPY download_model.py .
COPY fetch_checkpoint.py .
COPY main.py .

# Create models directory
RUN mkdir -p models

# Download the model checkpoint if it doesn't exist
# This will run during container build
RUN python download_model.py || echo "Model download failed or will be attempted at runtime"

# Expose port
EXPOSE 8006

# Create an entrypoint script to ensure model is downloaded before starting
RUN echo '#!/bin/bash\n\
if [ ! -f "models/checkpoint.pt" ]; then\n\
  echo "Model checkpoint not found, attempting download..."\n\
  python download_model.py || echo "Warning: Model download failed"\n\
fi\n\
echo "Starting Fine-tuned LLM service..."\n\
exec uvicorn main:app --host 0.0.0.0 --port 8006\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
