import baygon.matchers


def test_equals():

    assert baygon.matchers.MatchEquals(42)(42) is None

    assert isinstance(
        baygon.matchers.MatchEquals(42)(43), baygon.matchers.InvalidEquals
    )


def test_contains():
    assert baygon.matchers.MatchContains("foo")("i am foobar") is None

    assert isinstance(
        baygon.matchers.MatchContains("baz")("i am foobar"),
        baygon.matchers.InvalidContains,
    )


def test_regex():
    assert baygon.matchers.MatchRegex(r"fo{2,}")("i am foobar") is None

    assert isinstance(
        baygon.matchers.MatchRegex(r"fa{2,}")("i am foobar"),
        baygon.matchers.InvalidRegex,
    )
