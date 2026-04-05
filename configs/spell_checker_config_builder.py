from typing import TypeAlias
from itertools import product
from dataclasses import dataclass

from korean_spell_checker.models.spell_checker_classes import *
from korean_spell_checker.models.interface import SpellErrorType

ErrorMessage: TypeAlias = str
RuleSteps: TypeAlias = list[tuple[Condition, SpacingRule, bool]]
KoSpellRules: TypeAlias = tuple[RuleSteps, ErrorMessage, SpellErrorType]
AndParam: TypeAlias = "Condition | _TagSet | _FormSet"

@dataclass(frozen=True, slots=True)
class _TagSet:
    """AND 내부에서 여러 태그를 묶는 용도. Condition이 아님."""
    tags: set[str]

@dataclass(frozen=True, slots=True)
class _FormSet:
    """AND 내부에서 여러 폼을 묶는 용도. Condition이 아님."""
    forms: set[str]

class _RuleStepData:
    def __init__(self, conditions):
        self.conditions: list[Condition] = conditions
        self.spacing_rule: SpacingRule = SpacingRule.ANY
        self.is_optional: bool = False
        
    def __repr__(self):
        return f"_RuleStepData(conditions={self.conditions}, spacing_rule={self.spacing_rule}, is_optional={self.is_optional})"

class RuleBuilder:
    def __init__(self, error_type: SpellErrorType = None):
        self.steps: list[_RuleStepData] = []
        self.message = None
        self.error_type: SpellErrorType = error_type

    def tag(self, tag: str):
        self.steps.append(_RuleStepData([TagCondition(tag=tag)]))
        return self

    def tags(self, tag_set: set[str]):
        self.steps.append(_RuleStepData([TagCondition(tag=t) for t in tag_set]))
        return self
    
    def form(self, form: str):
        self.steps.append(_RuleStepData([FormCondition(form=form)]))
        return self

    def forms(self, form_set: set[str]):
        self.steps.append(_RuleStepData([FormCondition(form=f) for f in form_set]))
        return self
    
    def batchim(self, b: str):
        self.steps.append(_RuleStepData([BatchimCondition(batchim=b)]))
        return self
    
    def any_batchim(self):
        self.steps.append(_RuleStepData([AnyBatchimCondition()]))
        return self
    
    def any(self):
        self.steps.append(_RuleStepData([AnyCondition()]))
        return self
    
    def tag_form(self, tag: str, form: str):
        self.steps.append(_RuleStepData([TagAndFormCondition(form=form, tag=tag)]))
        return self
    
    def first(self):
        self.steps.append(_RuleStepData([FirstTokenCondition()]))
        return self

    def _set_space(self, spacing_rule: SpacingRule):
        if not self.steps:
            raise ValueError("No condition to set a spacing rule. Call a condition method first.")
        if spacing_rule not in SpacingRule:
            raise ValueError(f"{spacing_rule} is not a member of SpacingRule class.")
        self.steps[-1].spacing_rule = spacing_rule

    def if_spaced(self):
        self._set_space(SpacingRule.SPACED)
        return self

    def if_not_spaced(self):
        self._set_space(SpacingRule.ATTACHED)
        return self

    def opt(self):
        """조건을 선택적으로 만드는 메서드.

        첫 번째 조건을 Optional로 설정하면 ValueError.
        (첫 번째 조건 optional은 의미가 없음)
        """
        if not self.steps:
            raise ValueError("No condition to make optional. Call a condition method first.")
        if len(self.steps) == 1:
            raise ValueError("First condition can't be optional. Optional conditions must come after required ones.")
        self.steps[-1].is_optional = True
        return self

    def msg(self, input_msg: str):
        """에러 메시지를 입력하는 메서드.
        에러 메시지는 반드시 입력해야 함.
        """
        self.message = input_msg
        return self
    
    def errtype(self, error_type: SpellErrorType = None):
        if error_type == None and self.error_type == None:
            raise ValueError("Error type has not be set.")
        
        self.error_type = error_type
        return self

    def AND(self, *params: AndParam):
        optimized = _optimize_and(params)
        self.steps.append(_RuleStepData(optimized))
        return self

    def OR(self, *conditions: Condition):
        self.steps.append(_RuleStepData(list(conditions)))
        return self
    
    def NOT(self, condition: "Condition | _TagSet | _FormSet"):
        self.steps.append(_RuleStepData([NotCondition(_resolve_to_condition(condition))]))
        return self

    def build(self) -> list[KoSpellRules]:
        if self.message is None:
            raise ValueError(f"Error message must be set using msg().\nconditions: {self.steps}")
        if self.error_type is None:
            raise ValueError(f"Error type has not be set. use errtype() to set error's type.\nconditions: {self.steps}")
        if not self.steps:
            raise ValueError(f"At least one condition must be added.\nconditions: {self.steps}")

        condition_lists = [step.conditions for step in self.steps]

        results: list[KoSpellRules] = []
        for combo in product(*condition_lists):
            rule_steps: RuleSteps = [
                (cond, step.spacing_rule, step.is_optional)
                for cond, step in zip(combo, self.steps)
            ]
            results.append((rule_steps, self.message, self.error_type))
            
        return results

def tag(t: str) -> TagCondition:
    return TagCondition(tag=t)

def tags(ts: set[str]) -> _TagSet:
    return _TagSet(tags=ts)

def form(f: str) -> FormCondition:
    return FormCondition(form=f)

def forms(fs: set[str]) -> _FormSet:
    return _FormSet(forms=fs)

def tag_form(t: str, f: str) -> TagAndFormCondition:
    return TagAndFormCondition(form=f, tag=t)

def length(n: int) -> LengthCondition:
    return LengthCondition(length=n)

def batchim(b: str) -> BatchimCondition:
    return BatchimCondition(batchim=b)

def any_batchim() -> AnyBatchimCondition:
    return AnyBatchimCondition()

def first() -> FirstTokenCondition:
    return FirstTokenCondition()

def _resolve_to_condition(p: AndParam) -> Condition:
    """_TagSet/_FormSet → 런타임 Condition으로 변환. 이미 Condition이면 그대로."""
    if isinstance(p, _TagSet):
        if len(p.tags) == 1:
            return TagCondition(tag=next(iter(p.tags)))
        return TagSetCondition(tags=frozenset(p.tags))
    if isinstance(p, _FormSet):
        if len(p.forms) == 1:
            return FormCondition(form=next(iter(p.forms)))
        return FormSetCondition(forms=frozenset(p.forms))
    return p  # 이미 Condition

def NOT(condition: "Condition | _TagSet | _FormSet") -> NotCondition:
    return NotCondition(_resolve_to_condition(condition))

def _optimize_and(params: tuple[AndParam, ...]) -> list[Condition]:
    """Tags와 Forms를 AND로 묶을 경우, dictionary를 이용한 O(1) 조회가 쉽도록 각 조건을 분류하는 메서드.

    AND(Tag, Form) -> TagAndFormCondtion로 최적화(Tags/Form, Tag/Forms, Tags/Forms도 동일)
    
    기타 -> fallback으로 빠지는 AndCondition 생성
    
    """
    tag_values: list[str] = []
    form_values: list[str] = []
    other_conds: list[Condition] = []

    for p in params:
        if isinstance(p, _TagSet):
            tag_values.extend(p.tags)
        elif isinstance(p, _FormSet):
            form_values.extend(p.forms)
        elif isinstance(p, TagCondition):
            tag_values.append(p.tag)
        elif isinstance(p, FormCondition):
            form_values.append(p.form)
        elif isinstance(p, Condition):
            other_conds.append(p)
        else:
            raise TypeError(f"Unsupported AND parameter type: {type(p)}")

    if tag_values and form_values:
        tf_combos = [
            TagAndFormCondition(form=f, tag=t)
            for t, f in product(tag_values, form_values)
        ]
        if other_conds:
            return [
                AndCondition(conditions=(tf, *other_conds))
                for tf in tf_combos
            ]
        return tf_combos

    resolved = [_resolve_to_condition(p) for p in params]
    return [AndCondition(conditions=tuple(resolved))]

def OR(*conditions: Condition) -> OrCondition:
    return OrCondition(conditions=tuple(conditions))

def AND(*params: AndParam) -> Condition:
    flat_params: list[AndParam] = []
    for p in params:
        if isinstance(p, AndCondition):
            flat_params.extend(p.conditions)
        else:
            flat_params.append(p)

    optimized = _optimize_and(tuple(flat_params))
    if len(optimized) == 1:
        return optimized[0]
    return OrCondition(conditions=tuple(optimized))