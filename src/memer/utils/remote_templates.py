from pathlib import Path

import requests

from .memer_exceptions import RemoteTemplateError


def pull_image_from_url(
    *,
    url: str,
    timeout: int,
    target_dir_path: Path,
    verify_ssl: bool,
    name: str | None = None,
) -> Path:
    """Downloads an image from a given URL and saves it to a specified directory.

    Args:
        url (str): The URL of the image to download.
        timeout (int): The timeout duration for the request in seconds.
        target_dir_path (Path): The directory path where the image will be saved.
        verify_ssl (bool): Whether to verify SSL certificates.
        name (str | None, optional): The name to save the image as.
            If not provided, the name will be derived from the URL.

    Returns:
        Path: The path to the saved image file.

    Raises:
        RemoteTemplateError: If the file name cannot be determined from the URL.
        requests.exceptions.RequestException: If there is an issue with the HTTP request.
    """
    # Generate a default file name if none is provided
    url_path = Path(url)
    if name is None:
        name = url_path.name
        if not name:
            message = "Could not determine file name from URL."
            raise RemoteTemplateError(message)

    # Handle the case when user did not provide extension
    if Path(name).suffix == "":
        name += url_path.suffix

    name_without_spaces = name.replace(" ", "_")

    # Full path to save the image
    file_path = target_dir_path / name_without_spaces

    # Download the image
    response = requests.get(url=url, timeout=timeout, verify=verify_ssl)
    response.raise_for_status()  # Ensure we notice bad responses

    # Save the image to the specified path
    with file_path.open("wb") as file:
        file.write(response.content)

    return file_path
