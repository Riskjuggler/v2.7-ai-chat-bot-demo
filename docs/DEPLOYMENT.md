# Deployment Guide

This guide covers deploying the AI Chat Web Interface for production use.

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Environment Setup](#environment-setup)
- [Production Configuration](#production-configuration)
- [Deployment Options](#deployment-options)
- [Monitoring and Maintenance](#monitoring-and-maintenance)

## Pre-Deployment Checklist

Before deploying to production, verify:

### Code Quality
- [ ] All tests pass (`pytest tests/ -v` and `cd frontend && npm test`)
- [ ] Test coverage meets targets (>90% backend, >80% frontend)
- [ ] No linting errors (`ruff check src/ tests/` and `cd frontend && npm run lint`)
- [ ] Code formatted (`black src/ tests/` and `cd frontend && npm run format`)
- [ ] No debug code or console.logs in production code

### Security
- [ ] `.env` file not committed to version control
- [ ] API keys are valid and have appropriate permissions
- [ ] Localhost-only middleware enabled (default)
- [ ] CORS origins configured for production URLs
- [ ] Dependencies scanned for vulnerabilities (`pip-audit` and `npm audit`)

### Configuration
- [ ] `.env.example` is up-to-date with all required variables
- [ ] Production API keys obtained and tested
- [ ] Rate limiting configured (if applicable)
- [ ] Logging configured for production
- [ ] Error tracking set up (Sentry, etc.)

### Documentation
- [ ] README.md is complete and accurate
- [ ] API documentation is up-to-date
- [ ] Architecture documentation reflects current state
- [ ] Troubleshooting guide covers common issues

### Testing
- [ ] Manual smoke test completed successfully
- [ ] E2E tests pass (`pytest e2e/ -v`)
- [ ] Load testing performed (if expecting high traffic)
- [ ] Verified with all configured LLM providers

## Environment Setup

### Production Environment Variables

Create a production `.env` file with these variables:

```bash
# Production LLM Provider Configuration
OPENAI_API_KEY=sk-prod-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-prod-your-anthropic-api-key
LMSTUDIO_BASE_URL=http://localhost:1234/v1

# Service Configuration
LLM_CALLER_HOST=0.0.0.0  # Or specific IP
LLM_CALLER_PORT=8000
LLM_CALLER_PREFER_LOCAL=false  # true for privacy-focused deployment

# Production Settings (if applicable)
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
ENVIRONMENT=production
```

### Backend Requirements

**Install production dependencies**:
```bash
pip install -r requirements.txt
```

**Optional production dependencies**:
```bash
# Gunicorn for production server
pip install gunicorn

# Redis for caching (if using)
pip install redis

# Monitoring
pip install prometheus-client
```

### Frontend Build

**Build for production**:
```bash
cd frontend
npm install
npm run build
cd ..
```

This creates an optimized build in `frontend/dist/`.

## Production Configuration

### Backend (FastAPI)

**Option 1: Uvicorn (Recommended for small-medium load)**

```bash
# Single worker
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Multiple workers
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Option 2: Gunicorn with Uvicorn workers (High load)**

```bash
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile /var/log/ai-chat/access.log \
  --error-logfile /var/log/ai-chat/error.log
```

### Frontend (React)

**Option 1: Static file server (Recommended)**

Serve the built files from `frontend/dist/` with a static file server:

```bash
# Using Python's http.server
cd frontend/dist && python3 -m http.server 3000

# Using serve (npm package)
npm install -g serve
serve -s frontend/dist -l 3000

# Using nginx (see Deployment Options)
```

**Option 2: Node.js server**

For development/testing only:
```bash
cd frontend && npm run dev
```

## Deployment Options

### Option 1: Traditional Server

**Prerequisites**:
- Linux server (Ubuntu 20.04+ recommended)
- Python 3.9+
- Node.js 18+
- Nginx (optional, for reverse proxy)

**Steps**:

1. **Clone repository**:
   ```bash
   git clone <repository-url>
   cd v2.7-test
   ```

2. **Setup backend**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with production credentials
   ```

3. **Build frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Configure systemd service** (backend):

   Create `/etc/systemd/system/ai-chat-api.service`:
   ```ini
   [Unit]
   Description=AI Chat API
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/ai-chat
   Environment="PATH=/opt/ai-chat/venv/bin"
   ExecStart=/opt/ai-chat/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start:
   ```bash
   sudo systemctl enable ai-chat-api
   sudo systemctl start ai-chat-api
   sudo systemctl status ai-chat-api
   ```

5. **Configure Nginx** (reverse proxy):

   Create `/etc/nginx/sites-available/ai-chat`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       # Frontend
       location / {
           root /opt/ai-chat/frontend/dist;
           try_files $uri $uri/ /index.html;
       }

       # API
       location /api/ {
           proxy_pass http://localhost:8000/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       # Health check
       location /health {
           proxy_pass http://localhost:8000/health;
       }
   }
   ```

   Enable and reload:
   ```bash
   sudo ln -s /etc/nginx/sites-available/ai-chat /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Option 2: Docker (Recommended for easy deployment)

**Dockerfile (backend)**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY llm_caller_cli/ llm_caller_cli/

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile (frontend)**:
```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped
```

**Deploy**:
```bash
docker-compose up -d
```

### Option 3: Cloud Platform (PaaS)

**AWS Elastic Beanstalk**, **Google App Engine**, or **Heroku**:

1. Build frontend: `cd frontend && npm run build`
2. Configure platform-specific deployment files
3. Set environment variables in platform dashboard
4. Deploy using platform CLI

**Example (Heroku)**:
```bash
# Install Heroku CLI
heroku login
heroku create ai-chat-app

# Set environment variables
heroku config:set OPENAI_API_KEY=sk-your-key

# Deploy
git push heroku main
```

## Monitoring and Maintenance

### Health Checks

**Backend health endpoint**:
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

**Monitor continuously**:
```bash
# Add to cron or monitoring service
*/5 * * * * curl -f http://localhost:8000/health || alert-me
```

### Logging

**Backend logs**:
```bash
# If using systemd
sudo journalctl -u ai-chat-api -f

# If using Docker
docker logs -f ai-chat-backend
```

**Log rotation** (systemd):
```bash
# Systemd handles log rotation automatically
# Configure in /etc/systemd/journald.conf
```

### Performance Monitoring

**Metrics to track**:
- Request latency (p50, p95, p99)
- Error rate
- LLM API call latency
- Memory usage
- CPU usage

**Tools**:
- Prometheus + Grafana
- New Relic
- DataDog
- AWS CloudWatch (if on AWS)

### Backup and Recovery

**What to backup**:
- `.env` file (store securely, not in version control)
- Configuration files
- Chat history database (if implemented)

**Recovery plan**:
1. Clone repository
2. Restore `.env` file
3. Install dependencies
4. Start services

### Updating

**Backend update**:
```bash
cd /opt/ai-chat
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
sudo systemctl restart ai-chat-api
```

**Frontend update**:
```bash
cd /opt/ai-chat/frontend
git pull origin main
npm install
npm run build
sudo systemctl reload nginx  # If using nginx
```

### Security Maintenance

**Regular tasks**:
- [ ] Update dependencies monthly: `pip install -U -r requirements.txt` and `npm update`
- [ ] Run security scans: `pip-audit` and `npm audit`
- [ ] Rotate API keys quarterly
- [ ] Review logs for suspicious activity
- [ ] Check for CVEs in dependencies

**Security checklist**:
```bash
# Backend security scan
pip-audit

# Frontend security scan
cd frontend && npm audit

# Fix vulnerabilities
pip-audit --fix
npm audit fix
```

## Troubleshooting Production Issues

### High latency

**Symptoms**: Slow API responses

**Diagnosis**:
```bash
# Check LLM provider latency
curl -w "@curl-format.txt" http://localhost:8000/chat

# Check system resources
htop
```

**Solutions**:
- Add caching layer (Redis)
- Increase worker count
- Optimize LLM parameters (lower max_tokens)
- Use faster models (gpt-3.5 vs gpt-4)

### Memory leaks

**Symptoms**: Increasing memory usage over time

**Diagnosis**:
```bash
# Monitor memory
ps aux | grep uvicorn
```

**Solutions**:
- Set worker restart threshold (Gunicorn: `--max-requests 1000`)
- Review code for circular references
- Add memory profiling (`memory_profiler`)

### API errors

**Symptoms**: 500/503 errors

**Diagnosis**:
```bash
# Check logs
sudo journalctl -u ai-chat-api --since "10 minutes ago"

# Test LLM providers
python llm_cli.py chat "test"
```

**Solutions**:
- Verify API keys are valid
- Check rate limits with providers
- Implement retry logic with exponential backoff
- Add circuit breaker pattern

## Production Checklist

Before going live:

- [ ] All tests pass
- [ ] Security scan complete (no critical vulnerabilities)
- [ ] Monitoring set up
- [ ] Logging configured
- [ ] Backup plan in place
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] API keys secured
- [ ] Health check endpoint accessible
- [ ] Error handling tested
- [ ] Load tested (if expecting traffic)
- [ ] Rollback plan documented
- [ ] On-call rotation established (if applicable)

## Support and Resources

For deployment issues:
- Review [README.md](../README.md) troubleshooting section
- Check [TESTING.md](TESTING.md) for test failures
- See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Open an issue on GitHub

---

**Document Version**: 1.0
**Last Updated**: 2025-11-09
