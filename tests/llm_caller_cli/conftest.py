"""Pytest configuration for llm_caller_cli tests.

Configures sys.path to allow tests to import from 'src.*' module structure.
"""
import sys
from pathlib import Path

# Add module root to path so tests can import from 'src.*'
# This allows imports like: from src.config.settings import ...
module_root = Path(__file__).parent.parent
if str(module_root) not in sys.path:
    sys.path.insert(0, str(module_root))
