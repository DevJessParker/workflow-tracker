"""Configuration loading and management."""

import os
import yaml
import re
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration manager."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.

        Args:
            config_path: Path to configuration file. If None, looks for:
                1. config/local.yaml
                2. config/config.yaml
                3. config/config.example.yaml
        """
        # Load environment variables from .env file
        load_dotenv()

        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        self._expand_env_vars(self.config)
        self._override_with_env()

    def _find_config_file(self) -> str:
        """Find the configuration file."""
        possible_paths = [
            "config/local.yaml",
            "config/config.yaml",
            "config/config.example.yaml",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        raise FileNotFoundError(
            "No configuration file found. Please create config/local.yaml from config/config.example.yaml"
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f) or {}

    def _expand_env_vars(self, obj: Any) -> Any:
        """Recursively expand environment variables in configuration.

        Supports syntax: ${VAR_NAME} or ${VAR_NAME:-default_value}

        Examples:
            ${CONFLUENCE_URL}                    # Required variable
            ${REPO_PATH:-.}                      # Optional with default
            ${CONFLUENCE_SPACE_KEY:-~YOURUSERID} # Optional with default
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._expand_env_vars(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = self._expand_env_vars(item)
        elif isinstance(obj, str):
            # Match ${VAR_NAME} or ${VAR_NAME:-default}
            pattern = r'\$\{([^}:]+)(?::-(.*?))?\}'

            def replace_var(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ''
                return os.getenv(var_name, default_value)

            return re.sub(pattern, replace_var, obj)

        return obj

    def _override_with_env(self):
        """Override configuration with environment variables."""
        # Confluence settings
        if os.getenv('CONFLUENCE_URL'):
            self.config.setdefault('confluence', {})['url'] = os.getenv('CONFLUENCE_URL')
        if os.getenv('CONFLUENCE_USERNAME'):
            self.config.setdefault('confluence', {})['username'] = os.getenv('CONFLUENCE_USERNAME')
        if os.getenv('CONFLUENCE_API_TOKEN'):
            self.config.setdefault('confluence', {})['api_token'] = os.getenv('CONFLUENCE_API_TOKEN')
        if os.getenv('CONFLUENCE_SPACE_KEY'):
            self.config.setdefault('confluence', {})['space_key'] = os.getenv('CONFLUENCE_SPACE_KEY')

        # Repository settings
        if os.getenv('REPOSITORY_PATH'):
            self.config.setdefault('repository', {})['path'] = os.getenv('REPOSITORY_PATH')

        # CI mode
        if os.getenv('CI_MODE'):
            self.config.setdefault('ci_mode', {})['enabled'] = os.getenv('CI_MODE').lower() == 'true'

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'confluence.url')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    def get_repository_path(self) -> str:
        """Get repository path to scan."""
        return self.get('repository.path', '.')

    def get_confluence_config(self) -> Dict[str, str]:
        """Get Confluence configuration."""
        return {
            'url': self.get('confluence.url'),
            'username': self.get('confluence.username'),
            'api_token': self.get('confluence.api_token'),
            'space_key': self.get('confluence.space_key'),
            'parent_page_id': self.get('confluence.parent_page_id'),
        }

    def get_scanner_config(self) -> Dict[str, Any]:
        """Get scanner configuration."""
        return self.get('scanner', {})

    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return self.get('output', {})

    def is_ci_mode(self) -> bool:
        """Check if running in CI mode."""
        return self.get('ci_mode.enabled', False)

    def __repr__(self) -> str:
        return f"Config(path={self.config_path})"
