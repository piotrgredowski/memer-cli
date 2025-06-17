import logging
from typing import Annotated

import typer

from memer.cli_commands.config import app as config_app
from memer.cli_commands.create import app as create_app
from memer.cli_commands.create import top_level_command_name as create_app_top_level_command_name
from memer.cli_commands.templates import app as templates_app
from memer.core.exceptions import setup_exception_handler
from memer.core.exceptions import setup_logging
from memer.utils.helper_methods import get_typer_command_by_name

logger = logging.getLogger(__name__)

# Initialize app with default settings - configuration will be loaded lazily
app = typer.Typer(no_args_is_help=True)


@app.callback()
def main(
    *,
    debug: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable debug mode"),
    ] = False,
) -> None:
    """A CLI for all of your meme needs."""
    setup_logging(debug=debug)
    setup_exception_handler(debug=debug)

    if debug:
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
    app()
