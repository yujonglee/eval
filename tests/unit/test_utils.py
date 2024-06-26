import pytest
import inspect

from fastrepl.utils import (
    LocalContext,
    HistoryDict,
    ensure,
    prompt,
    truncate,
    to_number,
    DEBUG,
    map_number_range,
)


class TestLocalContext:
    class TestStack:
        def test_depth_1(self):
            assert inspect.stack()[0].filename == __file__
            assert inspect.stack()[0].function == "test_depth_1"

        def test_depth_2_fn(self):
            def a():
                return inspect.stack()

            assert a()[0].filename == __file__
            assert a()[0].function == "a"
            assert a()[1].filename == __file__
            assert a()[1].function == "test_depth_2_fn"

        def test_depth_2_class(self):
            class B:
                def __init__(self):
                    self.stack = inspect.stack()

            b = B()
            assert b.stack[0].filename == __file__
            assert b.stack[0].function == "__init__"
            assert b.stack[1].filename == __file__
            assert b.stack[1].function == "test_depth_2_class"

        def test_depth3(self):
            class B:
                def __init__(self):
                    self.stack = inspect.stack()

            def c():
                b = B()
                return b.stack

            assert c()[0].filename == __file__
            assert c()[0].function == "__init__"
            assert c()[1].filename == __file__
            assert c()[1].function == "c"
            assert c()[2].filename == __file__

    def test_one_frame(self):
        def fn():
            frame = inspect.stack()[1]
            return LocalContext(frame)

        c0 = fn()

        assert c0 is c0
        assert c0 == c0
        assert c0.__hash__() == c0.__hash__()
        d = {}
        d[c0], d[c0] = 1, 2
        assert len(d) == 1
        assert d[c0] == 2

        assert c0.function == "test_one_frame"

    def test_two_frame(self):
        def fn():
            frame0, frame1 = inspect.stack()[0], inspect.stack()[1]
            return LocalContext(frame0), LocalContext(frame1)

        c0, c1 = fn()

        assert c0 is not c1
        assert c0 != c1
        assert c0.__hash__() != c1.__hash__()
        d = {}
        d[c0], d[c1] = 1, 2
        assert len(d) == 2

        assert c0.function == "fn"
        assert c1.function == "test_two_frame"

    def test_eq(self):
        def fn():
            frame0, frame1 = inspect.stack()[0], inspect.stack()[0]
            return LocalContext(frame0), LocalContext(frame1)

        c0, c1 = fn()
        assert c0 is not c1
        assert c0 == c1

    def test_neq(self):
        def fn():
            frame0, frame1 = inspect.stack()[0], inspect.stack()[1]
            return LocalContext(frame0), LocalContext(frame1)

        c0, c1 = fn()
        assert c0 is not c1
        assert c0 != c1

    def test_hash_eq(self):
        def fn():
            frame0, frame1 = inspect.stack()[0], inspect.stack()[0]
            return LocalContext(frame0), LocalContext(frame1)

        c0, c1 = fn()
        d = {}
        d[c0], d[c1] = 1, 2
        assert len(d) == 1
        assert d[c0] == 2
        assert d[c1] == 2

    def test_hash_neq(self):
        def fn():
            frame0, frame1 = inspect.stack()[0], inspect.stack()[1]
            return LocalContext(frame0), LocalContext(frame1)

        c0, c1 = fn()
        d = {}
        d[c0], d[c1] = 1, 2
        assert len(d) == 2
        assert d[c0] == 1
        assert d[c1] == 2


class TestDataStructure:
    def test_ordered_set(self):
        from fastrepl.utils import OrderedSet

        o = OrderedSet[str]()
        assert len(o) == 0
        assert o.keys() == []

        # TODO: Why no type error
        o.add(1)
        assert len(o) == 1
        assert o.keys() == [1]

        o = OrderedSet[str]()
        assert len(o) == 0
        assert o.keys() == []

        o.add("a")
        o.add("b")
        assert len(o) == 2
        assert o.keys() == ["a", "b"]

        assert "a" in o
        assert "b" in o
        assert "c" not in o

        with pytest.raises(NotImplementedError):
            o == []

    def test_history_dict(self):
        with pytest.raises(NotImplementedError):
            hd = HistoryDict[str](initial="initial")
            assert hd is not None


class TestDecorator:
    def test_ensure(self):
        x = 0

        @ensure(lambda: x == 0)
        def fn1():
            return True

        @ensure(lambda: x != 0)
        def fn2():
            return True

        assert fn1()
        with pytest.raises(AssertionError):
            assert fn2()


class TestPromt:
    def test_basic(self):
        @prompt
        def fn(instruction, examples, question):
            """{{ instruction }}

            {% for example in examples %}
            Q: {{ example.question }}
            A: {{ example.answer }}
            {% endfor %}
            Q: {{ question }}
            """

        assert (
            fn("Instruction", [], "Question")
            == """Instruction

Q: Question"""
        )

        assert (
            fn(instruction="Instruction", examples=[], question="Question")
            == """Instruction

Q: Question"""
        )

        assert (
            fn(
                instruction="Instruction",
                examples=[
                    {"question": "q1", "answer": "a1"},
                    {"question": "q2", "answer": "a2"},
                ],
                question="a3",
            )
            == """Instruction

Q: q1
A: a1
Q: q2
A: a2
Q: a3"""
        )

    def test_if(self):
        @prompt
        def fn(question, context=""):
            """{% if context != '' %}
            Consider the following context when answering the question:
            {{ context }}\n
            {% endif %}
            Q: {{ question }}
            """

        assert fn("hello?", "") == """Q: hello?"""
        assert fn("hello?") == """Q: hello?"""
        assert fn(question="hello?") == """Q: hello?"""

        assert (
            fn("hello?", context="this is context")
            == """Consider the following context when answering the question:
this is context

Q: hello?"""
        )


def test_truncate():
    assert truncate("hello", 10) == "hello"
    assert truncate("hello", 4) == "h..."

    with pytest.raises(ValueError):
        truncate("hello", 3)

    with pytest.raises(ValueError):
        truncate("hello", 2)

    with pytest.raises(ValueError):
        truncate("hello", 1)


@pytest.mark.parametrize(
    "input, expected",
    [
        (1, 1),
        (1.1, 1.1),
        ("1", 1),
        ("1 ", 1),
        ("1.1", 1.1),
        ("61", 61),
        ("61a ", None),
        ("one", None),
        (None, None),
    ],
)
def test_number(input, expected):
    assert to_number(input) == expected


def test_debug():
    DEBUG(0)
    assert DEBUG == 0

    DEBUG(1)
    assert DEBUG == 1


@pytest.mark.parametrize(
    "value_input, value_output, from_min, from_max, to_min, to_max",
    [
        (0, 0, 0, 4, 0, 100),
        (1, 25, 0, 4, 0, 100),
        (2, 50, 0, 4, 0, 100),
        (3, 75, 0, 4, 0, 100),
        (4, 100, 0, 4, 0, 100),
        #
        (0, 0, 0, 4, 0, 1),
        (1, 0.25, 0, 4, 0, 1),
        (2, 0.5, 0, 4, 0, 1),
        (3, 0.75, 0, 4, 0, 1),
        (4, 1, 0, 4, 0, 1),
        #
        (0, 0, 0, 4, 0, 10),
        (1, 2.5, 0, 4, 0, 10),
        (2, 5, 0, 4, 0, 10),
        (3, 7.5, 0, 4, 0, 10),
        (4, 10, 0, 4, 0, 10),
    ],
)
def test_map_range(value_input, value_output, from_min, from_max, to_min, to_max):
    assert (
        map_number_range(value_input, from_min, from_max, to_min, to_max)
        == value_output
    )
