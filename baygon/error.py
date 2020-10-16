class InvalidCondition:
    def __init__(self, got, expected, message=None, on=None):
        self.got = got
        self.expected = expected
        self.message = message
        self.on = on

    def __str__(self):
        return f'Expected "{self.expected}", but got "{self.got}"'


class InvalidExitStatus(InvalidCondition):
    def __str__(self):
        if hasattr(self.got, '__len__') and len(self.got) > 20:
            return f'Invalid exit status. Expected {self.expected}'
        else:
            return f'Invalid exit status. Expected {self.expected}, but got {self.got}'


class InvalidContains(InvalidCondition):
    pass


class InvalidRegex(InvalidCondition):
    def __str__(self):
        return f'Invalid value on {self.on}. Expected to match regex /{self.expected}/'


class InvalidEquals(InvalidCondition):
    def __str__(self):
        if hasattr(self.got, '__len__') and len(self.got) > 20:
            return f'Invalid value on {self.on}. Expected exactly "{self.expected}"'
        else:
            return f'Invalid value on {self.on}. Expected exactly "{self.expected}", but got "{self.got}"'

