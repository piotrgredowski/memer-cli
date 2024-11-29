import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Annotated

import rich
import typer
from requests.exceptions import RequestException
from rich.console import Console
from rich.progress import track
from rich.table import Table

# TODO(Mateusz): we need to fix those implicit relative imports...
from memer.utils.remote_templates import pull_image_from_url
from memer.utils.settings import Template
from memer.utils.settings import TemplateToPull
from memer.utils.settings import configuration
from memer.utils.settings import get_user_data_templates_path
from memer.utils.settings import load_default_template_list

console = Console()

logger = logging.getLogger(__name__)

app = typer.Typer(no_args_is_help=configuration.interface.typer.no_arg_is_help)


# We do not use the default, typer infered name here,
# because we want the command to be called "list", but that would shadow the built-in list function.
@app.command(name="list")
def list_templates(
    *,
    verbose: Annotated[bool, typer.Option(
        "--verbose", "-v", help="Enable verbose output")] = False,
) -> None:
    """Lists the available templates.

    Args:
        verbose (bool): If True, enables verbose output which includes the
            template's name, path, and key.
            If False, only the template's name is displayed.

    Returns:
        None
    """
    # TODO(Mateusz): docstring looks weird with the line breaks
    discovered_templates = configuration.images.templates.discovered_templates
    _echo_templates(
        templates=discovered_templates.values(),
        attributes=["name", "path", "key"] if verbose else ["name"],
    )


@app.command()
def search(phrase: str) -> None:
    """Searches for templates that match the given phrase and prints the results.

    Args:
        phrase (str): The phrase to search for in the template names.

    Returns:
        None
    """
    # TODO(Mateusz): add option to have raw output in order to pipe it to create meme
    # TODO(Mateusz): maybe make interactive? prompt_toolkit could help
    search_phrase = phrase.strip().strip('"').strip("'").lower()
    discovered_templates = configuration.images.templates.discovered_templates
    matching_templates = [
        template
        for template in discovered_templates.values()
        if _phrase_present_in_template(template=template, phrase=search_phrase)
    ]
    rich.print(f"[bold]Search results for '{phrase}':[/bold]")

    _echo_templates(templates=matching_templates,
                    attributes=["name", "path", "key"])


@app.command()
def pull(
    *,
    url: Annotated[str | None, typer.Option("--url", "-u")] = None,
    name: Annotated[str | None, typer.Option("--name", "-n")] = None,
    from_file: Annotated[Path | None,
                         typer.Option("--from-file", "-f")] = None,
    defaults: Annotated[bool, typer.Option("--defaults", "-d")] = False,
) -> None:
    """Pulls meme templates from various sources and saves them to the user data template path.

    Parameters:
    url (str | None): The URL of the meme template to pull. Specified with --url or -u option.
    name (str | None): The name to assign to the pulled meme template.
    Specified with --name or -n option.
    from_file (Path | None): The path to a file containing URLs of meme templates to pull
    Specified with --from-file or -f option.
    defaults (bool): Flag to pull default meme templates. Specified with --defaults or -d option.

    """
    user_data_template_path = get_user_data_templates_path()
    # TODO(Mateusz): add help text
    # TODO(Mateusz): Should this check be here? or its too low level?
    if not user_data_template_path.exists():
        user_data_template_path.mkdir(parents=True)

    to_pull_list: list[TemplateToPull] = []
    if url:
        to_pull_list.append(TemplateToPull(url=url, name=name))

    if from_file:
        to_pull_list.extend(load_default_template_list(from_file))

    if defaults:
        logger.debug("Pulling default templates.")
        default_templates = load_default_template_list()
        to_pull_list.extend(default_templates)

    # This is a single file case:

    to_pull_set = set(to_pull_list)
    rich.print(f"[bold]Pulling {len(to_pull_set)} templates:[/bold]")

    # TODO(Mateusz): this should be async
    failed_downloads: list[list[str | None]] = []
    for meme_to_pull in track(to_pull_set, description="Pulling templates..."):
        logger.debug("Pulling template from URL: %s", str(meme_to_pull.url))

        try:
            downloaded_template_path = pull_image_from_url(
                url=meme_to_pull.url,
                target_dir_path=user_data_template_path,
                timeout=configuration.images.remote.timeout,
                name=meme_to_pull.name,
                verify_ssl=configuration.images.remote.verify_ssl,
            )
            rich.print(
                f"[bold]Template downloaded to:[/bold] {downloaded_template_path}")

        except RequestException as e:
            failed_downloads.append([meme_to_pull.name, meme_to_pull.url])
            logger.debug(
                "Failed to pull template %s " "from URL: %s (%s)",
                meme_to_pull.name,
                meme_to_pull.url,
                e,
            )
            continue

    rich.print(f"Successfully pulled {
               len(to_pull_list)-len(failed_downloads)} templates")
    if failed_downloads:
        rich.print(
            "[yellow]Error while pulling templates (please check " "the provided URL(s)):[/yellow]"
        )

        table = Table(title="Failed downloads")
        table.add_column("Name", style="white", header_style="bold")
        table.add_column("URL", style="red", header_style="bold")
        for failed_download in failed_downloads:
            table.add_row(*failed_download)
        console.print(table)


def _echo_templates(templates: Iterable[Template], attributes: list[str]) -> None:
    table = Table(*attributes, title="Templates")

    for template in templates:
        values = [str(getattr(template, attribute))
                  for attribute in attributes]
        table.add_row(*values)
    console.print(table)


def _phrase_present_in_template(template: Template, phrase: str) -> bool:
    """Check if a given phrase is present in the template's name, key, or path.

    This function searches for the phrase in a sanitized version of the
    template's name, key, and path, as well as in the original concatenated
    string of these attributes. The search is case-insensitive and ignores
    certain special characters by replacing them with spaces.

    Args:
        template (Template): The template object containing name, key, and path attributes.
        phrase (str): The phrase to search for within the template's attributes.

    Returns:
        bool: True if the phrase is found in the sanitized or original string, False otherwise.
    """
    # TODO(Mateusz): This search could be more clever.
    # It could also return number of "hits" to rank the results.
    search_body = (template.name + template.key + str(template.path)).lower()
    sanitized_body = (
        search_body.replace("-", " ")
        .replace("_", " ")
        .replace(".", " ")
        .replace("/", " ")
        .replace("\\", " ")
        .replace(" ", "")
    )

    return phrase in sanitized_body + search_body
