from template_project.libs.exceptions import BaseProjectException


class SnapshotManagerException(BaseProjectException):
    """Exception raised when an error occurs in the SnapshotManager."""

    pass


class ChangelogManagerException(BaseProjectException):
    """Exception raised when an error occurs in the ChangelogManager."""

    pass


class IncrementalExtractException(BaseProjectException):
    """Exception raised when an error occurs during incremental extraction."""

    pass


class InvalidTableFormatError(BaseProjectException):
    """Exception raised when an invalid table format is encountered."""

    pass


class CommitChangesError(BaseProjectException):
    """Exception raised when an error occurs while committing changes."""

    pass
