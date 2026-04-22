from typing import TypeAlias
from itertools import product
from dataclasses import dataclass
import re
import warnings

from korean_spell_checker.models.spell_checker_classes import *
from korean_spell_checker.models.interface import SpellErrorType
from korean_spell_checker.utils.hangul import remove_batchim, replace_batchim

ErrorMessage: TypeAlias = str
RuleSteps: TypeAlias = list[tuple[Condition, SpacingRule, bool, bool]]
KoSpellRules: TypeAlias = tuple[RuleSteps, ErrorMessage, SpellErrorType]
AndParam: TypeAlias = "Condition | _TagSet | _FormSet"

class MessageToken():
    def __init__(self, type: str, string: str):
        self.type: str = type
        self.string: str = string
    
    def __repr__(self):
        return f"MessageToken({self.type}: '{self.string}')"
    
class MessageParser:
    def __init__(self):
        self.parens = {"(": "LPAREN", ")": "RPAREN", "{": "LBRAKET", "}": "RBRAKET"}
        self.methods = {"merge": "MERGE"}
        self.tags = {"tokenform": "TFORM", "batchimremovedform": "BREMOVEDFORM", "batchimreplacedform": "BREPLACEDFORM", "dform": "DYNAMIC_FORM"}
    
    def tokenize(self, string: str) -> list[MessageToken]:            
        if string == "":
            return []
        
        tokens = []
        i = 0
        temp_strings = ""
        
        def _make_string_token():
            nonlocal temp_strings
            if temp_strings == "":
                return
            tokens.append(MessageToken("STRING", temp_strings))
            temp_strings = ""
        
        while i < len(string):            
            if string[i].isalpha():                
                _make_string_token()
                start = i
                while i < len(string) and string[i] not in self.parens:
                    i += 1
                alphas = string[start:i]
                if alphas in self.methods.keys():
                    tokens.append(MessageToken(self.methods[alphas], alphas))
                elif alphas in self.tags.keys():
                    tokens.append(MessageToken(self.tags[alphas], alphas))
                else:
                    tokens.append(MessageToken("STRING", alphas))
                continue
            
            elif string[i] in self.parens.keys():
                _make_string_token()
                tokens.append(MessageToken(self.parens[string[i]], string[i]))
            else:
                temp_strings += string[i]
            i += 1
        return tokens
    
parser = MessageParser()
print(parser.tokenize("동사 활용이 잘못되었습니다. '{batchimremovedform[0]}셨다, {batchimremovedform[0]}신' 등이 올바른 표현입니다."))
        

# {form} / {form[N]} / {조사a,조사b} 플레이스홀더 처리
_TEMPLATE_PATTERN = re.compile(
    r'\{(form|batchimremovedform)(?:\[(-?\d+)\])?\}'
    r'|\{(batchimreplacedform)(?:\[(-?\d+)\])?,([ㄱ-ㅎ])\}'
    r'|\{([^{},\[\]]+),([^{},\[\]]+)\}'
)

def _select_josa(a: str, b: str, last_char: str) -> str:
    """
    받침 여부에 따라 a(받침 있음) / b(받침 없음) 선택.
    으로/로 계열: ㄹ받침이면 b로.
    """
    if not ('가' <= last_char <= '힣'):
        return b
    code = (ord(last_char) - 0xAC00) % 28
    if code == 0:
        return b
    if code == 8 and a.startswith("으") and b == a[1:]:  # ㄹ받침 + 으로/로 계열
        return b
    return a

def _resolve_msg(template: str, combo: tuple) -> str:
    """
    메시지 템플릿의 플레이스홀더를 combo의 form 값으로 치환.

    - {form}    → combo의 마지막 TagAndFormCondition / FormCondition의 form
    - {form[N]} → N번째 TagAndFormCondition / FormCondition의 form (음수 인덱스 지원)
    - {batchimremovedform[N]} → 받침 제거된 form
    - {batchimreplacedform[N],A} → 받침을 A로 변경한 form
    - {a,b}     → 직전에 치환된 form의 받침 여부로 a/b 선택
    조사 마커는 직전 {form} 기준으로 결정되며, {form} 없이 단독 사용 시 마지막 form 기준.
    """
    if '{' not in template:
        return template
    form_vals = [c.form for c in combo if isinstance(c, (TagAndFormCondition, FormCondition))]
    if not form_vals:
        return template

    current_last_char = form_vals[-1][-1] if form_vals[-1] else ""

    def replacer(m: re.Match) -> str:
        nonlocal current_last_char

        if m.group(1) is not None:                            # {form} / {batchimremovedform}
            keyword = m.group(1)
            idx_str = m.group(2)
            try:
                val = form_vals[-1] if idx_str is None else form_vals[int(idx_str)]
            except IndexError:
                return m.group(0)

            if keyword == 'batchimremovedform' and val:
                val = val[:-1] + remove_batchim(val[-1])

            current_last_char = val[-1] if val else ""
            return val

        elif m.group(3) is not None:                          # {batchimreplacedform[N],ㅈ}
            idx_str = m.group(4)
            jamo = m.group(5)
            try:
                val = form_vals[-1] if idx_str is None else form_vals[int(idx_str)]
            except IndexError:
                return m.group(0)

            if val:
                val = val[:-1] + replace_batchim(val[-1], jamo)

            current_last_char = val[-1] if val else ""
            return val

        else:                                                 # {a,b} 조사
            return _select_josa(m.group(6), m.group(7), current_last_char)

    return _TEMPLATE_PATTERN.sub(replacer, template)

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
        self.is_context: bool = False
        
    def __repr__(self):
        return f"_RuleStepData(conditions={self.conditions}, spacing_rule={self.spacing_rule}, is_optional={self.is_optional}, is_context={self.is_context})"

class RuleBuilder:
    def __init__(self, error_type: SpellErrorType = SpellErrorType.NOT_SET):
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
    
    def lemma(self, lemma: str):
        self.steps.append(_RuleStepData([LemmaCondition(lemma=lemma)]))
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
    
    def length(self, n: int):
        self.steps.append(_RuleStepData([LengthCondition(length=n)]))
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
    
    def context(self):
        if not self.steps:
            raise ValueError("No condition to set context flag. Call a condition method first.")
        if self.steps[-1].is_context:
            warnings.warn("Context flag is already set on this condition.")
        
        self.steps[-1].is_context = True
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
        
        {form}으로 form 조건을 지정할 수 있음.
        
        {form[0]}: 0번째 form 조건
        {batchimremovedform[0]}: 0번째 form 조건에서 마지막 글자의 받침을 뺀 str
        {batchimreplacedform[0],A}: 0번째 form 조건의 마지막 받침을 A로 바꾼 str
        
        {을,를} 리터럴로 조사 표현 가능.
        """
        self.message = input_msg
        return self
    
    def errtype(self, error_type: SpellErrorType):
        # init에서 설정하고 있지만 중간에 개별적으로 바꾸고 싶을 경우를 위해 메서드 준비
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

    def _validate_buildable(self):
        if not self.steps:
            raise ValueError(f"At least one condition must be added.\nconditions: {self.steps}")
        if self.message is None:
            raise ValueError(f"Error message must be set using msg().\nconditions: {self.steps}")
        if self.error_type == SpellErrorType.NOT_SET:
            raise ValueError(f"Error type has not be set. use errtype() to set error's type.\nconditions: {self.steps}")
        if not any(not s.is_context for s in self.steps):
            raise ValueError(f"At least one non-context condition must be added.\nconditions: {self.steps}")

    def build(self) -> list[KoSpellRules]:
        self._validate_buildable()

        results: list[KoSpellRules] = []
        for combo in product(*(step.conditions for step in self.steps)):
            rule_steps: RuleSteps = [
                (cond, step.spacing_rule, step.is_optional, step.is_context)
                for cond, step in zip(combo, self.steps)
            ]
            results.append((rule_steps, _resolve_msg(self.message, combo), self.error_type))

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

def lemma(l: str) -> LemmaCondition:
    return LemmaCondition(lemma=l)

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
        tf_combos: list[Condition]= [
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