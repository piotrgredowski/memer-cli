"""Input validation and security utilities."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from memer.core.exceptions import ValidationError


def validate_file_path(path: str | Path, must_exist: bool = True) -> Path:
    """Validate and sanitize a file path.
    
    Args:
        path: The file path to validate.
        must_exist: Whether the file must exist.
        
    Returns:
        Validated Path object.
        
    Raises:
        ValidationError: If the path is invalid or unsafe.
    """
    # Security check: prevent path traversal attacks before resolution
    if ".." in str(path) or str(path).startswith("/etc") or str(path).startswith("/proc"):
        raise ValidationError(f"Unsafe file path: {path}")

    try:
        file_path = Path(path).resolve()
    except (OSError, ValueError) as e:
        raise ValidationError(f"Invalid file path: {path}") from e

    if must_exist and not file_path.exists():
        raise ValidationError(f"File does not exist: {path}")

    return file_path


def validate_template_name(name: str) -> str:
    """Validate a template name.
    
    Args:
        name: The template name to validate.
        
    Returns:
        Validated template name.
        
    Raises:
        ValidationError: If the name is invalid.
    """
    if not name or not name.strip():
        raise ValidationError("Template name cannot be empty")

    name = name.strip()

    # Check for reasonable length
    if len(name) > 255:
        raise ValidationError("Template name too long (max 255 characters)")

    # Check for invalid characters (basic safety)
    if re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
        raise ValidationError("Template name contains invalid characters")

    return name


def validate_url(url: str) -> str:
    """Validate a URL.
    
    Args:
        url: The URL to validate.
        
    Returns:
        Validated URL.
        
    Raises:
        ValidationError: If the URL is invalid.
    """
    if not url or not url.strip():
        raise ValidationError("URL cannot be empty")

    url = url.strip()

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {url}") from e

    if not parsed.scheme or not parsed.netloc:
        raise ValidationError(f"Invalid URL format: {url}")

    if parsed.scheme not in ("http", "https"):
        raise ValidationError(f"Unsupported URL scheme: {parsed.scheme}")

    return url


def validate_text_input(text: str, max_length: int = 1000) -> str:
    """Validate text input for meme generation.
    
    Args:
        text: The text to validate.
        max_length: Maximum allowed length.
        
    Returns:
        Validated text.
        
    Raises:
        ValidationError: If the text is invalid.
    """
    if text is None:
        return ""

    if len(text) > max_length:
        raise ValidationError(f"Text too long (max {max_length} characters)")

    # Remove any control characters except newlines and tabs
    cleaned = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)

    return cleaned


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe file system usage.
    
    Args:
        filename: The filename to sanitize.
        
    Returns:
        Sanitized filename.
    """
    if not filename:
        return "untitled"

    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(" .")

    # Ensure it's not empty after sanitization
    if not sanitized:
        return "untitled"

    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]

    return sanitized


def validate_configuration_dict(config: dict[str, Any]) -> dict[str, Any]:
    """Validate configuration dictionary for security issues.
    
    Args:
        config: Configuration dictionary to validate.
        
    Returns:
        Validated configuration.
        
    Raises:
        ValidationError: If the configuration contains security issues.
    """
    # Check for suspicious keys that might indicate code injection
    suspicious_keys = {"__import__", "__builtins__", "exec", "eval", "compile"}

    def check_dict(d: dict[str, Any], path: str = "") -> None:
        for key, value in d.items():
            current_path = f"{path}.{key}" if path else key

            if key in suspicious_keys:
                raise ValidationError(f"Suspicious configuration key: {current_path}")

            if isinstance(value, dict):
                check_dict(value, current_path)
            elif isinstance(value, str) and any(sus in value for sus in suspicious_keys):
                raise ValidationError(f"Suspicious configuration value at: {current_path}")

    check_dict(config)
    return config
