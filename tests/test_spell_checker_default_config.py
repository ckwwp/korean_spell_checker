from dataclasses import dataclass

import pytest

from helpers import assert_error, assert_no_errors, check_error_type
from korean_spell_checker.configs.spell_checker_config import SPELL_CHECK_RULES
from korean_spell_checker.models.interface import SpellErrorType

@dataclass
class Case:
    text: str
    expect_error: bool = True
    error_type: SpellErrorType = None

class TestSpellChecker:
    @pytest.fixture(autouse=True)
    def setup(self, checker):
        checker.add_rule_from_list(SPELL_CHECK_RULES)
        self.checker = checker

    def _run_test(self, tokenizer, c: Case):
        tokens = tokenizer.tokenize(c.text)
        errors = list(self.checker.check(tokens))

        if c.expect_error:
            assert_error(errors, tokens)
            if c.error_type:
                check_error_type(errors, c.error_type)
        else:
            assert_no_errors(errors, tokens)

    # 1 ── 띄어쓰기 오류 케이스 (SPACING)
    @pytest.mark.parametrize("text", [
        "딸이 아버지를 잃었으니, 아버지까지 딸을 잃게 할 필요없잖아",
        "그 눈빛은 마치 시공간을 초월한 듯 했다.",
        "오픈 되지 않은 이벤트이거나 이벤트 오픈 조건을 달성하지 못했습니다",
        "대선배님이니까, 아실 지도 모르겠네요",
        "그게 달인이라고 할만한 일인가?",
        "둘을 깜빡할뻔했네",
        "이제 시작일뿐이야",
        "우리가 질리 없다고!",
        "…친구, 모르면서 아는척하지 말라고.",
        "생존의 중압감 때문에 그들은 삶에 대한 열정을 전부 잃어버린지 오래였다.",
        "알고 계실텐데요",
        "잠깐, 거긴 대체 무슨 상황인거야?",
        "많은분들의 응원 덕분에 가능했습니다.",
        "끊임 없이 밀고 나가면 노벨상은 선물로 주어진다고 말했다.",
    ])
    def test_spacing_errors(self, tokenizer, text):
        self._run_test(tokenizer, Case(text, error_type=SpellErrorType.SPACING))
        
    # 1 ── 띄어쓰기 오류 오탐 방지 케이스
    @pytest.mark.parametrize("text", [
        "딸이 아버지를 잃었으니, 아버지까지 딸을 잃게 할 필요 없잖아",
        "그 눈빛은 마치 시공간을 초월한 듯했다.",
        "출발할 준비 됐어",
        "그러게. 말 되네!",
        "주사위의 수가 40% 확률로 두 배 되기",
        "그 녀석들은 아직 눈치채지 못했을 거야.",
        "사람은 과거에 빠져 헤어나질 못하면 안 되지."
    ])
    def test_spacing_no_errors(self, tokenizer, text):
        self._run_test(tokenizer, Case(text, expect_error=False))

    # 2 ── 맞춤법 및 활용 오류 케이스 (SPELLING)
    @pytest.mark.parametrize("text", [
        "업무가 잘 안되서",
        "그런 상태가 되 있는 거지",
        "될 대로 돼라고 생각하고 있을 가능성도 있다…",
        "너와 네의 동료들에 대해 알고 싶어.",
        "이 게임은 정말 재미잇어.",
        "정말 살고 있엇던 건가…",
        "거절하겠씁니다.",
        "생각보다 빨리 해역을 벗어낫군.",
        "오랜 개발 기간 이후에도 끈임없이 발생하는 수많은 버그와 게임플레이를 제대로 공개하지 않는다는 점 등이 문제가 되었다.",
        
        "이게 왠 떡이냐?",
        "여름엔 웬지 첫사랑 생각이 나",
        "지금 당장 회의실으로 가야 해.",
        
        "사상 최저치의 출산률을 기록하였다.",
        "아니예요, 그럴 리가요",
        "자랑스런 우리 딸.",
        "주파수와 기억을 지우려고 했을 뿐이예요...",
        "이로서 회의를 마치겠습니다.",
        "어따 대고 반말이야!",
        "김홍도의 서민에 대한 풍속화를 보면, 서당에서 횟초리를 맞아서 창피함을 주는 체벌의 모습을 볼 수 있다.",
        "사람을 본따 만든 조각상.",
    ])
    def test_spelling_errors(self, tokenizer, text):
        self._run_test(tokenizer, Case(text, error_type=SpellErrorType.SPELLING))

    # 2 ── 맞춤법 및 활용 오탐 방지 케이스
    @pytest.mark.parametrize("text", [
        "네, 앞에 있는 이 사람들은 다 「순례자」예요.",
        "선의의 보답을 받았나 보구나",
        "정말 지치지도 않나 보군"
        "자랑스러운 우리 딸.",
        "사상 최저치의 출산율을 기록하였다.",
        "오랜 개발 기간 이후에도 끊임없이 발생하는 수많은 버그와 게임플레이를 제대로 공개하지 않는다는 점 등이 문제가 되었다.",
        "사람을 본떠 만든 조각상.",
    ])
    def test_spelling_no_errors(self, tokenizer, text):
        self._run_test(tokenizer, Case(text, expect_error=False))