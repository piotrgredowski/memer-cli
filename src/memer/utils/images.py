import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pytz
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from memer.utils.memer_exceptions import MemeGenerationError
from memer.utils.settings import MarginsConfiguration
from memer.utils.settings import TextConfiguration

logger = logging.getLogger(__name__)


@dataclass
class MemeText:
    """A class to represent meme text with optional top and bottom text and a font.

    Attributes:
        top_text (str | None): The text to display at the top of the meme.
        bottom_text (str | None): The text to display at the bottom of the meme.
        font (ImageFont.FreeTypeFont | None): The font to use for the text.
        By default uses font from configuration.
    """

    top_text: str | None = None
    bottom_text: str | None = None
    font: ImageFont.FreeTypeFont | None = None

    def __post_init__(self) -> None:
        """Post-initialization method to perform additional setup after the object is created.

        This method is automatically called after the object's initialization to validate
        the text attribute of the instance.

        Returns:
            None
        """
        self._validate_text()

    def _validate_text(self) -> None:
        """Validates that at least one of 'top_text' or 'bottom_text' is provided and not empty.

        Raises:
            ValueError: If both 'top_text' and 'bottom_text' are None or empty.
        """
        if not (self.top_text or self.bottom_text):
            error_message = (
                "At least one of 'top_text' or 'bottom_text' must be provided and not empty."
            )
            raise MemeGenerationError(error_message)


def load_image(file_path: Path | str) -> Image.Image:
    """Loads an image from a file.

    Reason for this function to exits is to make the main file not "know" about the PIL library.

    Args:
        file_path (Path): The path to the image file.

    Returns:
        Image.Image: The loaded image.

    Example usage:
    >>> image = load_image("distracted_boyfriend.jpg")
    """
    return Image.open(file_path)


def create_meme(
    image: Image.Image,
    meme_text: MemeText,
    text_configuration: TextConfiguration,
) -> Image.Image:
    # TODO(Mateusz): consider if both text configuration and confiuguraiton
    """Creates a meme by adding text to an image.

    This is a top level function to be used in meme main file.

    Args:
        image (Image.Image): The image to which the meme text will be added.
        meme_text (MemeText): An object containing the top and bottom text for the meme,
        as well as the font.
        text_configuration (TextConfiguration): Configuration for the text,
        including font path and margins.
        configuration (settings.Configuration): The configuration object
        containing global configuration

    Returns:
        Image.Image: The image with the meme text added.

    Example:
        >>> from PIL import Image
        >>> image = load_image("../memer-resources/distracted_boyfriend.jpg")
        >>> meme_text = MemeText(top_text="Me", bottom_text="New project idea | Current project")
        >>> text_configuration = configuration.text
        >>> meme = create_meme(image, meme_text, text_configuration)
        >>> meme.save("../memer-resources/distracted_boyfriend_with_text_top_level.jpg")

    """
    font = meme_text.font
    if font is None:
        font_size_candidates: list[int] = []
        if meme_text.top_text is not None:
            font_size_candidates.append(
                _determine_font_size(
                    image=image,
                    text=meme_text.top_text,
                    font_path=text_configuration.font.font_path,
                    text_configuration=text_configuration,
                )
            )
        if meme_text.bottom_text is not None:
            font_size_candidates.append(
                _determine_font_size(
                    image=image,
                    text=meme_text.bottom_text,
                    font_path=text_configuration.font.font_path,
                    text_configuration=text_configuration,
                )
            )
        logger.debug("Font size candidates: %s", font_size_candidates)

        font_size = min(font_size_candidates)

        logger.debug("Selected font size: %s", font_size)

        font = ImageFont.truetype(text_configuration.font.font_path, font_size)
    return _add_text_to_image(
        image=image,
        font=font,
        top_text=meme_text.top_text,
        bottom_text=meme_text.bottom_text,
        margins=text_configuration.margins,
    )


def _add_text_to_image(
    image: Image.Image,
    font: ImageFont.FreeTypeFont,
    top_text: str | None,
    bottom_text: str | None,
    margins: MarginsConfiguration,
) -> Image.Image:
    """Adds text to the top and bottom of an image.

    Args:
        image (Image.Image): The image to which text will be added.
        font (ImageFont.FreeTypeFont): The font to be used for the text.
        top_text (str | None): The text to be added at the top of the image.
        If None, no text is added at the top.
        bottom_text (str | None): The text to be added at the bottom of the image.
        If None, no text is added at the bottom.
        margins (MarginsConfiguration): Configuration for the margins around the text.

    Returns:
        Image.Image: The image with the added text.

            Example usage:
    >>> image = Image.open("distracted_boyfriend.jpg")
    >>> font = ImageFont.truetype("impact.ttf", 40)
    >>> image_with_text = add_text_to_image(image, font, "Me", "New project idea | Current project")
    >>> image_with_text.show()
    """
    draw = ImageDraw.Draw(image)

    # Add text to image
    if top_text is not None:
        # Calculate text size and position for top text
        top_text_width, _ = _get_text_size(text=top_text, font=font)
        top_text_position = ((image.width - top_text_width) / 2, margins.vertical)

        draw.text(  # type: ignore Ignoring return type of draw.text
            top_text_position,
            top_text,
            font=font,
            fill="white",
            stroke_width=2,
            stroke_fill="black",
        )
    if bottom_text is not None:
        # Calculate text size and position for bottom text
        bottom_text_width, bottom_text_height = _get_text_size(text=bottom_text, font=font)
        bottom_text_position = (
            (image.width - bottom_text_width) / 2,
            image.height - bottom_text_height - margins.vertical,
        )
        draw.text(  # type: ignore Ignoring return type of draw.text
            bottom_text_position,
            bottom_text,
            font=font,
            fill="white",
            stroke_width=2,
            stroke_fill="black",
        )

    return image


def _get_text_size(text: str, font: ImageFont.FreeTypeFont) -> tuple[float | int, float | int]:
    """Calculates the width and height of a line of text.

    It is actually not obvoius how to calculate text heigh.
    Fortunatley, there is article:
    "How to properly calculate text size in PIL images" by José Fernando Costa
    https://levelup.gitconnected.com/how-to-properly-calculate-text-size-in-pil-images-17a2cc6f51fd

    Args:
        text (str): The text string to be measured.
        font (ImageFont.FreeTypeFont): The font used to render the text.

    Returns:
        tuple[int, int]: A tuple containing the width and height of the text.
    """
    _, descent = font.getmetrics()

    # Type of "getmask" is partially unknown
    width: float | int | Any = font.getmask(text=text).getbbox()[2]  # type: ignore[no-untyped-call]
    height: float | int | Any = font.getmask(text=text).getbbox()[3] + descent  # type: ignore[no-untyped-call]
    if not isinstance(width, float | int) or not isinstance(height, float | int):
        message = (
            "Both width and height should be floats. "
            "Width is %s and has type %s and height is %s and has type %s"
        )
        raise MemeGenerationError(message % (width, type(width), height, type(height)))  # type: ignore[arg-type]
    return width, height


def _line_fits(text: str, font: ImageFont.FreeTypeFont, max_width: int, max_height: int) -> bool:
    """Determines if a given text fits within specified width and height.

    Args:
        text (str): The text string to be measured.
        font (ImageFont.FreeTypeFont): The font used to render the text.
        max_width (int): The maximum allowable width for the text.
        max_height (int): The maximum allowable height for the text.

    Returns:
        bool: True if the text fits within both the specified width and height, False otherwise.
    """
    text_width, text_height = _get_text_size(text, font)
    width_fits = text_width <= max_width

    height_fits = text_height < max_height

    logger.debug(
        "Font size: %s, text width: %s, max width: %s, text height: %s, max height: %s",
        font.size,
        text_width,
        max_width,
        text_height,
        max_height,
    )

    return width_fits and height_fits


def _determine_font_size(
    image: Image.Image,
    text: str,
    font_path: str | Path,
    text_configuration: TextConfiguration,
) -> int:
    """Guesses the font size that will fit the text in the image.

    TODO(Mateusz): maybe add support for line breaking?
    """
    font_size = 1  # font size is the text hight
    font = ImageFont.truetype(font_path, font_size)
    max_width = image.width - 2 * text_configuration.margins.horizontal
    max_height = round(image.height * text_configuration.max_text_to_height_ratio)

    # initial check:
    if not _line_fits(
        text=text,
        font=font,
        max_width=max_width,
        max_height=max_height,
    ):
        error_message = (
            "No font size matched for meme."
            "Hint: try max_text_to_height_ratio or decreasing margins."
        )
        raise MemeGenerationError(error_message)
    # TODO(Mateusz): this search could be more clever
    while _line_fits(
        text=text,
        font=font,
        max_width=max_width,
        max_height=max_height,
    ):
        font_size += 1
        font = ImageFont.truetype(font_path, font_size)
    return font_size - 1


def generate_meme_name(template_stem: str) -> Path:
    """Generates a meme name based on the template name and the current date.

    Args:
        template_stem (str): The name of the template file.

    Returns:
        str: A meme name based on the template name and the current date.
    """
    local_nondst_tz = time.tzname[0]
    current_time = datetime.now(tz=pytz.timezone(local_nondst_tz)).strftime(
        format="%Y-%m-%d_%H-%M-%S"
    )

    return Path.cwd() / f"{template_stem}_{current_time}.png"


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
