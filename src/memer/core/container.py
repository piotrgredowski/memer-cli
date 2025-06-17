"""Dependency injection container for the memer application."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from memer.utils.settings import Configuration
from memer.utils.settings import load_configuration


class ConfigurationProvider(Protocol):
    """Protocol for configuration providers."""

    def get_configuration(self) -> Configuration:
        """Get the application configuration."""
        ...


class FileConfigurationProvider:
    """Configuration provider that loads from file system."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the configuration provider.

        Args:
            config_path: Optional path to configuration file.
        """
        self._config_path = config_path
        self._configuration: Configuration | None = None

    def get_configuration(self) -> Configuration:
        """Get the application configuration."""
        if self._configuration is None:
            self._configuration = load_configuration(config_path=self._config_path)
        return self._configuration


class Container:
    """Dependency injection container."""

    def __init__(self, config_provider: ConfigurationProvider | None = None) -> None:
        """Initialize the container.

        Args:
            config_provider: Configuration provider to use.
        """
        self._config_provider = config_provider or FileConfigurationProvider()

    @property
    def configuration(self) -> Configuration:
        """Get the application configuration."""
        return self._config_provider.get_configuration()


# Default container instance
_default_container: Container | None = None


def get_container() -> Container:
    """Get the default container instance."""
    global _default_container  # noqa: PLW0603
    if _default_container is None:
        _default_container = Container()
    return _default_container


def set_container(container: Container) -> None:
    """Set the default container instance."""
    global _default_container  # noqa: PLW0603
    _default_container = container
