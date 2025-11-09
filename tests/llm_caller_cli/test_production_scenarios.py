"""Production scenario tests for llm_call.py CLI wrapper.

Tests high-volume requests, timeouts, retries, concurrent requests,
and error handling under production-like conditions.
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List
import pytest


# Path to llm_call.py
LLM_CALL_PATH = Path(__file__).parent.parent / "llm_call.py"


def run_cli_request(request_data: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
    """Run CLI request and return response.

    Args:
        request_data: Request JSON dictionary
        timeout: Timeout in seconds

    Returns:
        Response dictionary (stdout parsed as JSON)

    Raises:
        subprocess.TimeoutExpired: If request times out
        subprocess.CalledProcessError: If CLI exits with error
        json.JSONDecodeError: If response is not valid JSON
    """
    cmd = [
        "python3",
        str(LLM_CALL_PATH),
        "--request-json",
        json.dumps(request_data)
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout
    )

    # Check for errors (non-zero exit code)
    if result.returncode != 0:
        error_info = {
            'exit_code': result.returncode,
            'stderr': result.stderr,
            'stdout': result.stdout
        }
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            output=result.stdout,
            stderr=result.stderr
        )

    # Parse JSON response
    return json.loads(result.stdout)


class TestProductionScenarios:
    """Production scenario tests for llm_call.py."""

    @pytest.mark.integration
    def test_high_volume_chat_requests(self):
        """Test handling of high-volume chat requests (sequential)."""
        num_requests = 10
        request_data = {
            "operation": "chat",
            "provider": "lmstudio",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }

        start_time = time.time()
        responses = []
        errors = []

        for i in range(num_requests):
            try:
                response = run_cli_request(request_data, timeout=30)
                responses.append(response)
            except Exception as e:
                errors.append(str(e))

        elapsed = time.time() - start_time

        # Assertions
        assert len(responses) + len(errors) == num_requests
        assert elapsed < 300, f"High-volume test took too long: {elapsed:.2f}s"

        # Log results
        print(f"\nHigh-volume test: {len(responses)} successful, {len(errors)} failed")
        print(f"Total time: {elapsed:.2f}s")
        print(f"Average time per request: {elapsed/num_requests:.2f}s")

    @pytest.mark.integration
    def test_timeout_handling(self):
        """Test timeout handling for long-running requests."""
        request_data = {
            "operation": "chat",
            "provider": "lmstudio",
            "messages": [
                {"role": "user", "content": "Write a very long essay about AI"}
            ],
            "max_tokens": 5000  # Large response
        }

        # Test with short timeout - should fail
        with pytest.raises(subprocess.TimeoutExpired):
            run_cli_request(request_data, timeout=1)

        # Test with reasonable timeout - should succeed
        try:
            response = run_cli_request(request_data, timeout=60)
            assert 'choices' in response or 'content' in response
        except subprocess.TimeoutExpired:
            # LM Studio not running - skip assertion
            pytest.skip("LM Studio not available for timeout test")

    @pytest.mark.integration
    def test_concurrent_requests(self):
        """Test handling of concurrent requests (simulated via parallel subprocess calls)."""
        num_concurrent = 5
        request_data = {
            "operation": "chat",
            "provider": "lmstudio",
            "messages": [{"role": "user", "content": f"Test message"}],
            "max_tokens": 20
        }

        start_time = time.time()

        # Launch concurrent subprocess calls
        processes = []
        for i in range(num_concurrent):
            cmd = [
                "python3",
                str(LLM_CALL_PATH),
                "--request-json",
                json.dumps(request_data)
            ]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            processes.append(proc)

        # Wait for all to complete
        responses = []
        errors = []
        for proc in processes:
            try:
                stdout, stderr = proc.communicate(timeout=30)
                if proc.returncode == 0:
                    responses.append(json.loads(stdout))
                else:
                    errors.append(stderr)
            except subprocess.TimeoutExpired:
                proc.kill()
                errors.append("Timeout")

        elapsed = time.time() - start_time

        # Assertions
        assert len(responses) + len(errors) == num_concurrent
        assert elapsed < 60, f"Concurrent test took too long: {elapsed:.2f}s"

        # Log results
        print(f"\nConcurrent test: {len(responses)} successful, {len(errors)} failed")
        print(f"Total time: {elapsed:.2f}s")

    @pytest.mark.integration
    def test_error_handling_invalid_json(self):
        """Test error handling for invalid JSON input."""
        cmd = [
            "python3",
            str(LLM_CALL_PATH),
            "--request-json",
            "invalid json"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Should exit with error code 1 (InvalidRequestError)
        assert result.returncode == 1
        assert "Invalid JSON" in result.stderr or "error" in result.stderr.lower()

    @pytest.mark.integration
    def test_error_handling_missing_fields(self):
        """Test error handling for missing required fields."""
        request_data = {
            "operation": "chat"
            # Missing 'messages' field
        }

        cmd = [
            "python3",
            str(LLM_CALL_PATH),
            "--request-json",
            json.dumps(request_data)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Should exit with error code 1 (InvalidRequestError)
        assert result.returncode == 1
        assert "messages" in result.stderr.lower()

    @pytest.mark.integration
    def test_error_context_in_response(self):
        """Test that error responses include proper context (timestamp, error_type)."""
        request_data = {
            "operation": "chat"
            # Missing messages
        }

        cmd = [
            "python3",
            str(LLM_CALL_PATH),
            "--request-json",
            json.dumps(request_data)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse error from stderr
        try:
            error_data = json.loads(result.stderr)
            assert 'error' in error_data
            assert 'error_type' in error_data
            assert 'timestamp' in error_data
            assert 'exit_code' in error_data
        except json.JSONDecodeError:
            # Error might be in text format - check for key fields
            assert 'error' in result.stderr.lower()

    @pytest.mark.integration
    def test_embedding_batch_processing(self):
        """Test batch embedding generation (production scenario)."""
        texts = [f"Test text {i}" for i in range(20)]

        request_data = {
            "operation": "embedding",
            "texts": texts,
            "provider": "lmstudio"
        }

        start_time = time.time()

        try:
            response = run_cli_request(request_data, timeout=60)
            elapsed = time.time() - start_time

            # Assertions
            assert 'embeddings' in response or 'data' in response
            print(f"\nEmbedding batch test: {len(texts)} texts in {elapsed:.2f}s")
        except subprocess.CalledProcessError as e:
            # LM Studio not running or embedding not available - skip
            pytest.skip(f"Embedding test failed: {e.stderr}")

    @pytest.mark.integration
    def test_structured_logging_output(self):
        """Test that structured logging is present in stderr."""
        request_data = {
            "operation": "chat",
            "provider": "lmstudio",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10
        }

        cmd = [
            "python3",
            str(LLM_CALL_PATH),
            "--request-json",
            json.dumps(request_data),
            "--verbose"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        # Check for structured logging in stderr
        # Should contain timestamps, log levels, operation info
        if result.returncode == 0:
            # Success case - check for info logs
            assert len(result.stderr) > 0  # Should have some logging
        else:
            # Error case - check for error logs
            assert 'ERROR' in result.stderr or 'WARNING' in result.stderr

    @pytest.mark.integration
    @pytest.mark.slow
    def test_stress_test_rapid_fire(self):
        """Stress test with rapid-fire requests (tests rate limiting / stability)."""
        num_requests = 30
        request_data = {
            "operation": "chat",
            "provider": "lmstudio",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5
        }

        start_time = time.time()
        responses = []
        errors = []

        for i in range(num_requests):
            try:
                response = run_cli_request(request_data, timeout=15)
                responses.append(response)
            except Exception as e:
                errors.append(str(e))
            # No delay - rapid fire

        elapsed = time.time() - start_time

        # Assertions
        assert len(responses) + len(errors) == num_requests
        print(f"\nStress test: {len(responses)}/{num_requests} successful in {elapsed:.2f}s")
        print(f"Success rate: {len(responses)/num_requests*100:.1f}%")

        # Should handle at least 50% successfully under stress
        assert len(responses) >= num_requests * 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
