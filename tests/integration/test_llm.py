import pytest

from fastrepl.run import cache, tokenize, completion


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
            #
            ("gpt-3.5-turbo-16k", "A", [32]),
            ("gpt-3.5-turbo-16k", "B", [33]),
            ("gpt-3.5-turbo-16k", "C", [34]),
            ("gpt-3.5-turbo-16k", "1", [16]),
            ("gpt-3.5-turbo-16k", "2", [17]),
            ("gpt-3.5-turbo-16k", "3", [18]),
            #
            ("gpt-4", "A", [32]),
            ("gpt-4", "B", [33]),
            ("gpt-4", "C", [34]),
            ("gpt-4", "1", [16]),
            ("gpt-4", "2", [17]),
            ("gpt-4", "3", [18]),
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
        ],
    )
    def test_cohere(self, model, text, expected):
        actual = tokenize(model, text)
        assert actual == expected

    def test_ai21(self):
        with pytest.raises(NotImplementedError):
            tokenize("j2-ultra", "A")


def test_llm_cache():
    result_1 = completion(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": "hello"}]
    )
    assert result_1.get("_fastrepl_cached", None) is None

    result_2 = completion(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": "hello"}]
    )
    assert result_2.pop("_fastrepl_cached")

    assert result_1 == result_2
