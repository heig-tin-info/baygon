""" String filters. """


def apply_filters(value: str, filters: dict = None) -> str:
    """ Apply global filters before tests. """

    for f in filters or {}:
        if f == 'uppercase':
            value = value.upper()
        elif f == 'lowercase':
            value = value.lower()
        elif f == 'trim':
            value = value.strip()
        elif f in ['ignorespaces', 'ignore-spaces']:
            value = value.replace(' ', '')
        elif f == 'regex':
            value = re.sub(filters['regex'][0], filters['regex'][1], value)
        elif f == 'replace':
            value = value.replace(
                filters['replace'][0], filters['replace'][1])

    return value
