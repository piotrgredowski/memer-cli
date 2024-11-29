import logging
from pathlib import Path
from typing import Annotated

import rich
import rich.emoji
import typer
from rich.console import Console

from memer.utils.images import MemeText
from memer.utils.images import create_meme
from memer.utils.images import generate_meme_name
from memer.utils.images import load_image
from memer.utils.settings import Template
from memer.utils.settings import configuration

console = Console()

logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=configuration.interface.typer.no_arg_is_help)

top_level_command_name = "create"


@app.command(name=top_level_command_name)
def create(
    *,
    template_name: Annotated[
        str,
        typer.Option(
            "--template-name",
            "-n",
            help=" The name of the meme template to use. If provided name "
            "is a path, it will be used as a template.",
        ),
    ],
    top_text: Annotated[
        str | None,
        typer.Option("--top-text", "-t", help="The text to display at the top of the meme."),
    ] = None,
    bottom_text: Annotated[
        str | None,
        typer.Option("--bottom-text", "-b", help="The text to display at the bottom of the meme."),
    ] = None,
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--output-path",
            "-o",
            help="The path where the generated meme will be saved.",
        ),
    ] = None,
) -> None:
    """Create a meme using the specified template and text options."""
    # TODO(Matez): add option such that if tempalte name is not provided, we open the search window
    # TODO(Matez): add option to customize font size, font color, etc.

    # TODO(Matez): catch exception and raise nicer one

    # Case where user provided a path to the template
    if Path(template_name).is_file():
        template = Template(path=Path(template_name))
        image = load_image(file_path=template_name)

    # In all other cases, we load it by name
    else:
        template = configuration.images.templates.discovered_templates[template_name]
        image = load_image(file_path=template.path)

    meme = create_meme(
        image=image,
        meme_text=MemeText(top_text=top_text, bottom_text=bottom_text),
        text_configuration=configuration.text,
    )
    # Current working directory / meme template name (path stem) + date. png
    default_output_path = generate_meme_name(template_stem=template.path.stem)
    saved_path = (output_path if output_path else default_output_path).resolve()

    meme.save(saved_path)

    # TODO(Mateusz): Maybe we should extract the printing somewhere else?
    rich.print(":mage: [green]Meme created![/green]")
    rich.print("Find it at:")
    rich.print(f"[bold]{saved_path}[/bold]")


if __name__ == "__main__":
    app()
