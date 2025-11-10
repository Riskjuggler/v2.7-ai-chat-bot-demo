# Contributing to AI Chat Web Interface

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, Node version)
- **Relevant logs** or error messages
- **Screenshots** if applicable

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Clear use case** for the enhancement
- **Detailed description** of the proposed functionality
- **Examples** of how it would work
- **Alternative solutions** you've considered

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the development setup** in README.md
3. **Write tests** for any new functionality
4. **Ensure all tests pass** before submitting
5. **Follow code style** guidelines (Black for Python, ESLint for TypeScript)
6. **Update documentation** as needed
7. **Write clear commit messages**

## Development Process

### Setting Up Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ai-chat-interface.git
cd ai-chat-interface

# Set up backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Set up frontend
cd frontend
npm install
cd ..

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code following project conventions
   - Add/update tests
   - Update documentation

3. **Test your changes**:
   ```bash
   # Backend tests
   pytest tests/ -v --cov=src

   # Frontend tests
   cd frontend && npm test && cd ..

   # E2E tests
   pytest e2e/ -v

   # Linting
   ruff check src/ tests/
   black src/ tests/
   cd frontend && npm run lint && cd ..
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** on GitHub

### Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, no logic changes)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add streaming support for chat responses
fix: resolve CORS error on production deployment
docs: update API documentation with new endpoints
test: add integration tests for LM Studio provider
```

## Code Style Guidelines

### Python

- **Formatter**: [Black](https://black.readthedocs.io/) with default settings
- **Linter**: [Ruff](https://github.com/astral-sh/ruff)
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Use Google-style docstrings for public functions
- **Line length**: 88 characters (Black default)

Example:
```python
def process_chat_message(message: str, model: str = "gpt-4") -> ChatResponse:
    """Process a chat message and return AI response.

    Args:
        message: The user's chat message
        model: The model to use for completion

    Returns:
        ChatResponse object with AI reply

    Raises:
        ValueError: If message is empty
    """
    # Implementation
```

### TypeScript/React

- **Linter**: ESLint with React plugin
- **Formatter**: Prettier
- **Naming**: PascalCase for components, camelCase for functions
- **Hooks**: Follow [Rules of Hooks](https://react.dev/warnings/invalid-hook-call-warning)
- **Props**: Use TypeScript interfaces for component props

Example:
```typescript
interface ChatMessageProps {
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ content, role, timestamp }) => {
  // Implementation
};
```

## Testing Guidelines

### Backend Testing

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test API endpoints and service interactions
- **Coverage target**: >90% for new code
- **Naming**: `test_<function_name>_<scenario>`

Example:
```python
def test_chat_endpoint_returns_valid_response():
    """Test that /chat endpoint returns properly formatted response."""
    # Arrange
    client = TestClient(app)
    payload = {"message": "Hello"}

    # Act
    response = client.post("/chat", json=payload)

    # Assert
    assert response.status_code == 200
    assert "content" in response.json()
```

### Frontend Testing

- **Component tests**: Test component rendering and interactions
- **Service tests**: Test API client functions
- **Coverage target**: >80% for new code
- **Use Testing Library**: Prefer user-centric queries

Example:
```typescript
describe('ChatMessage', () => {
  it('renders user message correctly', () => {
    render(<ChatMessage content="Hello" role="user" timestamp={new Date()} />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByTestId('user-message')).toHaveClass('user');
  });
});
```

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Document parameters, return types, and exceptions
- Include usage examples for complex functions

### README and Guides

- Update README.md for new features or configuration
- Add/update guides in `docs/` for significant changes
- Include screenshots for UI changes

## Project Structure Conventions

- **Backend**: Place new endpoints in `src/api/routes.py`
- **Services**: Add business logic to `src/api/service.py` or create new service modules
- **Models**: Define data models in `src/api/models.py`
- **Frontend components**: Place in `frontend/src/components/`
- **Frontend services**: Place in `frontend/src/services/`
- **Tests**: Mirror the structure of source files

## Review Process

All submissions require review before merging:

1. **Automated checks**: Tests and linting must pass
2. **Code review**: At least one maintainer review required
3. **Documentation**: Ensure docs are updated
4. **Testing**: Verify test coverage meets requirements

### What We Look For

- **Correctness**: Does the code work as intended?
- **Tests**: Are there adequate tests?
- **Style**: Does it follow project conventions?
- **Documentation**: Is it well-documented?
- **Performance**: Are there any performance concerns?
- **Security**: Any security implications?

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Chat**: Join our community (link TBD)
- **Issues**: Check existing issues or create a new one
- **Documentation**: Review the `docs/` directory

## Recognition

Contributors will be recognized in:
- README.md acknowledgments section
- Release notes for significant contributions
- GitHub contributors page

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to AI Chat Web Interface! 🎉
