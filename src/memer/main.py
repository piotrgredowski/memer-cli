import logging
import sys
from typing import Annotated

import typer

from memer.cli_commands.config import app as config_app
from memer.cli_commands.create import app as create_app
from memer.cli_commands.create import top_level_command_name as create_app_top_level_command_name
from memer.cli_commands.templates import app as templates_app
from memer.utils.helper_methods import get_typer_command_by_name
from memer.utils.helper_methods import handle_uncaught_exception
from memer.utils.settings import configuration

# TODO(Mateusz): we should dump the logs to file as well, even if no debug mode
logging.basicConfig(
    level=logging.INFO,
    format=("%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"),
)
logger = logging.getLogger(__name__)

debug_mode = False

# TODO(Mateusz): settings should be in typer context

# TODO(Krzysztof): add an interactive memer setup command
# (initial setup, ask if the user wants to download default templates / fonts)

app = typer.Typer(no_args_is_help=configuration.interface.typer.no_arg_is_help)

# TODO(Mateusz): at every docstring i was breaking line when it was too long
# This breaks how typer displays help
# What should we do with it?

# TODO(Mateusz): i am running memer with uv run memer.py  [...]
# it would be cool for the users to be able to run it by just typing uvx memer ...

# TODO(Mateusz): add default help option if no command passed


# Register the custom exception handler
sys.excepthook = handle_uncaught_exception


@app.callback()
def main(
    *,
    debug: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable debug mode"),
    ] = False,
) -> None:
    """A CLI for all of your meme needs."""
    if debug:
        global debug_mode  # noqa: PLW0603 - good case for a global switch
        debug_mode = debug

        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled!")


# This is a trick to make the command from a lower level typer app a top level command
# From user perspective it will look like it is a top level command (memer create)
# instead of a subcommand (e.g. memer create create)
app.command()(
    get_typer_command_by_name(
        app=create_app, command_name=create_app_top_level_command_name)
)

# add subcommands
app.add_typer(
    typer_instance=config_app,
    name="config",
    help="Configuration related commands.",
)

# TODO(Mateusz): what about singular template? it should be alias to the same
app.add_typer(
    typer_instance=templates_app,
    name="templates",
    help="Meme template related commands.",
)

if __name__ == "__main__":
    try:
        app()
    except Exception:
        if debug_mode:
            raise
        else:
            # Show user-friendly error message without stack trace
            # TODO(Mateusz): add logs location to the message
            typer.echo("An unexpected error occurred! 😢")
            typer.echo(
                "Please contact support or run with '--debug' for more details.")
