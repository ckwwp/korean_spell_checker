from __future__ import annotations
from enum import Enum, auto
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from korean_spell_checker.models.interface import InternalToken, TAG_TO_INT
from korean_spell_checker.utils.hangul import BATCHIM_LIST

class SpacingRule(Enum):
    """해당 단어 앞에 띄어쓰기 있는지 여부.

    Args:
        SPACED: 띄어져 있는 상태.
        ATTACHED: 붙어 있는 상태.
        ANY: 아무 상태나 허용.
    """
    SPACED = 1
    ATTACHED = 2
    ANY = 0

# ConditionEncoded: Rust에 전달하는 직렬화 형식
# Leaf:    (kind: int, value: int)   kind 1~9
# TagSet:  (10, list[int])
# FormSet: (11, list[int])
# And:     (12, list[ConditionEncoded])
# Or:      (13, list[ConditionEncoded])
# Not:     (14, ConditionEncoded)
type ConditionEncoded = tuple

_BATCHIM_TO_INT: dict[str, int] = {b: i for i, b in enumerate(BATCHIM_LIST) if b}

@dataclass(frozen=True, slots=True)
class Condition(ABC):
    @abstractmethod
    def match(self, token: InternalToken) -> bool:
        """상속받은 클래스에서 구현해야 하는 추상 메서드. 조건 만족 시 True를 반환하도록 구현해야 함."""
        raise NotImplementedError

    @abstractmethod
    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        """Rust에 전달하기 위한 정수 직렬화. intern은 문자열 → u32 intern id 함수."""
        raise NotImplementedError

@dataclass(frozen=True, slots=True)
class TagCondition(Condition):
    tag: str

    def match(self, token: InternalToken) -> bool:
        return token.tag == self.tag

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (1, TAG_TO_INT[self.tag])

@dataclass(frozen=True, slots=True)
class FormCondition(Condition):
    form: str

    def match(self, token: InternalToken) -> bool:
        return token.form == self.form

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (2, intern(self.form))

@dataclass(frozen=True, slots=True)
class TagAndFormCondition(Condition):
    """Tag와 Form을 동시에 검사하는 메서드. (form, tag)의 튜플을 이용해 O(1) 검사할 것이므로 TagCondition과 FormCondition을 and로 조합하지 않고 별도 메서드로 분리.
    """
    form: str
    tag: str

    def match(self, token: InternalToken) -> bool:
        return token.form == self.form and token.tag == self.tag

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (3, TAG_TO_INT[self.tag], intern(self.form))

@dataclass(frozen=True, slots=True)
class LemmaCondition(Condition):
    lemma: str

    def match(self, token: InternalToken) -> bool:
        return token.lemma == self.lemma

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (7, intern(self.lemma))

@dataclass(frozen=True, slots=True)
class AnyCondition(Condition):
    def match(self, token: InternalToken) -> bool:
        return True

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (8, 0)

@dataclass(frozen=True, slots=True)
class AnyBatchimCondition(Condition):
    def match(self, token: InternalToken) -> bool:
        return token.batchim != ""

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (5, 0)

@dataclass(frozen=True, slots=True)
class BatchimCondition(Condition):
    batchim: str

    def match(self, token: InternalToken) -> bool:
        return token.batchim == self.batchim

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (4, _BATCHIM_TO_INT[self.batchim])

@dataclass(frozen=True, slots=True)
class LengthCondition(Condition):
    length: int

    def match(self, token: InternalToken) -> bool:
        return token.len >= self.length

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (6, self.length)

@dataclass(frozen=True, slots=True)
class FirstTokenCondition(Condition):
    def match(self, token: InternalToken) -> bool:
        return token.start == 0

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (9, 0)

@dataclass(frozen=True, slots=True)
class TagSetCondition(Condition):
    tags: frozenset[str]

    def match(self, token: InternalToken) -> bool:
        return token.tag in self.tags

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (10, [TAG_TO_INT[t] for t in self.tags])

@dataclass(frozen=True, slots=True)
class FormSetCondition(Condition):
    forms: frozenset[str]

    def match(self, token: InternalToken) -> bool:
        return token.form in self.forms

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (11, [intern(f) for f in self.forms])

@dataclass(frozen=True, slots=True)
class AndCondition(Condition):
    conditions: tuple[Condition, ...]

    def match(self, token: InternalToken) -> bool:
        for cond in self.conditions:
            if not cond.match(token):
                return False
        return True

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (12, [c.encode(intern) for c in self.conditions])

@dataclass(frozen=True, slots=True)
class OrCondition(Condition):
    conditions: tuple[Condition, ...]

    def match(self, token):
        for cond in self.conditions:
            if cond.match(token):
                return True
        return False

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (13, [c.encode(intern) for c in self.conditions])

@dataclass(frozen=True, slots=True)
class NotCondition(Condition):
    condition: Condition

    def match(self, token: InternalToken) -> bool:
        return not self.condition.match(token)

    def encode(self, intern: Callable[[str], int]) -> ConditionEncoded:
        return (14, self.condition.encode(intern))