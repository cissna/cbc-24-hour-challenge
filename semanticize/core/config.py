"""Configuration management for API settings."""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class APIConfig:
    """API configuration."""
    base_url: str
    api_key: str
    model: str
    use_legacy_cli: bool = False  # Backward compatibility with gemini CLI


class ConfigManager:
    """Manages API configuration."""

    CONFIG_FILE = 'config.json'

    def __init__(self, semanticize_dir: Path):
        self.config_path = semanticize_dir / self.CONFIG_FILE
        self.semanticize_dir = semanticize_dir

    def load(self) -> Optional[APIConfig]:
        """Load configuration from disk."""
        if not self.config_path.exists():
            return None

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            return APIConfig(**data)
        except Exception:
            return None

    def save(self, config: APIConfig):
        """Save configuration to disk."""
        self.semanticize_dir.mkdir(exist_ok=True)

        with open(self.config_path, 'w') as f:
            json.dump(asdict(config), f, indent=2)

    def exists(self) -> bool:
        """Check if configuration exists."""
        return self.config_path.exists()

    def validate(self, config: APIConfig) -> tuple[bool, Optional[str]]:
        """Validate configuration.

        Returns:
            (is_valid, error_message)
        """
        if not config.base_url:
            return False, "base_url is required"

        if not config.api_key:
            return False, "api_key is required"

        if not config.model:
            return False, "model is required"

        # Basic URL validation
        if not (config.base_url.startswith('http://') or config.base_url.startswith('https://')):
            return False, "base_url must start with http:// or https://"

        return True, None
