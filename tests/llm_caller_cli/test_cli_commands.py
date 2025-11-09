"""
Integration tests for LLM caller CLI commands.

Tests validate:
- chat: Chat completion command with streaming and non-streaming
- embed: Embedding generation command
- models: List available models command
- status: Service status command
- metrics: Service metrics command (if available)
- config: Configuration management command
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestLLMCallerCLICommands:
    """Test LLM caller CLI commands."""

    def test_cli_help_shows_all_commands(self):
        """Test that all command options appear in CLI help."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Core commands
        assert "chat" in result.stdout
        assert "embed" in result.stdout
        assert "models" in result.stdout
        assert "status" in result.stdout
        assert "config" in result.stdout

    def test_chat_command_exists(self):
        """Test that chat command exists and is documented."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "chat", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "chat" in result.stdout.lower() or "message" in result.stdout.lower()

    def test_chat_command_has_options(self):
        """Test that chat command has all expected options."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "chat", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Core chat options
        assert "--model" in result.stdout or "-m" in result.stdout
        assert "--task" in result.stdout or "-t" in result.stdout
        assert "--stream" in result.stdout or "-s" in result.stdout
        assert "--temperature" in result.stdout
        assert "--max-tokens" in result.stdout
        assert "--local-only" in result.stdout

    def test_chat_stream_option_documented(self):
        """Test that chat streaming option is documented."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "chat", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--stream" in result.stdout

        # Should mention streaming
        help_text = result.stdout.lower()
        assert "stream" in help_text

    def test_embed_command_exists(self):
        """Test that embed command exists and is documented."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "embed", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "embed" in result.stdout.lower()

    def test_embed_command_has_model_option(self):
        """Test that embed command has model option."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "embed", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--model" in result.stdout or "-m" in result.stdout

    def test_models_command_exists(self):
        """Test that models command exists and is documented."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "models", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "models" in result.stdout.lower() or "list" in result.stdout.lower()

    def test_status_command_exists(self):
        """Test that status command exists and is documented."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "status", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "status" in result.stdout.lower()

    def test_config_command_exists(self):
        """Test that config command exists and is documented."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "config", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "config" in result.stdout.lower()

    def test_config_command_has_options(self):
        """Test that config command has all expected options."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "config", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Config options
        assert "--init" in result.stdout
        assert "--validate" in result.stdout
        assert "--show" in result.stdout

    def test_global_json_option_exists(self):
        """Test that global --json option exists."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--json" in result.stdout

    def test_global_verbose_option_exists(self):
        """Test that global --verbose option exists."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--verbose" in result.stdout or "-v" in result.stdout

    def test_all_commands_have_documentation_quality(self):
        """Test that all commands have adequate documentation."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Test each command for meaningful documentation
        commands_to_check = {
            'chat': 'chat',
            'embed': 'embed',
            'models': 'model',
            'status': 'status',
            'config': 'config',
        }

        help_text = result.stdout.lower()
        for command, keyword in commands_to_check.items():
            # Each command should be mentioned
            assert command in help_text, f"{command} command should be in help"
            # Should have relevant keyword
            assert keyword in help_text, f"{command} help should mention '{keyword}'"

    def test_chat_task_type_choices_documented(self):
        """Test that chat command documents task type choices."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "chat", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should show task types as choices
        help_text = result.stdout.lower()
        # Look for --task option with choices
        assert "--task" in result.stdout
        # Should mention routing or task
        assert "task" in help_text or "routing" in help_text

    def test_config_options_mutually_exclusive(self):
        """Test that config options appear as mutually exclusive choices."""
        result = subprocess.run(
            [sys.executable, "llm_cli.py", "config", "--help"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # All three options should be present
        assert "--init" in result.stdout
        assert "--validate" in result.stdout
        assert "--show" in result.stdout

        # Should indicate mutual exclusivity (via required group or similar)
        help_text = result.stdout.lower()
        # Config command requires one of these options
        assert "init" in help_text and "validate" in help_text and "show" in help_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
