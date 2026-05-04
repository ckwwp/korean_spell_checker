from __future__ import annotations
from typing import Iterator

from _core import RustSpellChecker
from korean_spell_checker.models.interface import KoToken, SpellError
from korean_spell_checker.models.spell_checker_classes import Condition
from korean_spell_checker.configs.spell_checker_config_builder import (
    KoSpellRules, EncodedKoSpellRules, _StringInterner,
)


def _encode_rule(rule: KoSpellRules, interner: _StringInterner) -> EncodedKoSpellRules:
    steps, msg, error_type, rule_id = rule
    encoded_steps = [
        (cond.encode(interner.intern), spacing.value, is_optional, is_context)
        for cond, spacing, is_optional, is_context in steps
    ]
    return (encoded_steps, msg, error_type, rule_id)


class SpellChecker:
    def __init__(self, debug: bool = False):
        self._inner = RustSpellChecker()
        self._interner = _StringInterner()
        self._is_frozen: bool = False
        self._debug = debug

    def _add_rule(self, rule: KoSpellRules | EncodedKoSpellRules) -> None:
        if self._is_frozen:
            raise RuntimeError("You cannot add rules after calling 'check' function.")

        # KoSpellRules vs EncodedKoSpellRules 판별:
        # KoSpellRules의 steps[0][0]은 Condition 인스턴스
        # EncodedKoSpellRules의 steps[0][0]은 tuple (kind, ...)
        steps = rule[0]
        if steps and isinstance(steps[0][0], Condition):
            rule = _encode_rule(rule, self._interner)  # type: ignore[arg-type]

        self._inner.add_rule(rule)

    def add_rule_from_list(self, rules: list) -> None:
        """KoSpellRules 또는 EncodedKoSpellRules가 담긴 list를 받아 규칙을 추가하는 함수."""
        for rule in rules:
            self._add_rule(rule)

    def check(self, tokens: list[KoToken]) -> Iterator[SpellError]:
        """토큰을 검사하는 함수.

        Args:
            tokens: KoToken의 list.

        Raises:
            ValueError: 아무 규칙도 추가하지 않고 호출 시 ValueError 발생.

        Yields:
            SpellError: 발견된 맞춤법 오류 정보를 순차적으로 반환.
        """
        self._is_frozen = True
        self._inner.set_strings(self._interner.strings)
        yield from self._inner.check(tokens)
