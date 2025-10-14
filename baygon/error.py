"""Errors for Baygon"""


class BaygonError(Exception):
    """Base class for Baygon errors"""


class ConfigError(BaygonError):
    """Raised when a config value is not valid"""


class InvalidExecutableError(BaygonError):
    """Raised when an executable is not found"""


class InvalidFilterError(BaygonError):
    """Raised when a filter is not found"""


class ConfigSyntaxError(ConfigError):
    """Raised when the configuration file cannot be parsed."""

    def __init__(self, message: str, *, line: int | None = None, column: int | None = None):
        if line is not None and column is not None:
            message = f"{message} (line {line}, column {column})"
        super().__init__(message)
        self.line = line
        self.column = column
