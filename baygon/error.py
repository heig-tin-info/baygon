""" Errors for Baygon """


class BaygonError(Exception):
    """ Base class for Baygon errors """
    pass


class ConfigError(BaygonError):
    """ Raised when a config value is not valid """
    pass


class InvalidExecutableError(BaygonError):
    """ Raised when an executable is not found """
    pass


class InvalidFilterError(BaygonError):
    """ Raised when a filter is not found """
    pass


class InvalidCondition:
    """ Invalid condition error. """

    def __init__(self, value, expected, message=None, on=None, **kwargs):
        self.value = value
        self.expected = expected
        self.message = message
        self.name = kwargs.get('name', '')
        self.id = kwargs.get('id', None)
        self.on = on

    def __str__(self):
        return f'Expected "{self.expected}", but got "{self.value}"'


class InvalidExitStatus(InvalidCondition):
    """ Invalid exit status error. """

    def __str__(self):
        if hasattr(self.value, '__len__') and len(self.value) > 20:
            return f'Invalid exit status. Expected {self.expected}'

        return (f'Invalid exit status. '
                f'Expected {self.expected}, but got {self.value}')


class InvalidContains(InvalidCondition):
    """ Invalid contains error. """


class InvalidRegex(InvalidCondition):
    """ Invalid regex error. """

    def __str__(self):
        return (f'Invalid value on {self.on}. '
                f'Expected to match regex /{self.expected}/')


class InvalidEquals(InvalidCondition):
    """ Invalid equals error. """

    def __str__(self):
        if hasattr(self.value, '__len__') and len(self.value) > 20:
            return (f'Invalid value on {self.on}. '
                    f'Expected exactly "{self.expected}"')

        return (f'Invalid value on {self.on}. '
                f'Expected exactly "{self.expected}", '
                f'but got "{self.value}"')
