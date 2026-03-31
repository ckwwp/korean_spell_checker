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
        "사람은 과거에 빠져 헤어나질 못하면 안 되지.",
        "408,8**장",
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
        "사람을 본따 만든 조각상.",
        "앞서서 다카이치 총리가 파병에 대해서 승락을 하기는 쉽지 않을 것이다라고 말씀하셨는데.",
        "대만에서 일자리를 주겠다는 꾀임에 속아 경유지 캄보디아로 밀입국했던 베트남인 5명이 고문을 당하다 1명이 숨지고 4명은 몰래 강을 헤엄쳐 국경을 넘었다.",
        "“5만원권 환수율 향상을 위한 제조년도 표기를 적극 추진해야 한다”고 한국은행에 촉구한 바 있다.",
        "30% 이상의 크리티컬율을 보유할 경우 몬스터의 보호로 인한 크리티컬 감소를 상쇄할 수 있다."
        "새해에는 진심에 걸맞는 진심으로 보답드릴 수 있도록 제가 더 노력하겠습니다.",
        "앞으로도 저희 레스토랑을 애용해 주십시요.",
        "네가 밥을 먹던지 말던지 내 알 바 아니야.",
        "유일하게 기다리는 실날같은 희망이 있었다.",
        "작은 정육면체가 쥐여 있었다.",
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
        "오승환이 팀에서 떠날 때를 대비해서 오승환의 대체 선수로 손승락을 눈여겨보고 있다는 닛칸스포츠의 기사가 나왔다.",
        "그 모습이 얼마나 예쁘던지…",
        "눈은 영혼의 창이라던가.",
        "즉위하실 날 같은 생각은 안 하고 있다니까요.",
        "너의 손에 칼을 쥐여줄게."
    ])
    def test_spelling_no_errors(self, tokenizer, text):
        self._run_test(tokenizer, Case(text, expect_error=False))