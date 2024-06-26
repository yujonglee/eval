import pytest

import fastrepl
from fastrepl.llm import completion, tokenize
from fastrepl.errors import TokenizeNotImplementedError


class TestTokenize:
    @pytest.mark.parametrize(
        "model, text, expected",
        [
            ("gpt-3.5-turbo", "A", [32]),
            ("gpt-3.5-turbo", "B", [33]),
            ("gpt-3.5-turbo", "C", [34]),
            ("gpt-3.5-turbo", "1", [16]),
            ("gpt-3.5-turbo", "2", [17]),
            ("gpt-3.5-turbo", "3", [18]),
            ("gpt-3.5-turbo", "11", [806]),
            ("gpt-3.5-turbo", "99", [1484]),
            ("gpt-3.5-turbo", "100", [1041]),
            #
            ("gpt-3.5-turbo-16k", "A", [32]),
            ("gpt-3.5-turbo-16k", "B", [33]),
            ("gpt-3.5-turbo-16k", "C", [34]),
            ("gpt-3.5-turbo-16k", "1", [16]),
            ("gpt-3.5-turbo-16k", "2", [17]),
            ("gpt-3.5-turbo-16k", "3", [18]),
            ("gpt-3.5-turbo", "11", [806]),
            ("gpt-3.5-turbo-16k", "99", [1484]),
            ("gpt-3.5-turbo-16k", "100", [1041]),
            #
            ("gpt-4", "A", [32]),
            ("gpt-4", "B", [33]),
            ("gpt-4", "C", [34]),
            ("gpt-4", "1", [16]),
            ("gpt-4", "2", [17]),
            ("gpt-4", "3", [18]),
            ("gpt-3.5-turbo", "11", [806]),
            ("gpt-3.5-turbo-16k", "99", [1484]),
            ("gpt-3.5-turbo-16k", "100", [1041]),
        ],
    )
    def test_openai(self, model, text, expected):
        actual = tokenize(model, text)
        assert actual == expected

    @pytest.mark.parametrize(
        "model, text, expected",
        [
            ("command-nightly", "A", [40]),
            ("command-nightly", "B", [41]),
            ("command-nightly", "C", [42]),
            ("command-nightly", "1", [24]),
            ("command-nightly", "2", [25]),
            ("command-nightly", "3", [26]),
            ("command-nightly", "11", [2795]),
            ("command-nightly", "99", [3518]),
            ("command-nightly", "100", [4899]),
        ],
    )
    def test_cohere(self, model, text, expected):
        actual = tokenize(model, text)
        assert actual == expected

    def test_ai21(self):
        with pytest.raises(NotImplementedError):
            tokenize("j2-ultra", "A")
        with pytest.raises(TokenizeNotImplementedError):
            tokenize("j2-ultra", "A")
