class InvalidCondition:
    def __init__(self, value, expected, message=None, on=None):
        self.value = value
        self.expected = expected
        self.message = message
        self.on = on

    def __str__(self):
        return f'Expected "{self.expected}", but got "{self.value}"'


class InvalidExitStatus(InvalidCondition):
    def __str__(self):
        if hasattr(self.value, '__len__') and len(self.value) > 20:
            return f'Invalid exit status. Expected {self.expected}'
        else:
            return f'Invalid exit status. Expected {self.expected}, but got {self.value}'


class InvalidContains(InvalidCondition):
    pass


class InvalidRegex(InvalidCondition):
    def __str__(self):
        return f'Invalid value on {self.on}. Expected to match regex /{self.expected}/'


class InvalidEquals(InvalidCondition):
    def __str__(self):
        if hasattr(self.value, '__len__') and len(self.value) > 20:
            return f'Invalid value on {self.on}. '
            'Expected exactly "{self.expected}"'
        else:
            return f'Invalid value on {self.on}. '
            f'Expected exactly "{self.expected}",'
            f' but got "{self.value}"'
