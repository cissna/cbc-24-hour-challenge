"""Setup command for configuring API settings."""

from pathlib import Path
import getpass

from ..core.config import ConfigManager, APIConfig


PRESETS = {
    'openrouter': {
        'base_url': 'https://openrouter.ai/api/v1',
        'model_example': 'anthropic/claude-3.5-sonnet'
    },
    'openai': {
        'base_url': 'https://api.openai.com/v1',
        'model_example': 'gpt-4'
    },
    'custom': {
        'base_url': '',
        'model_example': ''
    }
}


def run(project_root: Path):
    """Run the setup command."""
    semanticize_dir = project_root / '.semanticize'
    semanticize_dir.mkdir(exist_ok=True)

    config_manager = ConfigManager(semanticize_dir)

    print("=== Semanticize API Setup ===\n")

    # Check if config already exists
    existing = config_manager.load()
    if existing and not existing.use_legacy_cli:
        print(f"Existing configuration found:")
        print(f"  Base URL: {existing.base_url}")
        print(f"  Model: {existing.model}")
        print(f"  API Key: {'*' * (len(existing.api_key) - 4)}{existing.api_key[-4:]}")
        print()
        response = input("Overwrite? [y/N] ")
        if response.lower() != 'y':
            print("Cancelled.")
            return

    # Select provider
    print("Select provider:")
    print("  1. OpenRouter")
    print("  2. OpenAI")
    print("  3. Custom (any OpenAI-compatible API)")
    print()

    while True:
        choice = input("Enter choice [1-3]: ").strip()
        if choice == '1':
            preset = PRESETS['openrouter']
            break
        elif choice == '2':
            preset = PRESETS['openai']
            break
        elif choice == '3':
            preset = PRESETS['custom']
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

    # Get base URL
    print()
    if preset['base_url']:
        base_url_input = input(f"Base URL [{preset['base_url']}]: ").strip()
        base_url = base_url_input if base_url_input else preset['base_url']
    else:
        base_url = input("Base URL (e.g., https://api.example.com/v1): ").strip()

    # Get API key
    print()
    api_key = getpass.getpass("API Key: ").strip()

    # Get model
    print()
    if preset['model_example']:
        print(f"Example model: {preset['model_example']}")
    model = input("Model name: ").strip()

    # Create and validate config
    config = APIConfig(
        base_url=base_url,
        api_key=api_key,
        model=model,
        use_legacy_cli=False
    )

    valid, error = config_manager.validate(config)
    if not valid:
        print(f"\n✗ Configuration error: {error}")
        return

    # Save
    config_manager.save(config)

    print("\n✓ Configuration saved successfully!")
    print(f"  Location: {config_manager.config_path}")
    print("\nYou can now run 'semanticize init' to analyze your codebase.")
