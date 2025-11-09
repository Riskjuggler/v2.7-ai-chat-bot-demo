#!/usr/bin/env python
"""
LLM Caller Command Line Interface

Provides command-line access to LLM Caller functionality.
"""

import asyncio
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from llm_caller_cli.src import LLMService, TaskType
from llm_caller_cli.src.config.settings import ConfigManager, get_config


async def chat_command(args):
    """Handle chat command."""
    async with LLMService() as service:
        messages = [{"role": "user", "content": args.message}]

        # Build request parameters
        kwargs = {}
        if args.model:
            kwargs['model'] = args.model
        if args.task:
            kwargs['task_type'] = TaskType(args.task)
        if args.local_only:
            kwargs['prefer_local'] = True
        if args.temperature is not None:
            kwargs['temperature'] = args.temperature
        if args.max_tokens:
            kwargs['max_tokens'] = args.max_tokens

        try:
            if args.stream:
                print("🤖 Streaming response:")
                async for chunk in service.chat_completion_stream(messages, **kwargs):
                    if chunk.choices and chunk.choices[0].get('delta', {}).get('content'):
                        content = chunk.choices[0]['delta']['content']
                        print(content, end='', flush=True)
                print()  # New line after streaming
            else:
                response = await service.chat_completion(messages, **kwargs)

                if args.json:
                    print(json.dumps(response.dict(), indent=2))
                else:
                    print(f"🤖 Model: {response.model} ({response.provider})")
                    print(f"💭 Response: {response.choices[0].message.content}")
                    if response.usage:
                        print(f"📊 Tokens: {response.usage.total_tokens}")

        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1

    return 0


async def embed_command(args):
    """Handle embed command."""
    async with LLMService() as service:
        try:
            response = await service.generate_embeddings(
                [args.text],
                model=args.model
            )

            if args.json:
                print(json.dumps(response.dict(), indent=2))
            else:
                embedding = response.data[0].embedding
                print(f"🤖 Model: {response.model} ({response.provider})")
                print(f"📐 Dimensions: {len(embedding)}")
                print(f"🧮 Embedding: [{embedding[0]:.6f}, {embedding[1]:.6f}, ...]")

        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1

    return 0


async def models_command(args):
    """Handle models command."""
    async with LLMService() as service:
        try:
            models = await service.list_models()

            if args.json:
                models_data = [model.dict() for model in models]
                print(json.dumps(models_data, indent=2))
            else:
                if not models:
                    print("No models available")
                    return 0

                # Group by provider
                by_provider = {}
                for model in models:
                    if model.provider not in by_provider:
                        by_provider[model.provider] = []
                    by_provider[model.provider].append(model)

                for provider_name, provider_models in by_provider.items():
                    print(f"\n🔧 {provider_name.upper()} ({len(provider_models)} models):")
                    for model in provider_models:
                        capabilities = ", ".join(model.capabilities) if model.capabilities else "N/A"
                        context = f"{model.context_length:,}" if model.context_length else "N/A"
                        print(f"  • {model.id}")
                        print(f"    Capabilities: {capabilities}")
                        print(f"    Context: {context} tokens")

        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1

    return 0


async def status_command(args):
    """Handle status command."""
    async with LLMService() as service:
        try:
            health = await service.health_check()

            if args.json:
                print(json.dumps(health.dict(), indent=2))
            else:
                status_emoji = {
                    "healthy": "💚",
                    "degraded": "🟡",
                    "unhealthy": "🔴"
                }

                print(f"{status_emoji.get(health.status, '❓')} Service Status: {health.status}")
                print(f"📊 Models Available: {health.models_available}")
                print(f"⏱️  Uptime: {health.uptime_seconds:.1f}s")

                print(f"\n📡 Providers:")
                for provider_name, provider_data in health.providers.items():
                    status = provider_data.get('status', 'unknown')
                    emoji = "🟢" if status == "online" else "🔴" if status == "offline" else "🟡"
                    models_count = len(provider_data.get('models_available', []))
                    latency = provider_data.get('latency_ms')

                    print(f"  {emoji} {provider_name}: {status}")
                    print(f"    Models: {models_count}")
                    if latency:
                        print(f"    Latency: {latency:.1f}ms")
                    if provider_data.get('error_message'):
                        print(f"    Error: {provider_data['error_message']}")

        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1

    return 0


async def metrics_command(args):
    """Handle metrics command."""
    async with LLMService() as service:
        try:
            metrics = await service.get_metrics()

            if args.json:
                print(json.dumps(metrics.dict(), indent=2))
            else:
                print(f"📊 Service Metrics")
                print(f"Total Requests: {metrics.total_requests}")
                print(f"Successful: {metrics.successful_requests}")
                print(f"Failed: {metrics.failed_requests}")
                print(f"Average Latency: {metrics.average_latency_ms:.1f}ms")

                if metrics.provider_breakdown:
                    print(f"\n🔧 Provider Usage:")
                    for provider, count in metrics.provider_breakdown.items():
                        print(f"  {provider}: {count}")

                if metrics.task_breakdown:
                    print(f"\n🎯 Task Breakdown:")
                    for task, count in metrics.task_breakdown.items():
                        print(f"  {task}: {count}")

        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1

    return 0


def config_command(args):
    """Handle config command."""
    config_manager = ConfigManager()

    if args.init:
        try:
            config_path = config_manager.create_default_config()
            print(f"✅ Created default configuration: {config_path}")
            print(f"📝 Edit the file to customize settings")
            print(f"🔧 Example .env file created: {Path(config_path).parent / '.env.example'}")
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1

    elif args.validate:
        try:
            is_valid, errors = config_manager.validate_config()
            if is_valid:
                print("✅ Configuration is valid")
            else:
                print("❌ Configuration has errors:")
                for error in errors:
                    print(f"  • {error}")
                return 1
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1

    elif args.show:
        try:
            config = get_config()
            if args.json:
                print(json.dumps(config.dict(), indent=2, default=str))
            else:
                print(f"📋 Configuration")
                print(f"Config Path: {config_manager.config_path}")
                print(f"Host: {config.host}:{config.port}")
                print(f"Debug: {config.debug}")
                print(f"Enabled Providers: {', '.join(config.get_enabled_providers())}")
                print(f"Prefer Local: {config.routing.prefer_local}")
                print(f"Default Provider: {config.routing.default_provider or 'Auto'}")
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLM Caller Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s chat "Hello, world!"
  %(prog)s chat "Write a Python function" --task code_generation
  %(prog)s chat "Analyze this data" --model gpt-4 --stream
  %(prog)s embed "Text to vectorize" --model ada-002
  %(prog)s models list
  %(prog)s status
  %(prog)s config init
        """
    )

    # Global options
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Chat completion')
    chat_parser.add_argument('message', help='Message to send')
    chat_parser.add_argument('--model', '-m', help='Specific model to use')
    chat_parser.add_argument('--task', '-t', choices=[t.value for t in TaskType], help='Task type for routing')
    chat_parser.add_argument('--local-only', action='store_true', help='Use only local models')
    chat_parser.add_argument('--stream', '-s', action='store_true', help='Stream response')
    chat_parser.add_argument('--temperature', type=float, help='Temperature (0.0-2.0)')
    chat_parser.add_argument('--max-tokens', type=int, help='Maximum tokens to generate')

    # Embed command
    embed_parser = subparsers.add_parser('embed', help='Generate embeddings')
    embed_parser.add_argument('text', help='Text to embed')
    embed_parser.add_argument('--model', '-m', help='Embedding model to use')

    # Models command
    models_parser = subparsers.add_parser('models', help='List available models')
    models_parser.add_argument('action', nargs='?', default='list', choices=['list'], help='Action to perform')

    # Status command
    status_parser = subparsers.add_parser('status', help='Check service status')

    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Show service metrics')

    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument('--init', action='store_true', help='Create default configuration')
    config_group.add_argument('--validate', action='store_true', help='Validate configuration')
    config_group.add_argument('--show', action='store_true', help='Show current configuration')

    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return 1

    # Handle config command (synchronous)
    if args.command == 'config':
        return config_command(args)

    # Handle async commands
    async def run_async_command():
        if args.command == 'chat':
            return await chat_command(args)
        elif args.command == 'embed':
            return await embed_command(args)
        elif args.command == 'models':
            return await models_command(args)
        elif args.command == 'status':
            return await status_command(args)
        elif args.command == 'metrics':
            return await metrics_command(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1

    try:
        return asyncio.run(run_async_command())
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())