#!/bin/bash
set -e

echo "🚀 Starting Ollama service..."

# Start Ollama in the background
ollama serve &
OLLAMA_PID=$!

echo "⏳ Waiting for Ollama to be ready..."
sleep 5

# Check if model is already pulled
MODEL="${OLLAMA_MODEL:-phi3}"
echo "📦 Checking if model '$MODEL' exists..."

if ollama list | grep -q "$MODEL"; then
    echo "✅ Model '$MODEL' already exists"
else
    echo "📥 Model '$MODEL' not found. Pulling now..."
    ollama pull "$MODEL"
    echo "✅ Model '$MODEL' pulled successfully"
fi

echo "✨ Ollama is ready with model '$MODEL'"

# Keep the container running
wait $OLLAMA_PID
