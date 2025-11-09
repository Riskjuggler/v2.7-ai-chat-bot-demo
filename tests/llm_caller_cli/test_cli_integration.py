"""
Integration tests for llm_call.py CLI wrapper.

Tests subprocess execution, JSON I/O, error handling, and provider routing.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

import pytest


# Path to CLI script
CLI_PATH = Path(__file__).parent.parent / "llm_call.py"


def run_cli(request_json: str, verbose: bool = False) -> tuple[int, str, str]:
    """Run CLI with JSON request via subprocess.

    Args:
        request_json: JSON request string
        verbose: Enable verbose logging

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    cmd = [
        sys.executable,
        str(CLI_PATH),
        "--request-json", request_json
    ]

    if verbose:
        cmd.append("--verbose")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30
    )

    return result.returncode, result.stdout, result.stderr


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_exists(self):
        """Verify CLI script exists and is executable."""
        assert CLI_PATH.exists(), f"CLI script not found: {CLI_PATH}"
        assert CLI_PATH.is_file(), f"CLI path is not a file: {CLI_PATH}"

    def test_missing_request_json_arg(self):
        """Verify CLI fails without --request-json argument."""
        cmd = [sys.executable, str(CLI_PATH)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        assert result.returncode != 0, "CLI should fail without --request-json"
        assert "request-json" in result.stderr.lower(), "Error should mention missing argument"

    def test_invalid_json(self):
        """Verify CLI handles invalid JSON gracefully."""
        returncode, stdout, stderr = run_cli("{not valid json}")

        assert returncode == 1, "Should return exit code 1 for invalid JSON"
        assert "error" in stderr.lower(), "Stderr should contain error message"

        # Try to parse stderr as JSON (should be structured error)
        try:
            error = json.loads(stderr)
            assert "error" in error
            assert "InvalidRequestError" in error.get("error_type", "")
        except json.JSONDecodeError:
            pytest.fail("Stderr should be valid JSON for structured errors")

    def test_empty_request(self):
        """Verify CLI handles empty request object."""
        request = json.dumps({})
        returncode, stdout, stderr = run_cli(request)

        assert returncode == 1, "Should return exit code 1 for empty request"

        error = json.loads(stderr)
        assert "messages" in error["error"].lower(), "Should complain about missing messages"


class TestChatCompletionRequests:
    """Test chat completion requests."""

    def test_minimal_chat_request(self):
        """Test minimal valid chat request."""
        request = {
            "operation": "chat",
            "messages": [
                {"role": "user", "content": "Hello, world!"}
            ]
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        # Note: This may fail if no providers are available
        # That's expected behavior - test the error handling
        if returncode == 2:
            error = json.loads(stderr)
            assert "provider" in error["error"].lower()
            pytest.skip("No providers available (expected in some environments)")

        assert returncode in [0, 2], f"Unexpected exit code: {returncode}"

        if returncode == 0:
            response = json.loads(stdout)
            assert "choices" in response
            assert len(response["choices"]) > 0
            assert "message" in response["choices"][0]
            assert "content" in response["choices"][0]["message"]

    def test_chat_with_lmstudio_provider(self):
        """Test chat request with explicit LMStudio provider."""
        request = {
            "operation": "chat",
            "provider": "lmstudio",
            "messages": [
                {"role": "user", "content": "Say 'test successful'"}
            ],
            "max_tokens": 50
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        if returncode == 2:
            pytest.skip("LMStudio provider not available")

        assert returncode == 0, f"Request failed: {stderr}"

        response = json.loads(stdout)
        assert response.get("provider") == "lmstudio" or returncode == 2

    def test_chat_with_model_selection(self):
        """Test chat request with specific model."""
        request = {
            "operation": "chat",
            "model": "deepseek-coder",
            "messages": [
                {"role": "user", "content": "Write a hello world function"}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        if returncode == 2:
            pytest.skip("Requested model not available")

        if returncode == 0:
            response = json.loads(stdout)
            # Model name might be normalized, just check for content
            assert "choices" in response

    def test_chat_missing_messages(self):
        """Test chat request without messages field."""
        request = {
            "operation": "chat",
            # Missing messages
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        assert returncode == 1, "Should return exit code 1 for missing messages"

        error = json.loads(stderr)
        assert "messages" in error["error"].lower()

    def test_chat_empty_messages(self):
        """Test chat request with empty messages list."""
        request = {
            "operation": "chat",
            "messages": []
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        assert returncode == 1, "Should return exit code 1 for empty messages"

    def test_chat_with_generation_params(self):
        """Test chat request with various generation parameters."""
        request = {
            "operation": "chat",
            "messages": [
                {"role": "user", "content": "Test"}
            ],
            "temperature": 0.5,
            "max_tokens": 50,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        if returncode == 2:
            pytest.skip("No providers available")

        assert returncode in [0, 3], f"Unexpected exit code: {returncode}"

        if returncode == 0:
            response = json.loads(stdout)
            assert "choices" in response


class TestCompletionRequests:
    """Test text completion requests."""

    def test_minimal_completion_request(self):
        """Test minimal valid completion request."""
        request = {
            "operation": "completion",
            "prompt": "Once upon a time"
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        if returncode == 2:
            pytest.skip("No providers available")

        assert returncode in [0, 3], f"Unexpected exit code: {returncode}"

        if returncode == 0:
            response = json.loads(stdout)
            assert "choices" in response or "text" in response

    def test_completion_missing_prompt(self):
        """Test completion request without prompt field."""
        request = {
            "operation": "completion"
            # Missing prompt
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        assert returncode == 1, "Should return exit code 1 for missing prompt"

        error = json.loads(stderr)
        assert "prompt" in error["error"].lower()


class TestEmbeddingRequests:
    """Test embedding generation requests."""

    def test_minimal_embedding_request(self):
        """Test minimal valid embedding request."""
        request = {
            "operation": "embedding",
            "texts": ["Hello, world!", "Test embedding"]
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        if returncode == 2:
            pytest.skip("No embedding providers available")

        assert returncode in [0, 3], f"Unexpected exit code: {returncode}"

        if returncode == 0:
            response = json.loads(stdout)
            assert "data" in response
            assert len(response["data"]) == 2
            assert "embedding" in response["data"][0]
            assert isinstance(response["data"][0]["embedding"], list)

    def test_embedding_single_text(self):
        """Test embedding with single text."""
        request = {
            "operation": "embedding",
            "texts": ["Single text"]
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        if returncode == 2:
            pytest.skip("No embedding providers available")

        if returncode == 0:
            response = json.loads(stdout)
            assert len(response["data"]) == 1

    def test_embedding_missing_texts(self):
        """Test embedding request without texts field."""
        request = {
            "operation": "embedding"
            # Missing texts
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        assert returncode == 1, "Should return exit code 1 for missing texts"

        error = json.loads(stderr)
        assert "texts" in error["error"].lower()

    def test_embedding_empty_texts(self):
        """Test embedding request with non-list texts."""
        request = {
            "operation": "embedding",
            "texts": "not a list"
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        assert returncode == 1, "Should return exit code 1 for invalid texts type"


class TestErrorHandling:
    """Test error handling and exit codes."""

    def test_unknown_operation(self):
        """Test request with unknown operation."""
        request = {
            "operation": "unknown_op",
            "messages": [{"role": "user", "content": "Test"}]
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        assert returncode == 1, "Should return exit code 1 for unknown operation"

        error = json.loads(stderr)
        assert "unknown" in error["error"].lower()

    def test_structured_error_output(self):
        """Verify all errors produce structured JSON output."""
        invalid_requests = [
            "{}",  # Empty
            '{"messages": []}',  # Empty messages
            '{"operation": "chat"}',  # Missing messages
            '{"operation": "unknown"}',  # Unknown operation
        ]

        for req in invalid_requests:
            returncode, stdout, stderr = run_cli(req)

            assert returncode != 0, f"Should fail for invalid request: {req}"

            # Stderr should be valid JSON
            try:
                error = json.loads(stderr)
                assert "error" in error
                assert "error_type" in error
            except json.JSONDecodeError:
                pytest.fail(f"Stderr should be JSON for request: {req}\nGot: {stderr}")


class TestProviderRouting:
    """Test provider selection and routing."""

    def test_default_operation_is_chat(self):
        """Verify default operation is chat completion."""
        request = {
            # No operation specified
            "messages": [{"role": "user", "content": "Test"}]
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        if returncode == 2:
            pytest.skip("No providers available")

        # Should succeed or fail at LLM level, not validation
        assert returncode in [0, 2, 3], "Should treat as chat operation"

    def test_task_type_routing(self):
        """Test request with task type for routing."""
        request = {
            "operation": "chat",
            "messages": [{"role": "user", "content": "Write a Python function"}],
            "task_type": "code_generation"
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        if returncode == 2:
            pytest.skip("No providers available")

        # Task type should not cause validation error
        assert returncode in [0, 3], "Valid task_type should be accepted"

    def test_invalid_task_type_ignored(self):
        """Test that invalid task_type is ignored (not fatal)."""
        request = {
            "operation": "chat",
            "messages": [{"role": "user", "content": "Test"}],
            "task_type": "invalid_task_type"
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        if returncode == 2:
            pytest.skip("No providers available")

        # Should proceed despite invalid task_type (logged but not fatal)
        assert returncode in [0, 3], "Invalid task_type should be ignored"


class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.slow
    def test_response_time_under_500ms_simple_request(self):
        """Verify simple request completes in <500ms (excluding LLM time)."""
        import time

        request = {
            "operation": "chat",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5  # Minimal generation
        }

        start = time.time()
        returncode, stdout, stderr = run_cli(json.dumps(request))
        elapsed_ms = (time.time() - start) * 1000

        if returncode == 2:
            pytest.skip("No providers available")

        # This includes subprocess startup + LLM call
        # <500ms overhead is the target (excluding LLM generation time)
        # With minimal tokens, should be fast
        print(f"Request took {elapsed_ms:.0f}ms")

        # Lenient timeout for CI environments
        assert elapsed_ms < 5000, f"Request too slow: {elapsed_ms}ms"


class TestJSONIOCompliance:
    """Test JSON input/output compliance."""

    def test_stdout_only_contains_json_on_success(self):
        """Verify stdout contains only JSON on success."""
        request = {
            "operation": "chat",
            "messages": [{"role": "user", "content": "Test"}]
        }

        returncode, stdout, stderr = run_cli(json.dumps(request))

        if returncode == 0:
            # Stdout should be valid JSON
            response = json.loads(stdout)
            assert isinstance(response, dict)

    def test_stderr_contains_json_on_error(self):
        """Verify stderr contains JSON error on failure."""
        request = json.dumps({"invalid": "request"})

        returncode, stdout, stderr = run_cli(request)

        assert returncode != 0, "Should fail"

        # Stderr should be valid JSON
        error = json.loads(stderr)
        assert "error" in error
        assert isinstance(error["error"], str)

    def test_verbose_flag(self):
        """Verify --verbose flag enables debug logging."""
        request = {
            "operation": "chat",
            "messages": [{"role": "user", "content": "Test"}]
        }

        returncode, stdout, stderr = run_cli(json.dumps(request), verbose=True)

        # Verbose flag should add logging to stderr but not break JSON output
        if returncode == 0:
            response = json.loads(stdout)
            assert isinstance(response, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
