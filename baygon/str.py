import re


class GreppableString(str):
    """ A string that can be parsed with regular expressions. """

    def grep(self, pattern: str, *args) -> bool:
        """ Return True if the pattern is found in the string. """
        return re.findall(pattern, self, *args)

    def contains(self, value: str) -> bool:
        """ Return True if the value is found in the string. """
        return value in self
