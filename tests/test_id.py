from baygon.id import Id, TrackId


def test_id():
    # Create an Id from a string representation
    i = Id("1.2.3.4")

    # Check the string representation
    assert str(i) == "1.2.3.4"

    # Check the tuple representation
    assert tuple(i) == (1, 2, 3, 4)

    # Check the list representation
    assert list(i) == [1, 2, 3, 4]


def test_trackid():
    # Initialize TrackId object
    t = TrackId()

    # Go down one level in the hierarchy
    t.down()
    assert str(t._id) == "1"

    # Go down again, should still be "1" since it's just initializing
    t.down()
    assert str(t._id) == "1"

    # Go down with a return value and ensure the ID updates correctly
    u = t.down()(42)
    assert str(t._id) == "1.1"
    assert u == 42  # The returned value should match the passed argument

    # Increment the ID, next() should move to "1.2" and return the correct test_id
    u = t.next()({})
    assert str(t._id) == "1.2"
    assert u == {"test_id": [1, 1]}  # Ensure correct test_id in the dictionary

    # Increment again, ID should be "1.3"
    u = t.next()({})
    assert str(t._id) == "1.3"
    assert u == {"test_id": [1, 2]}  # test_id increments accordingly

    # Go down another level, ID should now be "1.3.1"
    t.down()()
    assert str(t._id) == "1.3.1"

    # Go back up a level, ID should revert to "1.3"
    t.up()()
    assert str(t._id) == "1.3"

    # Increment again, ID should move to "1.4"
    t.next()({})
    assert str(t._id) == "1.4"

    # Go down another level, ID should be "1.4.1"
    t.down()()
    assert str(t._id) == "1.4.1"

    # Reset the ID, should return to the root "1"
    t.reset()()
    assert str(t._id) == "1"
