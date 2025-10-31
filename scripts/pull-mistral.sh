#!/usr/bin/env bash
# Pull Mistral model to Ollama

echo "📥 Pulling Mistral model to Ollama..."
echo "This may take 5-10 minutes (about 4GB download)"

docker exec mailbox-ollama ollama pull mistral

echo "✅ Mistral model ready!"
echo ""
echo "You can now:"
echo "  1. Process emails with LLM"
echo "  2. View daily summaries"
echo "  3. Extract call-to-actions"
