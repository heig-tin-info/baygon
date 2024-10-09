"""Errors for Baygon"""


class BaygonError(Exception):
    """Base class for Baygon errors"""


class ConfigError(BaygonError):
    """Raised when a config value is not valid"""


class InvalidExecutableError(BaygonError):
    """Raised when an executable is not found"""


class InvalidFilterError(BaygonError):
    """Raised when a filter is not found"""
