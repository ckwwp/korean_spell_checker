import pytest

@pytest.fixture(scope="session")
def tokenizer():
    from korean_spell_checker.tokenizations.ko_tokenizer import KoTokenizer
    return KoTokenizer()

@pytest.fixture
def checker():
    from korean_spell_checker.engines.spell_checker import SpellChecker
    return SpellChecker(debug=True)