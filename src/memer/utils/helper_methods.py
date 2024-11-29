import sys
import traceback
from collections.abc import Callable
from logging import getLogger
from types import TracebackType

import typer

from .memer_exceptions import TyperCommandGetterError

logger = getLogger(name=__name__)

# Custom exception handler


def handle_uncaught_exception(
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    exc_tb: TracebackType | None,
) -> None:
    """Handle uncaught exceptions (and traceback) depending on debug mode flag."""
    if not hasattr(sys, "gettrace") or sys.gettrace() is None:  # Check if we're in debug mode
        # If not in debug mode, show a user-friendly message
        logger.error(
            "An unexpected error occurred. Please contact support "
            "or run the app with '--debug' for more details."
        )
    else:
        # In debug mode, show the full stack trace
        logger.error("An error occurred:")
        traceback.print_exception(exc_type, exc_value, exc_tb)


def split_camel_case_words(camel_case_string: str) -> str:
    """Splits a camel case string into words separated by spaces.

    Args:
        camel_case_string (str): The camel case string to be split.

    Returns:
        str: A string with words separated by spaces.
    """
    nice_name = ""
    for char in camel_case_string:
        if char.isupper() and nice_name and nice_name[-1] != " ":
            nice_name += " "
        nice_name += char
    return nice_name


def convert_string_to_nice_name(source_name: str) -> str:
    """Converts a given string to a more readable 'nice' name.

    This function performs the following transformations:
    1. Replaces underscores and hyphens with spaces.
    2. Splits camel case words into separate words.
    3. Capitalizes each word.

    Args:
        source_name (str): The original string to be converted.

    Returns:
        str: The converted 'nice' name.
    """
    # Replace underscores and hyphens with spaces
    nice_name = source_name.replace("_", " ").replace("-", " ")

    nice_name = split_camel_case_words(camel_case_string=nice_name)
    # Capitalize each word
    return " ".join(word.capitalize() for word in nice_name.split())


def get_typer_command_by_name(app: typer.Typer, command_name: str) -> Callable[..., None]:
    """Get a command by its name from a Typer application.

    Args:
        app (typer.Typer): The Typer application to search for the command.
        command_name (str): The name of the command to retrieve.

    Returns:
        Callable[..., None]: The command function.
    """
    discovered_commands: list[typer.models.CommandInfo] = [
        command for command in app.registered_commands if command.name == command_name
    ]
    if len(discovered_commands) > 1:
        error_message = f"Multiple commands with the name '{
            command_name}' found."
        raise TyperCommandGetterError(error_message)

    if not discovered_commands:
        error_message = f"No command with the name '{command_name}' found."
        raise TyperCommandGetterError(error_message)

    if discovered_commands[0].callback is None:
        error_message = f"The command '{
            command_name}' has no function associated with it."
        raise TyperCommandGetterError(error_message)

    return discovered_commands[0].callback
