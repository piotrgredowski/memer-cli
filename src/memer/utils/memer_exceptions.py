class MemeGenerationError(Exception):
    """Exception raised when no suitable font size is found for a meme."""


class ConfigurationValidationError(Exception):
    """Exception raised when the configuration is invalid."""


class MissingConfigurationError(Exception):
    """Exception raised when the configuration is missing."""


class RemoteTemplateError(Exception):
    """Exception raised when there is an error with the remote template."""


class TyperCommandGetterError(Exception):
    """Exception raised when there is an error with the Typer command getter utility."""
