import hashlib
import logging
from functools import cached_property
from pathlib import Path
from typing import Annotated
from typing import Any
from typing import Self
from typing import TypeVar

import yaml
from annotated_types import Gt
from platformdirs import user_config_dir
from platformdirs import user_data_dir
from pydantic import BaseModel
from pydantic import PlainSerializer

from .helper_methods import convert_string_to_nice_name
from .memer_exceptions import ConfigurationValidationError
from .memer_exceptions import MissingConfigurationError

logger = logging.getLogger(__name__)
# TODO(Mateusz): this should probably go to setup.py?
APP_NAME = "memer"

# TODO(Mateusz): this file should be renamed to default_templates.yaml
DEFAULT_MEMES_PATH = Path(__file__).parent.parent / "config" / "default_memes.yaml"

DEFAULT_CONFIGURATION_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "default_configuration.yaml"
)
DEFAULT_FONT_PATH: Path = Path(__file__).resolve().parent.parent / "font"

StringSerializedPath = Annotated[Path, PlainSerializer(lambda x: str(x), return_type=str)]


# DEFAULT MEMES CLASSES
class TemplateToPull(BaseModel):
    """MemeToPull is a model representing a meme to be pulled.

    Attributes:
        name (str | None): The name of the meme. It can be None if the name is not provided.
        url (str): The URL of the meme.
    """

    name: str | None
    # TODO(Mateusz): maybe HttpUrl is type?
    url: str

    # Oveload eq, ne, hash to create template sets
    def __eq__(self: Self, other: object) -> bool:
        """Compare 2 instances of this class based on .name and .url properties."""
        if isinstance(other, TemplateToPull):
            return (self.name, self.url) == (other.name, other.url)
        return False  # Objects of different types are not equal

    def __ne__(self: Self, other: object) -> bool:
        """Compare 2 instances of this class based on .name and .url properties."""
        return not self.__eq__(other)

    def __hash__(self: Self) -> int:
        """Compute the hash of the object."""
        return hash((self.name, self.url))


class ToPullTemplates(BaseModel):
    """DefaultTemplateList is a model that represents a list of meme templates.

    Attributes:
        templates (list[MemeToPull]): A list of MemeToPull objects representing the meme templates.
    """

    templates: list[TemplateToPull]


# DEFAULT SETTINGS CLASSES
class MarginsConfiguration(BaseModel):
    """Margins class represents the vertical and horizontal margins.

    Attributes:
        vertical (int): The vertical margin in pixels.
        horizontal (int): The horizontal margin in pixels.
    """

    vertical: int
    horizontal: int


class FontConfiguration(BaseModel):
    """FontConfiguration is a class that represents the configuration for a font.

    It includes fonts name, search paths, and file extension.

    Attributes:
        name (str): The name of the font. It can include (but does not have to) the file extension.
        search_paths (set[Path]): A list of paths to search for the font file.
        extension (str): The file extension of the font. Can be None

    Methods:
        _get_full_font_path(search_path: Path) -> Path:
            Constructs the full path to the font file based on the search path and font name.
        _font_exists(search_path: Path) -> bool:
            Checks if the font file exists in the given search path.
        font_path() -> Path:
            Property that computes and returns the full path to the font file if it exists
            in any of the search paths.
            Raises FileNotFoundError if the font file is not found in any of the search paths.
    """

    name: str
    search_paths: set[StringSerializedPath] = set()
    extension: str | None = None

    def _get_full_font_path(self, search_path: Path) -> Path:
        # Case: font name includes the extension
        if self.extension is not None and self.name.endswith(self.extension):
            return search_path / self.name

        # Case: font name does not include the extension
        if self.extension is not None and not self.name.endswith(self.extension):
            # Check if the extension includes the dot
            if self.extension.startswith("."):
                return search_path / f"{self.name}{self.extension}"
            return search_path / f"{self.name}.{self.extension}"
        # Case: extension is None, but no extension in the font name
        # (which still could be a valid font path)
        return search_path / self.name

    def _font_exists(self, search_path: Path) -> bool:
        font_path = self._get_full_font_path(search_path=search_path)
        return font_path.exists()

    @cached_property
    def font_path(self) -> Path:
        """Cached property for computed font path.

        This property will search for the font file in the search paths and return the full path.
        It will perform the search in the order from the settings.

        Returns:
            Path: The full path to the font if it exists in one of the search paths.

        Raises:
            ConfigurationValidationError: If the font is not found in any of the search paths.
        """
        # First try the built in path
        if self._font_exists(DEFAULT_FONT_PATH):
            return self._get_full_font_path(search_path=DEFAULT_FONT_PATH)

        # Then try the search paths
        for path in self.search_paths:
            if self._font_exists(path):
                return self._get_full_font_path(search_path=path)

        error_message = f"Default font not found in any of the search paths. Looked at: {
            DEFAULT_FONT_PATH} and at {self.search_paths}"
        raise ConfigurationValidationError(error_message)


class TextConfiguration(BaseModel):
    """Text class represents the text configuration.

    Attributes:
        max_text_to_height_ratio (float): The maximum text to height ratio.
        margins (Margins): An instance of the Margins class representing the margins configuration.
    """

    max_text_to_height_ratio: float
    margins: MarginsConfiguration
    font: FontConfiguration


class Template(BaseModel):
    """Template class representing a template file with a path.

    Attributes:
        path (Path): The file path of the template.

    Properties:
        name (str): A computed property that returns a nicely formatted name
        derived from the file stem.
        key (str): A computed property that returns a SHA-256 hash of the file path,
        which remains consistent if the path does not change.
    """

    # TODO(Mateusz): think about it. Should it even be pydantic base class?
    path: StringSerializedPath

    @cached_property
    def name(self) -> str:
        """A user-friendly name from the file stem of the path.

        Returns:
            str: A user-friendly name derived from the file stem.
        """
        return convert_string_to_nice_name(source_name=self.path.stem)

    @cached_property
    def key(self) -> str:
        # TODO(Mateusz): do we even need it?
        """Property will stay the same if the path did not change.

        Generates a SHA-256 hash of the file path.

        Returns:
            str: A SHA-256 hash of the file path.
        """
        # Maybe we should make it shorter?
        return hashlib.sha256(str(self.path).encode()).hexdigest()

    @cached_property
    def stem(self) -> str:
        """The file stem of the path.

        Returns:
            str: The file stem of the path.
        """
        return self.path.stem


class TemplatesConfiguration(BaseModel):
    """TemplatesConfiguration is a configuration class for managing template discovery.

    Attributes:
        extensions (list[str]): A list of file extensions to search for templates.
        search_paths (list[Path]): A list of paths to search for template files.

    Methods:
        discovered_templates() -> dict[str, Template]:
            Property with templates that are discovered from the search paths and extensions.
    """

    extensions: list[str]
    search_paths: set[StringSerializedPath] = set()

    @cached_property
    def discovered_templates(self) -> dict[str, Template]:
        """Property with templates that are discovered from the search paths and extensions.

        Discovers and loads templates from the specified search paths and extensions.
        This method iterates over the configured search paths and file extensions,
        creating a Template object for each discovered file and storing it in a dictionary
        with the template's key as the dictionary key.

        Returns:
            dict[str, Template]: A dictionary where the keys are template names and the values
            are Template objects.
        """
        templates: dict[str, Template] = {}
        # TODO(Mateusz): refactor this to maybe use a generator. Also too much nesting
        # This is really tought to understad
        for path in self.search_paths:
            # Case that path is a file already
            if path.is_file():
                template = Template(path=path)
                if template.name in templates:
                    logger.warning(
                        "Template name clash: %s and %s have the same name %s."
                        "Proceeding with %s.",
                        templates[template.name].path,
                        template.path,
                        template.name,
                        templates[template.name].path,
                    )
                    continue
                templates[template.name] = template
            else:
                for extension in self.extensions:
                    for file_path in path.glob(f"*.{extension}"):
                        template = Template(path=file_path.resolve())
                        # TODO(Mateusz): raise warning in case of clash
                        if template.name in templates:
                            logger.warning(
                                "Template name clash: %s and %s have the same name %s."
                                "Proceeding with %s.",
                                templates[template.name].path,
                                template.path,
                                template.name,
                                templates[template.name].path,
                            )
                            continue

                        templates[template.name] = template
        return templates


class RemoteConfiguration(BaseModel):
    """Configuration for downloading remote templates.

    Attributes:
        timeout (int): The timeout value for the remote connection. Must be greater than 0.
    """

    timeout: Annotated[int, Gt(0)]
    verify_ssl: bool


class ImagesConfiguration(BaseModel):
    """ImagesConfiguration is a configuration class for image-related settings.

    Attributes:
        templates (TemplatesConfiguration): Configuration for templates.
    """

    templates: TemplatesConfiguration
    remote: RemoteConfiguration


class TyperConfiguration(BaseModel):
    """TyperConfiguration is a configuration class for Typer.

    Attributes:
        no_args_is_help (bool): If True, the application will display the help message
        when no arguments are provided.
    """

    no_arg_is_help: bool


class InterfaceConfiguration(BaseModel):
    """InterfaceConfiguration is a model that holds the configuration settings for the interface.

    Attributes:
        typer (TyperConfiguration): Configuration settings for the typer.
    """

    typer: TyperConfiguration


class Configuration(BaseModel):
    """Configuration class that inherits from BaseModel.

    Attributes:
        text (Text): An instance of the Text class representing the text configuration.
    """

    text: TextConfiguration
    images: ImagesConfiguration
    interface: InterfaceConfiguration


# SETTINGS FUNCTIONS ###
# TODO(Mateusz): figure out how to correctly pass the type of the model
# AnyMemerModel = TypeVar("AnyMemerModel", type[Configuration], type[DefaultMemes])  # noqa: ERA001


def _log_yaml(dictionary: dict[str, Any]) -> None:
    config_yaml = yaml.dump(dictionary, default_flow_style=False)
    logger.debug("YAML configuration:\n%s", config_yaml)


def _log_object(memer_model: BaseModel) -> None:
    logger.debug("Model: %s", memer_model.model_dump_json(indent=4))


ModelType = TypeVar("ModelType", bound=BaseModel)


def _load_from_file(
    file_path: Path,
    target_class: type[ModelType],
    *,
    debug_log_on_load: bool = True,
) -> ModelType:
    try:
        with file_path.open() as file:
            config_data = yaml.safe_load(stream=file)
            if debug_log_on_load:
                _log_yaml(dictionary=config_data)
            memer_model = target_class(**config_data)
            if debug_log_on_load:
                _log_object(memer_model=memer_model)
            return memer_model
    except FileNotFoundError:
        message = f"Configuration file not found: {file_path}"
        raise MissingConfigurationError(message) from FileNotFoundError


def _dump_configuration_to_file(configuration: Configuration, file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w") as file:
        yaml.dump(configuration.model_dump(), file)


def get_config_path() -> Path:
    """Returns the path to the configuration file.

    This function constructs the path to the configuration file by using the
    user configuration directory for the application and appending "config.yaml"
    to it.

    Returns:
        Path: The full path to the configuration file.
    """
    return (Path(user_config_dir(appname=APP_NAME)) / "config.yaml").resolve()


def load_configuration(config_path: Path | None = None) -> Configuration:
    """Loads the configuration from a file.

    If the configuration file is not found, it generates one from default settings and saves it.

    Returns:
        Configuration: The loaded or default configuration object.

    Raises:
        MissingConfigurationError: If the configuration file is missing and cannot be generated.
    """
    if config_path is None:
        config_path = get_config_path()
    try:
        logger.debug("Loading configuration from %s", config_path)

        return _load_from_file(file_path=config_path, target_class=Configuration)

    except MissingConfigurationError:
        logger.info(
            "Configuration file not found under %s. Generating one from defaults",
            config_path,
        )
        default_configuration = _load_from_file(
            file_path=DEFAULT_CONFIGURATION_PATH, target_class=Configuration
        )
        dump_configuration(configuration=default_configuration)
        return default_configuration


def dump_configuration(configuration: Configuration) -> None:
    """Dumps the given configuration to a file.

    Args:
        configuration (Configuration): The configuration object to be dumped.
    """
    # TODO(Mateusz): how to handle different versions?
    # Maybe we should have a version field in the configuration.
    # user_config_dir also can support version field
    config_path = get_config_path()
    _dump_configuration_to_file(configuration=configuration, file_path=config_path)


def load_default_template_list(
    file_path: Path = DEFAULT_MEMES_PATH,
) -> list[TemplateToPull]:
    """Loads the default memes from a file.

    Returns:
        DefaultMemes: The loaded default memes object.
    """
    return _load_from_file(file_path=file_path, target_class=ToPullTemplates).templates


def get_user_data_templates_path() -> Path:
    """Returns the resolved path to the user's data templates directory.

    This function constructs the path to the "templates" directory within the
    user's data directory for the application specified by APP_NAME.

    Returns:
        Path: The resolved path to the "templates" directory.
    """
    return Path(user_data_dir(appname=APP_NAME)).resolve() / "templates"


# Global configuration is now managed through dependency injection
# See memer.core.container for the new approach
