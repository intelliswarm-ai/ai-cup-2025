# OpenAI API Setup for Agentic Workflows

## Overview
The agentic team discussions now use OpenAI API for fast, high-quality responses. Only the agentic workflows use OpenAI - all other features continue to run locally.

## Model Selection
We're using **gpt-4o-mini** - OpenAI's fastest and most cost-effective model:
- ⚡ **Speed**: Responses in 1-3 seconds (vs 60-120s with local Ollama)
- 💰 **Cost**: ~$0.15 per million input tokens, $0.60 per million output tokens
- 📊 **Estimated cost per discussion**: ~$0.001-0.003 (less than 1 cent)

## Setup Instructions

### Step 1: Get Your OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

### Step 2: Add Your API Key
Edit the `.env` file in the project root:

```bash
# Open the .env file
nano .env  # or use your preferred editor
```

Replace `your_openai_api_key_here` with your actual API key:

```env
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini
```

### Step 3: Restart the Backend
```bash
docker compose restart backend
```

### Step 4: Verify Setup
Check the backend logs to confirm OpenAI is being used:
```bash
docker compose logs backend | grep "AgenticTeamOrchestrator"
```

You should see:
```
[AgenticTeamOrchestrator] Using OpenAI API with model: gpt-4o-mini
```

## Testing
1. Go to https://localhost/pages/agentic-teams.html?team=compliance
2. Click on any email
3. The team discussion should complete in **30-60 seconds** (much faster than before!)

## Cost Monitoring
Each 5-agent discussion uses approximately:
- Input tokens: ~500-800 tokens
- Output tokens: ~400-600 tokens
- **Cost per discussion**: $0.001-0.003

For 100 discussions per day: ~$0.10-0.30/day

## Alternative Models
If you want different speed/cost trade-offs, edit `.env`:

```env
# Faster, slightly more expensive
OPENAI_MODEL=gpt-4o

# Cheaper alternative (not recommended, lower quality)
OPENAI_MODEL=gpt-3.5-turbo
```

## Fallback to Local
If no API key is configured, the system automatically falls back to local Ollama (slower but free).

## Security
- The `.env` file is in `.gitignore` - your API key will never be committed
- Share `.env.example` with your team, not `.env`
- Never commit your actual API key to the repository

## Troubleshooting

### "Using Ollama" in logs
- Check that your API key is in `.env` and doesn't say `your_openai_api_key_here`
- Restart the backend after editing `.env`

### "Error calling OpenAI API: 401"
- Your API key is invalid or expired
- Get a new key from https://platform.openai.com/api-keys

### "Error calling OpenAI API: 429"
- You've hit rate limits or run out of credits
- Check your usage at https://platform.openai.com/usage
- Add credits to your account

## Next Steps
Once configured, all agentic team discussions will use OpenAI automatically. The discussions will be:
- ✅ **10-20x faster** (30-60s vs 5-10 minutes)
- ✅ **Higher quality** responses
- ✅ **More consistent** results
- 💰 **Very affordable** (~$0.001 per discussion)
