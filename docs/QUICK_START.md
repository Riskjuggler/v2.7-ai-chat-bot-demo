# Quick Start Guide

Get the AI Chat Web Interface running in under 5 minutes!

## Prerequisites Check

Before starting, ensure you have:

- [ ] Python 3.9 or higher: `python3 --version`
- [ ] Node.js 18 or higher: `node --version`
- [ ] Git: `git --version`
- [ ] At least one LLM provider configured (see Step 2)

## 5-Minute Setup

### Step 1: Clone and Navigate (30 seconds)

```bash
git clone <repository-url>
cd v2.7-test
```

### Step 2: Configure LLM Provider (2 minutes)

Choose ONE of these options:

#### Option A: OpenAI (Recommended for beginners)

```bash
cp .env.example .env
# Edit .env and add:
OPENAI_API_KEY=sk-your-api-key-here
```

Get your API key: https://platform.openai.com/api-keys

#### Option B: Anthropic (Claude)

```bash
cp .env.example .env
# Edit .env and add:
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

Get your API key: https://console.anthropic.com/

#### Option C: LM Studio (Local, No API Key Needed)

1. Download and install LM Studio: https://lmstudio.ai/
2. Open LM Studio and load any model (e.g., "Llama 2 7B")
3. Start the local server (Server tab → Start Server)
4. Configure:
   ```bash
   cp .env.example .env
   # Edit .env and add:
   LMSTUDIO_BASE_URL=http://localhost:1234/v1
   LLM_CALLER_PREFER_LOCAL=true
   ```

### Step 3: Install Dependencies (1.5 minutes)

#### Backend:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend:
```bash
cd frontend
npm install
cd ..
```

### Step 4: Start the Application (30 seconds)

#### On Unix/Mac:
```bash
chmod +x scripts/*.sh
./scripts/start-all.sh
```

#### On Windows:
```bash
scripts\start-all.bat
```

This starts both backend (port 8000) and frontend (port 3000) concurrently.

### Step 5: Open and Test (30 seconds)

1. Open your browser to: http://localhost:3000
2. Type a test message: "Hello, what can you help me with?"
3. Press Enter or click Send
4. You should see an AI response within a few seconds!

## Verification Checklist

Confirm everything is working:

- [ ] Backend running: Visit http://localhost:8000/health (should show "healthy")
- [ ] API docs accessible: http://localhost:8000/docs (shows interactive API documentation)
- [ ] Frontend loaded: http://localhost:3000 (shows chat interface)
- [ ] Chat works: Send a message and receive a response
- [ ] No console errors: Check browser developer console (F12)

## Quick Troubleshooting

### "ModuleNotFoundError" when starting backend

**Problem**: Python dependencies not installed or virtualenv not activated

**Solution**:
```bash
source venv/bin/activate  # Activate virtualenv
pip install -r requirements.txt  # Reinstall dependencies
```

### "Cannot find module" when starting frontend

**Problem**: Node.js dependencies not installed

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
```

### "401 Unauthorized" or "API key not found"

**Problem**: `.env` file missing or API key not configured

**Solution**:
```bash
# Ensure .env exists
ls -la .env

# Verify it contains your API key
cat .env | grep API_KEY

# If missing, copy from example and edit
cp .env.example .env
# Then edit .env with your API key
```

### Backend starts but no response from LLM

**Problem**: Invalid API key or provider not reachable

**Solution**:
```bash
# Test your configuration
python llm_cli.py config --validate

# Test a simple chat
python llm_cli.py chat "Hello"
```

### Port already in use (8000 or 3000)

**Problem**: Another application is using the port

**Solution**:
```bash
# Find what's using the port (Unix/Mac)
lsof -i :8000
lsof -i :3000

# Kill the process or start on different port
uvicorn src.api.main:app --port 8001  # Different port for backend
```

### LM Studio: "Connection refused"

**Problem**: LM Studio server not running

**Solution**:
1. Open LM Studio
2. Go to "Local Server" tab (or "Server" tab)
3. Click "Start Server"
4. Verify it says "Server running on http://localhost:1234"
5. Test: `curl http://localhost:1234/v1/models`

## Next Steps

Now that you're up and running:

1. **Explore the API**: Visit http://localhost:8000/docs for interactive API documentation
2. **Read Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design
3. **Run Tests**: Try `pytest tests/ -v` to run the test suite
4. **Customize**: Modify the frontend or add new features

## Advanced: Manual Startup (Alternative to Scripts)

If you prefer to start services manually:

**Terminal 1 (Backend)**:
```bash
source venv/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Frontend)**:
```bash
cd frontend
npm run dev
```

## Time Breakdown

- Clone and navigate: 30 seconds
- Configure provider: 2 minutes (first time), 30 seconds (after)
- Install dependencies: 1.5 minutes (first time), skipped (after)
- Start application: 30 seconds
- Verify and test: 30 seconds

**Total first run**: 5 minutes
**Total subsequent runs**: 1.5 minutes

## Example First Message

Try these to test your setup:

- **General**: "Hello, what can you help me with?"
- **Code**: "Write a Python function to calculate Fibonacci numbers"
- **Creative**: "Write a haiku about programming"
- **Analysis**: "Explain how async/await works in JavaScript"

## Support

If you encounter issues not covered here:

1. Check the main [README.md](../README.md) troubleshooting section
2. Review [TESTING.md](TESTING.md) for test-related issues
3. See [INTEGRATION.md](INTEGRATION.md) for integration problems
4. Open an issue on GitHub

---

**Happy chatting!** You're now ready to use the AI Chat Web Interface.
