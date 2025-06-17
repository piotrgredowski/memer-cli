"""Professional exception handling for the memer application."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import typer

logger = logging.getLogger(__name__)


class MemerError(Exception):
    """Base exception for all memer-related errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize the exception.
        
        Args:
            message: Human-readable error message.
            cause: Optional underlying exception that caused this error.
        """
        super().__init__(message)
        self.message = message
        self.cause = cause


class ConfigurationError(MemerError):
    """Error related to configuration loading or validation."""


class TemplateError(MemerError):
    """Error related to template operations."""


class ImageProcessingError(MemerError):
    """Error related to image processing operations."""


class NetworkError(MemerError):
    """Error related to network operations."""


class ValidationError(MemerError):
    """Error related to input validation."""


def setup_exception_handler(debug: bool = False) -> None:
    """Set up global exception handler.
    
    Args:
        debug: Whether to show full stack traces.
    """

    def handle_exception(exc_type: type[BaseException], exc_value: BaseException, traceback: Any) -> None:
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Handle Ctrl+C gracefully
            typer.echo("\nOperation cancelled by user.")
            sys.exit(1)

        if isinstance(exc_value, MemerError):
            # Handle known application errors
            logger.error("Application error: %s", exc_value.message)
            if exc_value.cause:
                logger.debug("Caused by: %s", exc_value.cause)

            typer.echo(f"Error: {exc_value.message}", err=True)
            if debug and exc_value.cause:
                typer.echo(f"Caused by: {exc_value.cause}", err=True)
        else:
            # Handle unexpected errors
            logger.exception("Unexpected error: %s", exc_value)

            if debug:
                # In debug mode, show the full traceback
                sys.__excepthook__(exc_type, exc_value, traceback)
            else:
                typer.echo("An unexpected error occurred. Run with --verbose for details.", err=True)

        sys.exit(1)

    sys.excepthook = handle_exception


def setup_logging(debug: bool = False, log_file: Path | None = None) -> None:
    """Set up application logging.
    
    Args:
        debug: Whether to enable debug logging.
        log_file: Optional path to log file.
    """
    level = logging.DEBUG if debug else logging.INFO

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # File handler if specified
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
