#!/usr/bin/env python
"""
LLM Caller CLI Wrapper for Subprocess Integration

This module provides a JSON-based CLI interface for the llm_caller_cli module,
designed to be called via subprocess from other modules in the project.

Architectural Compliance:
- Modules chain via subprocess calls (not direct imports)
- This CLI enables other modules to use llm_caller_cli without importing it
- JSON input/output for structured data exchange

Usage:
    python3 llm_call.py --request-json '{
        "provider": "lmstudio",
        "model": "deepseek-coder",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
        "max_tokens": 100
    }'

Exit Codes:
    0: Success
    1: Invalid JSON or missing arguments
    2: Provider/model not available
    3: LLM request failed
    4: Unexpected error
"""

import asyncio
import sys
import json
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from llm_caller_cli.src import LLMService, TaskType
from llm_caller_cli.src.providers.base_provider import ProviderError


# Configure logging (will be set up in main() based on --verbose flag)
# Default: Disabled (NullHandler - no output to stderr)
# Verbose mode: INFO level (request/response timing, error details)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())  # Default: no output


class CLIError(Exception):
    """Base class for CLI errors with exit codes."""
    exit_code = 4

class InvalidRequestError(CLIError):
    """Invalid JSON or missing required fields."""
    exit_code = 1

class ProviderUnavailableError(CLIError):
    """Provider or model not available."""
    exit_code = 2

class LLMRequestError(CLIError):
    """LLM request failed."""
    exit_code = 3


def validate_request(request: Dict[str, Any]) -> None:
    """Validate JSON request structure.

    Args:
        request: Parsed JSON request

    Raises:
        InvalidRequestError: If request is invalid
    """
    # Provider is optional (routing will select)
    # Model is optional (routing will select)
    # Messages or prompt is required for chat/completion

    operation = request.get('operation', 'chat')

    if operation == 'chat':
        if 'messages' not in request:
            raise InvalidRequestError("Missing 'messages' field for chat operation")
        if not isinstance(request['messages'], list):
            raise InvalidRequestError("'messages' must be a list")
        if len(request['messages']) == 0:
            raise InvalidRequestError("'messages' cannot be empty")

    elif operation == 'completion':
        if 'prompt' not in request:
            raise InvalidRequestError("Missing 'prompt' field for completion operation")

    elif operation == 'embedding':
        if 'texts' not in request:
            raise InvalidRequestError("Missing 'texts' field for embedding operation")
        if not isinstance(request['texts'], list):
            raise InvalidRequestError("'texts' must be a list")
    else:
        raise InvalidRequestError(f"Unknown operation: {operation}")


def build_llm_kwargs(request: Dict[str, Any]) -> Dict[str, Any]:
    """Build kwargs for LLMService methods from request.

    Args:
        request: Parsed JSON request

    Returns:
        Dictionary of kwargs for LLMService methods
    """
    kwargs = {}

    # Model selection
    if 'model' in request:
        kwargs['model'] = request['model']

    # Provider preference
    if 'provider' in request:
        # Note: LLMService doesn't have direct provider parameter,
        # but we can use prefer_local for lmstudio
        if request['provider'].lower() == 'lmstudio':
            kwargs['prefer_local'] = True

    # Task type for routing
    if 'task_type' in request:
        try:
            kwargs['task_type'] = TaskType(request['task_type'])
        except ValueError:
            logger.warning(f"Invalid task_type: {request['task_type']}, ignoring")

    # Generation parameters
    if 'temperature' in request:
        kwargs['temperature'] = float(request['temperature'])
    if 'max_tokens' in request:
        kwargs['max_tokens'] = int(request['max_tokens'])
    if 'top_p' in request:
        kwargs['top_p'] = float(request['top_p'])
    if 'frequency_penalty' in request:
        kwargs['frequency_penalty'] = float(request['frequency_penalty'])
    if 'presence_penalty' in request:
        kwargs['presence_penalty'] = float(request['presence_penalty'])

    return kwargs


async def handle_chat_request(service: LLMService, request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle chat completion request.

    Args:
        service: LLMService instance
        request: Parsed JSON request

    Returns:
        Response dictionary

    Raises:
        LLMRequestError: If request fails
    """
    messages = request['messages']
    kwargs = build_llm_kwargs(request)

    start_time = time.time()
    provider = request.get('provider', 'auto')
    model = request.get('model', 'auto')

    try:
        logger.info(f"Chat request: provider={provider}, model={model}, messages={len(messages)}")
        response = await service.chat_completion(messages, **kwargs)

        elapsed = time.time() - start_time
        logger.info(f"Chat completed in {elapsed:.2f}s")

        return response.model_dump() if hasattr(response, 'model_dump') else response.dict()
    except ProviderError as e:
        elapsed = time.time() - start_time
        logger.error(f"Chat failed after {elapsed:.2f}s: {e}")
        raise LLMRequestError(f"Chat completion failed: {e}")
    except Exception as e:
        elapsed = time.time() - start_time
        logger.exception(f"Unexpected error in chat completion after {elapsed:.2f}s")
        raise LLMRequestError(f"Chat completion failed: {e}")


async def handle_completion_request(service: LLMService, request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle text completion request.

    Args:
        service: LLMService instance
        request: Parsed JSON request

    Returns:
        Response dictionary

    Raises:
        LLMRequestError: If request fails
    """
    prompt = request['prompt']
    kwargs = build_llm_kwargs(request)

    start_time = time.time()
    provider = request.get('provider', 'auto')
    model = request.get('model', 'auto')

    try:
        logger.info(f"Completion request: provider={provider}, model={model}, prompt_len={len(prompt)}")
        response = await service.text_completion(prompt, **kwargs)

        elapsed = time.time() - start_time
        logger.info(f"Completion completed in {elapsed:.2f}s")

        return response.model_dump() if hasattr(response, 'model_dump') else response.dict()
    except ProviderError as e:
        elapsed = time.time() - start_time
        logger.error(f"Completion failed after {elapsed:.2f}s: {e}")
        raise LLMRequestError(f"Text completion failed: {e}")
    except Exception as e:
        elapsed = time.time() - start_time
        logger.exception(f"Unexpected error in text completion after {elapsed:.2f}s")
        raise LLMRequestError(f"Text completion failed: {e}")


async def handle_embedding_request(service: LLMService, request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle embedding request.

    Args:
        service: LLMService instance
        request: Parsed JSON request

    Returns:
        Response dictionary

    Raises:
        LLMRequestError: If request fails
    """
    texts = request['texts']
    model = request.get('model')  # Optional

    start_time = time.time()
    provider = request.get('provider', 'auto')

    try:
        logger.info(f"Embedding request: provider={provider}, model={model}, texts={len(texts)}")
        response = await service.generate_embeddings(texts, model=model)

        elapsed = time.time() - start_time
        logger.info(f"Embedding completed in {elapsed:.2f}s")

        return response.model_dump() if hasattr(response, 'model_dump') else response.dict()
    except ProviderError as e:
        elapsed = time.time() - start_time
        logger.error(f"Embedding failed after {elapsed:.2f}s: {e}")
        raise LLMRequestError(f"Embedding generation failed: {e}")
    except Exception as e:
        elapsed = time.time() - start_time
        logger.exception(f"Unexpected error in embedding generation after {elapsed:.2f}s")
        raise LLMRequestError(f"Embedding generation failed: {e}")


async def process_request(request_json: str) -> Dict[str, Any]:
    """Process JSON request and return response.

    Args:
        request_json: JSON string containing request

    Returns:
        Response dictionary

    Raises:
        InvalidRequestError: If request is invalid
        ProviderUnavailableError: If no providers available
        LLMRequestError: If request fails
    """
    # Parse JSON
    try:
        request = json.loads(request_json)
    except json.JSONDecodeError as e:
        raise InvalidRequestError(f"Invalid JSON: {e}")

    # Validate request structure
    validate_request(request)

    # Determine operation (default: chat)
    operation = request.get('operation', 'chat')

    # Initialize LLM service
    async with LLMService() as service:
        # Check if any providers are available
        available = await service.provider_manager.get_available_providers()
        if not available:
            raise ProviderUnavailableError("No LLM providers available")

        # Route to appropriate handler
        if operation == 'chat':
            return await handle_chat_request(service, request)
        elif operation == 'completion':
            return await handle_completion_request(service, request)
        elif operation == 'embedding':
            return await handle_embedding_request(service, request)
        else:
            # Should have been caught by validate_request
            raise InvalidRequestError(f"Unknown operation: {operation}")


def main() -> int:
    """Main entry point for CLI.

    Returns:
        Exit code (0 = success, >0 = error)
    """
    parser = argparse.ArgumentParser(
        description='LLM Caller CLI Wrapper for subprocess integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Chat completion
  python3 llm_call.py --request-json '{
      "provider": "lmstudio",
      "messages": [{"role": "user", "content": "Hello"}]
  }'

  # Text completion
  python3 llm_call.py --request-json '{
      "operation": "completion",
      "prompt": "Once upon a time"
  }'

  # Embeddings
  python3 llm_call.py --request-json '{
      "operation": "embedding",
      "texts": ["Text 1", "Text 2"]
  }'
        """
    )

    parser.add_argument(
        '--request-json',
        type=str,
        required=True,
        help='JSON string containing request parameters'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging to stderr'
    )

    args = parser.parse_args()

    # Configure logging based on verbose flag
    if args.verbose:
        # Enable structured logging to stderr
        logger.handlers.clear()  # Remove NullHandler
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)  # INFO for request/response timing
    else:
        # Keep NullHandler (no logging output)
        logger.setLevel(logging.CRITICAL)  # Suppress all logs

    # Process request
    try:
        response = asyncio.run(process_request(args.request_json))

        # Write JSON response to stdout
        print(json.dumps(response, indent=2))

        return 0

    except CLIError as e:
        # Write structured error to stderr (pure JSON, no log messages)
        error_msg = {
            'error': str(e),
            'error_type': e.__class__.__name__,
            'timestamp': datetime.now().isoformat(),
            'exit_code': e.exit_code
        }
        print(json.dumps(error_msg, indent=2), file=sys.stderr)

        # Additional logging if verbose (separate from JSON error)
        logger.error(f"CLI error: {e.__class__.__name__}: {e}")

        return e.exit_code

    except Exception as e:
        # Unexpected error with full context
        logger.exception("Unexpected error in CLI")
        error_msg = {
            'error': f"Unexpected error: {e}",
            'error_type': type(e).__name__,
            'timestamp': datetime.now().isoformat(),
            'exit_code': 4
        }
        print(json.dumps(error_msg, indent=2), file=sys.stderr)
        return 4


if __name__ == '__main__':
    sys.exit(main())
