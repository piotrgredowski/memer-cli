"""Pytest configuration and fixtures."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from memer.core.container import Container
from memer.core.container import set_container
from memer.utils.settings import Configuration


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config() -> Configuration:
    """Create a test configuration."""
    # Create a minimal test configuration
    return Configuration.model_validate({
        "interface": {
            "typer": {"no_arg_is_help": True}
        },
        "images": {
            "templates": {
                "search_paths": [],
                "extensions": ["jpg", "png", "jpeg"]
            },
            "fonts": {
                "path": "font/Anton-Regular.ttf",
                "size": 50
            },
            "output": {
                "path": ".",
                "format": "png"
            }
        },
        "network": {
            "timeout": 10,
            "verify_ssl": True
        }
    })


@pytest.fixture
def test_container(test_config: Configuration) -> Generator[Container, None, None]:
    """Create a test container with mocked configuration."""

    class TestConfigProvider:
        def get_configuration(self) -> Configuration:
            return test_config

    container = Container(config_provider=TestConfigProvider())
    original_container = None

    try:
        # Store original container if it exists
        from memer.core.container import _default_container
        original_container = _default_container

        # Set test container as default
        set_container(container)
        yield container

    finally:
        # Restore original container
        if original_container:
            set_container(original_container)
