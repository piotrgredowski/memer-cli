"""Tests for validation utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from memer.core.exceptions import ValidationError
from memer.core.validation import sanitize_filename
from memer.core.validation import validate_file_path
from memer.core.validation import validate_template_name
from memer.core.validation import validate_text_input
from memer.core.validation import validate_url


def test_validate_file_path_valid(temp_dir: Path) -> None:
    """Test validation of valid file path."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test")

    result = validate_file_path(test_file)
    assert result == test_file.resolve()


def test_validate_file_path_nonexistent_when_required() -> None:
    """Test validation fails for nonexistent path when required."""
    with pytest.raises(ValidationError, match="File does not exist"):
        validate_file_path("/nonexistent/path.txt")


def test_validate_file_path_nonexistent_when_not_required() -> None:
    """Test validation passes for nonexistent path when not required."""
    result = validate_file_path("/some/path.txt", must_exist=False)
    assert isinstance(result, Path)


def test_validate_file_path_traversal_attack() -> None:
    """Test validation prevents path traversal attacks."""
    with pytest.raises(ValidationError, match="Unsafe file path"):
        validate_file_path("../../../etc/passwd", must_exist=False)


def test_validate_file_path_system_path_attack() -> None:
    """Test validation prevents access to system paths."""
    with pytest.raises(ValidationError, match="Unsafe file path"):
        validate_file_path("/etc/passwd", must_exist=False)


def test_validate_template_name_valid() -> None:
    """Test validation of valid template name."""
    result = validate_template_name("My Template")
    assert result == "My Template"


def test_validate_template_name_empty() -> None:
    """Test validation fails for empty name."""
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_template_name("")


def test_validate_template_name_whitespace_only() -> None:
    """Test validation fails for whitespace-only name."""
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_template_name("   ")


def test_validate_template_name_too_long() -> None:
    """Test validation fails for overly long name."""
    long_name = "a" * 256
    with pytest.raises(ValidationError, match="too long"):
        validate_template_name(long_name)


def test_validate_template_name_invalid_characters() -> None:
    """Test validation fails for invalid characters."""
    with pytest.raises(ValidationError, match="invalid characters"):
        validate_template_name("template<>name")


def test_validate_url_valid_http() -> None:
    """Test validation of valid HTTP URL."""
    url = "http://example.com/image.jpg"
    result = validate_url(url)
    assert result == url


def test_validate_url_valid_https() -> None:
    """Test validation of valid HTTPS URL."""
    url = "https://example.com/image.jpg"
    result = validate_url(url)
    assert result == url


def test_validate_url_empty() -> None:
    """Test validation fails for empty URL."""
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_url("")


def test_validate_url_invalid_scheme() -> None:
    """Test validation fails for invalid scheme."""
    with pytest.raises(ValidationError, match="Unsupported URL scheme"):
        validate_url("ftp://example.com/file.txt")


def test_validate_url_malformed() -> None:
    """Test validation fails for malformed URL."""
    with pytest.raises(ValidationError, match="Invalid URL format"):
        validate_url("not-a-url")


def test_validate_text_input_valid() -> None:
    """Test validation of valid text."""
    text = "Hello, World!"
    result = validate_text_input(text)
    assert result == text


def test_validate_text_input_none() -> None:
    """Test validation handles None input."""
    result = validate_text_input(None)
    assert result == ""


def test_validate_text_input_too_long() -> None:
    """Test validation fails for overly long text."""
    long_text = "a" * 1001
    with pytest.raises(ValidationError, match="too long"):
        validate_text_input(long_text)


def test_validate_text_input_control_characters_removed() -> None:
    """Test validation removes control characters."""
    text_with_controls = "Hello\x00\x01World"
    result = validate_text_input(text_with_controls)
    assert result == "HelloWorld"


def test_sanitize_filename_valid() -> None:
    """Test sanitization of valid filename."""
    result = sanitize_filename("test_file.txt")
    assert result == "test_file.txt"


def test_sanitize_filename_empty() -> None:
    """Test sanitization of empty filename."""
    result = sanitize_filename("")
    assert result == "untitled"


def test_sanitize_filename_invalid_characters() -> None:
    """Test sanitization removes invalid characters."""
    result = sanitize_filename("test<>file.txt")
    assert result == "test__file.txt"


def test_sanitize_filename_too_long() -> None:
    """Test sanitization truncates long filenames."""
    long_filename = "a" * 300 + ".txt"
    result = sanitize_filename(long_filename)
    assert len(result) <= 255
