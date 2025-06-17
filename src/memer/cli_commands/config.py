import rich
import typer

from memer.core.container import get_container
from memer.utils.settings import get_config_path

app = typer.Typer(no_args_is_help=True)


@app.command()
def show() -> None:
    """Logs the configuration."""
    container = get_container()
    rich.print(container.configuration.model_dump())


@app.command()
def path() -> None:
    """Shows the path to the configuration."""
    rich.print(str(get_config_path()))


@app.command()
def edit() -> None:
    """Opens the configuration in the default editor."""
    msg = "Opening the configuration in the default editor is not implemented yet."
    raise NotImplementedError(msg)


# TODO(Mateusz): add commands to edit the configuration and delete the configuration file
