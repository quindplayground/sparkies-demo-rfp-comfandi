import pytest

from template_project.libs.iceberg.cdc_with_tagging_strategy.exceptions import (
    SnapshotManagerException,
    ChangelogManagerException,
    IncrementalExtractException,
    InvalidTableFormatError,
    CommitChangesError,
)
from template_project.libs.exceptions import BaseProjectException


def test_snapshot_manager_exception():
    """Test SnapshotManagerException can be instantiated and inherits from BaseProjectException."""
    exception = SnapshotManagerException("Test error message")

    assert str(exception) == "Test error message"
    assert isinstance(exception, Exception)
    assert isinstance(exception, BaseProjectException)


def test_snapshot_manager_exception_empty_message():
    """Test SnapshotManagerException with empty message."""
    exception = SnapshotManagerException("")

    assert str(exception) == ""
    assert isinstance(exception, SnapshotManagerException)


def test_changelog_manager_exception():
    """Test ChangelogManagerException can be instantiated and inherits from BaseProjectException."""
    exception = ChangelogManagerException("Test error message")

    assert str(exception) == "Test error message"
    assert isinstance(exception, Exception)
    assert isinstance(exception, BaseProjectException)


def test_changelog_manager_exception_empty_message():
    """Test ChangelogManagerException with empty message."""
    exception = ChangelogManagerException("")

    assert str(exception) == ""
    assert isinstance(exception, ChangelogManagerException)


def test_incremental_extract_exception():
    """Test IncrementalExtractException can be instantiated and inherits from BaseProjectException."""
    exception = IncrementalExtractException("Test error message")

    assert str(exception) == "Test error message"
    assert isinstance(exception, Exception)
    assert isinstance(exception, BaseProjectException)


def test_incremental_extract_exception_empty_message():
    """Test IncrementalExtractException with empty message."""
    exception = IncrementalExtractException("")

    assert str(exception) == ""
    assert isinstance(exception, IncrementalExtractException)


def test_invalid_table_format_error():
    """Test InvalidTableFormatError can be instantiated and inherits from BaseProjectException."""
    exception = InvalidTableFormatError("Test error message")

    assert str(exception) == "Test error message"
    assert isinstance(exception, Exception)
    assert isinstance(exception, BaseProjectException)


def test_invalid_table_format_error_empty_message():
    """Test InvalidTableFormatError with empty message."""
    exception = InvalidTableFormatError("")

    assert str(exception) == ""
    assert isinstance(exception, InvalidTableFormatError)


def test_commit_changes_error():
    """Test CommitChangesError can be instantiated and inherits from BaseProjectException."""
    exception = CommitChangesError("Test error message")

    assert str(exception) == "Test error message"
    assert isinstance(exception, Exception)
    assert isinstance(exception, BaseProjectException)


def test_commit_changes_error_empty_message():
    """Test CommitChangesError with empty message."""
    exception = CommitChangesError("")

    assert str(exception) == ""
    assert isinstance(exception, CommitChangesError)


def test_exceptions_inheritance_chain():
    """Test that all custom exceptions properly inherit from BaseProjectException."""
    exceptions = [
        SnapshotManagerException("test"),
        ChangelogManagerException("test"),
        IncrementalExtractException("test"),
        InvalidTableFormatError("test"),
        CommitChangesError("test"),
    ]

    for exception in exceptions:
        assert isinstance(exception, BaseProjectException)
        assert isinstance(exception, Exception)


def test_exceptions_can_be_raised():
    """Test that all custom exceptions can be raised and caught."""
    exceptions_to_test = [
        SnapshotManagerException,
        ChangelogManagerException,
        IncrementalExtractException,
        InvalidTableFormatError,
        CommitChangesError,
    ]

    for exception_class in exceptions_to_test:
        with pytest.raises(exception_class) as exc_info:
            raise exception_class("Test error")

        assert str(exc_info.value) == "Test error"
