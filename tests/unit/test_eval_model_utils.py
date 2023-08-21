import pytest

from fastrepl.eval.model.utils import (
    logit_bias_for_classification,
)


class TestLogitBiasForClassification:
    @pytest.mark.parametrize(
        "model, choices, expected",
        [
            (
                "gpt-3.5-turbo",
                "ABCDE",
                {32: 100, 33: 100, 34: 100, 35: 100, 36: 100},
            ),
            (
                "gpt-3.5-turbo",
                "123",
                {16: 100, 17: 100, 18: 100},
            ),
            (
                "gpt-3.5-turbo-16k",
                "ABCDE",
                {32: 100, 33: 100, 34: 100, 35: 100, 36: 100},
            ),
            (
                "gpt-3.5-turbo-16k",
                "123",
                {16: 100, 17: 100, 18: 100},
            ),
            (
                "gpt-4",
                "ABCDE",
                {32: 100, 33: 100, 34: 100, 35: 100, 36: 100},
            ),
            (
                "gpt-4",
                "123",
                {16: 100, 17: 100, 18: 100},
            ),
        ],
    )
    def test_openai(self, model, choices, expected):
        actual = logit_bias_for_classification(model, set(choices))
        assert actual == expected

    @pytest.mark.parametrize(
        "model, choices, expected",
        [
            (
                "command-nightly",
                "ABCDE",
                {40: 10, 41: 10, 42: 10, 43: 10, 44: 10},
            ),
            (
                "command-nightly",
                "123",
                {24: 10, 25: 10, 26: 10},
            ),
        ],
    )
    def test_cohere(self, model, choices, expected):
        actual = logit_bias_for_classification(model, set(choices))
        assert actual == expected

    @pytest.mark.parametrize("model", ["j2-ultra", "togethercomputer/llama-2-70b-chat"])
    def test_empty(self, model):
        assert logit_bias_for_classification(model, "") == {}
        assert logit_bias_for_classification(model, "ABC") == {}

    def test_invalid(self):
        with pytest.raises(ValueError):
            logit_bias_for_classification("gpt-3.5-turbo", set(["GOOD", "GREAT"]))