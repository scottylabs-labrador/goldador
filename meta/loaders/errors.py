"""Exceptions raised when governance TOML cannot be loaded."""


class GovernanceLoadError(Exception):
    """Raised when a member or team TOML file cannot be parsed or validated."""

    def __init__(self, file_path: str, message: str) -> None:
        """Store the failing file path and a human-readable error message."""
        super().__init__(f"{file_path}: {message}")
        self.file_path = file_path
        self.message = message
