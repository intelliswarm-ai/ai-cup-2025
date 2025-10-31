#!/usr/bin/env bash
# Pull TinyLlama model to Ollama

echo "📥 Pulling TinyLlama model to Ollama..."
echo "This may take 2-3 minutes (about 600MB download)"

docker exec mailbox-ollama ollama pull tinyllama

echo "✅ TinyLlama model ready!"
echo ""
echo "You can now:"
echo "  1. Process emails with LLM"
echo "  2. View daily summaries"
echo "  3. Extract call-to-actions"
