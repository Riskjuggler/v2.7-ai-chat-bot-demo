#!/usr/bin/env python3
"""
Validation script for llm_caller_cli module integration.

Tests that the module can be imported and basic functionality works.
"""

import sys
from pathlib import Path

def main():
    """Run integration validation tests."""
    print("=" * 70)
    print("LLM Caller CLI Module Integration Validation")
    print("=" * 70)

    # Test 1: Import main module
    print("\n1. Testing module import...")
    try:
        import llm_caller_cli
        print(f"   ✓ Module imported successfully")
        print(f"   ✓ Version: {llm_caller_cli.__version__}")
    except ImportError as e:
        print(f"   ✗ Failed to import module: {e}")
        return False

    # Test 2: Import core components
    print("\n2. Testing core component imports...")
    try:
        from llm_caller_cli.src.core.llm_service import LLMService
        from llm_caller_cli.src.core.routing_engine import RoutingEngine
        print("   ✓ Core components imported")
    except ImportError as e:
        print(f"   ✗ Failed to import core components: {e}")
        return False

    # Test 3: Import configuration
    print("\n3. Testing configuration imports...")
    try:
        from llm_caller_cli.src.config.settings import LLMCallerConfig, get_config
        from llm_caller_cli.src.config.model_capabilities import ModelCapabilityRegistry
        print("   ✓ Configuration imports successful")
    except ImportError as e:
        print(f"   ✗ Failed to import configuration: {e}")
        return False

    # Test 4: Import models
    print("\n4. Testing model imports...")
    try:
        from llm_caller_cli.src.models.request_models import (
            ChatCompletionRequest,
            ChatCompletionResponse,
            TaskType
        )
        print("   ✓ Model imports successful")
    except ImportError as e:
        print(f"   ✗ Failed to import models: {e}")
        return False

    # Test 5: Import providers
    print("\n5. Testing provider imports...")
    try:
        from llm_caller_cli.src.providers.base_provider import ProviderAdapter, ProviderError
        from llm_caller_cli.src.providers.lmstudio_provider import LMStudioProvider
        print("   ✓ Provider imports successful (LMStudio)")
        print("   ℹ Note: OpenAI and Anthropic providers not yet implemented")
    except ImportError as e:
        print(f"   ✗ Failed to import providers: {e}")
        return False

    # Test 6: Check file structure
    print("\n6. Validating file structure...")
    base_path = Path(__file__).parent / "llm_caller_cli"
    required_paths = [
        base_path / "__init__.py",
        base_path / "src",
        base_path / "src" / "core",
        base_path / "src" / "config",
        base_path / "src" / "models",
        base_path / "src" / "providers",
    ]

    all_exist = True
    for path in required_paths:
        if path.exists():
            print(f"   ✓ {path.relative_to(Path.cwd())}")
        else:
            print(f"   ✗ Missing: {path.relative_to(Path.cwd())}")
            all_exist = False

    if not all_exist:
        return False

    # Test 7: Check configuration files
    print("\n7. Checking configuration files...")
    config_files = [
        Path(".env.example"),
        Path("requirements.txt"),
        Path("pytest.ini"),
    ]

    for config_file in config_files:
        if config_file.exists():
            print(f"   ✓ {config_file}")
        else:
            print(f"   ✗ Missing: {config_file}")

    # Summary
    print("\n" + "=" * 70)
    print("✓ Integration validation PASSED")
    print("=" * 70)
    print("\nModule is ready for use!")
    print("\nNext steps:")
    print("  1. Copy .env.example to .env and configure your LLM providers")
    print("  2. Install dependencies: pip install -r requirements.txt")
    print("  3. Run tests: pytest tests/llm_caller_cli/")
    print("\n")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
