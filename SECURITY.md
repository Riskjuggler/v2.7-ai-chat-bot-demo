# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of AI Chat Web Interface seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via:
- Opening a GitHub Security Advisory at https://github.com/YOUR_USERNAME/v2.7-ai-chat-bot-demo/security/advisories/new
- Or by sending an email to (security contact email)

Please include the following information in your report:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

This information will help us triage your report more quickly.

## Response Timeline

- **Initial Response**: We aim to respond within 48 hours
- **Status Update**: We will send a status update within 7 days
- **Resolution**: We aim to resolve critical issues within 30 days

## Disclosure Policy

- Report the vulnerability privately
- Give us reasonable time to fix the issue before public disclosure
- We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices for Users

When deploying this application:

1. **Use environment variables** for all API keys and secrets
2. **Never commit** `.env` files or credentials to version control
3. **Keep dependencies updated** - run `pip install -U -r requirements.txt` and `npm update` regularly
4. **Enable CORS restrictions** appropriate for your deployment
5. **Use HTTPS** in production environments
6. **Implement rate limiting** if exposing the API publicly
7. **Review security audit** in SECURITY_AUDIT.md before deployment
8. **Monitor logs** for suspicious activity
9. **Use strong authentication** if exposing beyond localhost
10. **Keep Python and Node.js updated** to latest stable versions

## Known Security Features

This application includes:

- **Localhost-only middleware** (default configuration)
- **CORS protection** with strict origin validation
- **Input validation** using Pydantic schemas
- **No credentials in code** (environment variable based)
- **Dependency scanning** (optional, via `pip-audit` and `npm audit`)
- **Security headers** (configured in middleware)

## Security Audits

See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for the complete security audit results.

## Comments on this Policy

If you have suggestions on how this process could be improved, please submit a pull request.

---

**Last Updated**: 2025-11-09
