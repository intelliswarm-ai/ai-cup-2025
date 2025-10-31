# Quick Start: Enable OpenAI for Agentic Workflows

## ✅ What's Been Done
- ✅ OpenAI API integration added to agentic workflows
- ✅ Secure `.env` configuration file created (not committed to git)
- ✅ System configured to use **gpt-4o-mini** (fastest & cheapest model)
- ✅ Automatic fallback to local Ollama if no API key provided

## 🚀 To Enable Fast Agentic Discussions (30 seconds instead of 10 minutes!)

### 1. Get your OpenAI API key
- Go to: https://platform.openai.com/api-keys
- Create a new secret key
- Copy it (starts with `sk-...`)

### 2. Add your API key to `.env`
```bash
# Edit the .env file in the project root
nano .env
```

Replace this line:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

With your actual key:
```env
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

Save and exit (Ctrl+X, Y, Enter in nano)

### 3. Restart the backend
```bash
docker compose restart backend
```

### 4. Verify it's working
```bash
docker compose logs backend | grep "AgenticTeamOrchestrator"
```

Should show:
```
[AgenticTeamOrchestrator] Using OpenAI API with model: gpt-4o-mini
```

## 📊 Cost & Performance

| Metric | Local (Ollama) | OpenAI (gpt-4o-mini) |
|--------|---------------|---------------------|
| **Speed** | 5-10 minutes | 30-60 seconds |
| **Quality** | Moderate | High |
| **Cost** | Free | ~$0.002 per discussion |

**Estimated monthly cost** (100 discussions/day): ~$6/month

## 🧪 Test It

1. Visit: https://localhost/pages/agentic-teams.html?team=compliance
2. Click on any email
3. Watch the discussion complete in **30-60 seconds**! 🚀

## 🔒 Security Note
Your API key is stored in `.env` which is in `.gitignore` - it will never be committed to the repository.

## 📖 Full Documentation
See `OPENAI_SETUP.md` for detailed information, troubleshooting, and cost analysis.
