from dataclasses import dataclass

import pytest

from helpers import assert_error_raw_text, assert_no_errors_raw_text, check_error_type
from korean_spell_checker.configs.raw_string_searcher_config import RAW_STRING_RULES
from korean_spell_checker.models.interface import SpellErrorType

@dataclass
class Case:
    text: str
    expect_error: bool = True
    error_type: SpellErrorType = None

class TestSpellChecker:
    @pytest.fixture(autouse=True)
    def setup(self, searcher):
        searcher.add_word_from_list(RAW_STRING_RULES)
        self.searcher = searcher

    def _run_test(self, text: str, c: Case):
        errors = list(self.searcher.search(text))

        if c.expect_error:
            assert_error_raw_text(errors, text)
            if c.error_type:
                check_error_type(errors, c.error_type)
        else:
            assert_no_errors_raw_text(errors, text)

    # 1 ── 띄어쓰기 오류 케이스 (SPACING)
    @pytest.mark.parametrize("text", [
        "프로모션을 진행해 팬들을 다시 한 번 경악하게 했다.",
        "팬들에게도 롤모델 이미지가 강하다.",
    ])
    def test_spacing_errors(self, text):
        self._run_test(text, Case(text, error_type=SpellErrorType.SPACING))
        
    # 1 ── 띄어쓰기 오류 오탐 방지 케이스
    @pytest.mark.parametrize("text", [
        "프로모션을 진행해 팬들을 다시 한번 경악하게 했다.",
        "팬들에게도 롤 모델 이미지가 강하다."
    ])
    def test_spacing_no_errors(self, text):
        self._run_test(text, Case(text, expect_error=False))

    # 2 ── 맞춤법 및 활용 오류 케이스 (SPELLING)
    @pytest.mark.parametrize("text", [
        "여지껏 발매한 젤다 시리즈 중에서",
        "팀 컬러는 노랑색."
    ])
    def test_spelling_errors(self, text):
        self._run_test(text, Case(text, error_type=SpellErrorType.SPELLING))

    # 2 ── 맞춤법 및 활용 오탐 방지 케이스
    @pytest.mark.parametrize("text", [
        "오승환이 팀에서 떠날 때를 대비해서 오승환의 대체 선수로 손승락을 눈여겨보고 있다는 닛칸스포츠의 기사가 나왔다.",
    ])
    def test_spelling_no_errors(self, text):
        self._run_test(text, Case(text, expect_error=False))