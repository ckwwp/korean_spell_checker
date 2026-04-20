from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from typing import Iterator

from korean_spell_checker.models.interface import KoToken, SpellError, SpellErrorType
from korean_spell_checker.models.spell_checker_classes import SpacingRule, Condition, TagCondition, FormCondition, TagAndFormCondition, NotCondition, BatchimCondition, AnyBatchimCondition
from korean_spell_checker.utils.hangul import get_jongseong, is_jamo
from korean_spell_checker.configs.spell_checker_config_builder import KoSpellRules

@dataclass(slots=True)
class _EnrichedToken:
    form: str
    tag: str
    start: int
    end: int
    len: int
    lemma: str
    batchim: str

@dataclass(frozen=True, slots=True)
class _Transition:
    condition: Condition
    target_node: _RuleNode
    spacing_rule: SpacingRule = SpacingRule.ANY
    is_optional: bool = False
    is_context: bool = False

class _RuleNode:
    __slots__ = ('tag_transitions', 'form_transitions', 'form_and_tag_transitions', 'batchim_transitions', 'any_batchim_transitions', 'fallback_transitions', '_all_transitions', '_optional_closure', 'output_message', 'output_path', 'error_type')

    def __repr__(self):
        n = len(self._all_transitions)
        out = self.output_message or "None"
        return f"_RuleNode(transitions={n}, output={out!r})"

    def __init__(self):
        self.tag_transitions: dict[str, list[_Transition]] = {}
        self.form_transitions: dict[str, list[_Transition]] = {}
        self.form_and_tag_transitions: dict[str, dict[str, list[_Transition]]] = {}
        self.batchim_transitions: dict[str, list[_Transition]] = {}
        self.any_batchim_transitions: list[_Transition] = []

        self.fallback_transitions: list[_Transition] = []
        
        self._all_transitions: list[_Transition] = []
        self._optional_closure: set[_RuleNode] | None = None

        self.output_message: str | None = None
        self.error_type: SpellErrorType = SpellErrorType.NOT_SET
        self.output_path: str | None = None
        
    def get_optional_closure(self) -> set[_RuleNode]:
        """optional로 갈 수 있는 노드들을 BFS로 탐색하는 함수. 엡실론 클로저를 구현.

        Returns:
            set[_RuleNode]: 도달 가능한 node의 set.
        """
        if self._optional_closure is not None:
            return self._optional_closure
        
        closure = {self}
        queue = deque([self])
        
        while queue:
            current_node = queue.popleft()
            
            for trans in current_node._all_transitions:
                if trans.is_optional and trans.target_node not in closure:
                    closure.add(trans.target_node)
                    queue.append(trans.target_node)
        
        self._optional_closure = closure
        return closure
    
    def get_or_create_next_node(self, condition: Condition, spacing_rule: SpacingRule, is_optional: bool, is_context: bool) -> _RuleNode:
        """조건에 맞는 간선을 찾거나 새로 생성하여 다음 노드를 반환하는 함수."""
        
        existing_node = self._find_transition(condition, spacing_rule, is_optional, is_context)
        if existing_node:
            return existing_node
        
        next_node = _RuleNode()
        new_trans = _Transition(condition=condition, target_node=next_node, spacing_rule=spacing_rule, is_optional=is_optional, is_context=is_context)
        
        self._add_transition_to_node(condition, new_trans)
        
        return next_node
    
    def _find_transition(self, cond: Condition, spacing: SpacingRule, optional: bool, context: bool) -> _RuleNode | None:
        target_list = []
        
        if isinstance(cond, TagAndFormCondition):
            tag_dict = self.form_and_tag_transitions.get(cond.form)
            if tag_dict is not None:
                target_list = tag_dict.get(cond.tag, [])
        elif isinstance(cond, TagCondition):
            target_list = self.tag_transitions.get(cond.tag, [])
        elif isinstance(cond, FormCondition):
            target_list = self.form_transitions.get(cond.form, [])
        elif isinstance(cond, BatchimCondition):
            target_list = self.batchim_transitions.get(cond.batchim, [])
        elif isinstance(cond, AnyBatchimCondition):
            target_list = self.any_batchim_transitions
        else:
            for t in self.fallback_transitions:
                if t.condition == cond and t.spacing_rule == spacing and t.is_optional == optional and t.is_context == context:
                    return t.target_node
            return None

        for t in target_list:
            if t.spacing_rule == spacing and t.is_optional == optional and t.is_context == context:
                return t.target_node
            
        return None

    def _add_transition_to_node(self, cond: Condition, trans: _Transition):
        if isinstance(cond, TagAndFormCondition):
            self.form_and_tag_transitions.setdefault(cond.form, {}).setdefault(cond.tag, []).append(trans)
        elif isinstance(cond, TagCondition):
            self.tag_transitions.setdefault(cond.tag, []).append(trans)
        elif isinstance(cond, FormCondition):
            self.form_transitions.setdefault(cond.form, []).append(trans)
        elif isinstance(cond, BatchimCondition):
            self.batchim_transitions.setdefault(cond.batchim, []).append(trans)
        elif isinstance(cond, AnyBatchimCondition):
            self.any_batchim_transitions.append(trans)
        else:
            self.fallback_transitions.append(trans)
        self._all_transitions.append(trans)

class SpellChecker:
    def __init__(self, debug: bool = False):
        self._root = _RuleNode()
        self._is_frozen: bool = False
        self._debug: bool = debug

    def _add_rule(self, rules: KoSpellRules) -> None:
        if self._is_frozen:
            raise RuntimeError("You cannot add rules after calling 'check' function.")
            
        current = self._root
        path = []
        conditions, msg, error_type = rules
        
        if len(conditions) == 0:
            return
          
        for cond, spacing, optional, context in conditions:
            current = current.get_or_create_next_node(condition=cond, spacing_rule=spacing, is_optional=optional, is_context=context)
            if self._debug:
                path.append(f"{cond}, {spacing}, {optional}, {context}")
            
        current.output_message = msg
        current.error_type = error_type

        if self._debug:
            current.output_path = "  →  ".join(path)

    def add_rule_from_list(self, rules: list[KoSpellRules]) -> None:
        """KoSpellRules가 담긴 list를 받아 규칙을 추가하는 함수.

        Args:
            rules (list[KoSpellRules]): spell_checker_config_builder로 생성한 결과물.
        """
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
        # 본 구현은 _check_impl 참조
        self._is_frozen = True
        if not self._root._all_transitions:
            raise ValueError("You must have at least one rule to check spelling.")
        
        return self._check_impl(tokens)
    
    def _check_impl(self, tokens: list[KoToken]) -> Iterator[SpellError]:
        """NFA 시뮬레이션 기반 토큰 검사.

        각 토큰마다 아래 4단계를 반복:
        1) root에서 새 커서 시작
        2) optional 전이로 도달 가능한 노드 확장 (epsilon closure)
           - i==0이면 NOT 전이도 엡실론으로 처리 (BOS epsilon: 문장 시작에서 NOT 조건은 vacuously true)
        3) 출력 가능한 노드에서 에러 수집
        4) 현재 토큰과 매칭되는 전이를 따라 커서 전진

        동일 노드에 여러 커서가 도달하면 가장 늦은 시작점만 유지 (최단 매치 우선).
        루프 종료 후 남은 커서에 대해 optional/NOT 전이를 엡실론으로 확장해 출력 수집 (EOF epsilon).
        """
        # 여러 번 실행되는 함수라 대부분을 인라인으로 작성.
        enriched_tokens = [
            _EnrichedToken(
                form=t.form, tag=t.tag, start=t.start, end=t.end, len=t.len, lemma=t.lemma,
                batchim=(t.form[-1] if is_jamo(t.form[-1]) else get_jongseong(t.form[-1]))
            )
            for t in tokens
        ]

        active_cursors: dict[_RuleNode, tuple[int, int]] = {}
        next_cursors: dict[_RuleNode, tuple[int, int]] = {}
        expanded_cursors: dict[_RuleNode, tuple[int, int]] = {}

        candidates: list[_Transition] = []

        for i, token in enumerate(enriched_tokens):
            has_space = (token.start - tokens[i-1].end > 0) if i > 0 else False

            active_cursors[self._root] = (-1, i)

            expanded_cursors.clear()
            
            # ── Phase 1: epsilon closure 확장 ──
            for node, idxs in active_cursors.items():
                start_idx, end_idx = idxs

                if node not in expanded_cursors or start_idx > expanded_cursors[node][0]:
                    expanded_cursors[node] = (start_idx, end_idx) # 엡실론 전이이므로 인덱스 갱신 없음

                for closure_node in node.get_optional_closure():
                    if closure_node not in expanded_cursors or start_idx > expanded_cursors[closure_node][0]:
                        expanded_cursors[closure_node] = (start_idx, end_idx)

            # ── BOS epsilon: 문장 시작에서 NOT 전이를 엡실론으로 처리 ──
            # spacing rule이 ANY인 경우에만 적용 (SPACED/ATTACHED는 실제 인접 토큰이 필요)
            if i == 0:
                bos_queue = deque(expanded_cursors.items())

                while bos_queue:
                    current_node, idxs = bos_queue.popleft()
                    start_idx, end_idx = idxs

                    for trans in current_node._all_transitions:
                        if not isinstance(trans.condition, NotCondition) or trans.spacing_rule != SpacingRule.ANY:
                            continue
                        
                        target = trans.target_node
                        if target not in expanded_cursors or start_idx > expanded_cursors[target][0]:
                            if start_idx == -1 and not trans.is_context: # -1: is_context가 아닌 노드에 도달한 적 없는 상태
                                start_idx = i
                            if not trans.is_context: # end는 마지막으로 본 is_context가 아닌 토큰의 위치이므로 is_context가 False라면 매번 갱신
                                end_idx = i

                            expanded_cursors[target] = (start_idx, end_idx)

                            bos_queue.append((target, (start_idx, end_idx)))
                            for opt_node in target.get_optional_closure():
                                if opt_node not in expanded_cursors or start_idx > expanded_cursors[opt_node][0]:
                                    expanded_cursors[opt_node] = (start_idx, end_idx)
                                    bos_queue.append((opt_node, (start_idx, end_idx)))

            # ── Phase 2: 출력 수집 & 전이 탐색 ──
            next_cursors.clear()
            current_step_errors: dict[str, tuple[SpellErrorType, int, int, str | None]] = {}

            for node, idxs in expanded_cursors.items():
                start_idx, end_idx = idxs

                if node.output_message and start_idx < i:
                    self._update_shortest_match(
                        current_step_errors,
                        node.output_message,
                        node.error_type,
                        tokens[start_idx].start,
                        tokens[end_idx].end,
                        node.output_path
                    )
            
                candidates.clear()
                
                form_tag_dict = node.form_and_tag_transitions.get(token.form)
                if form_tag_dict is not None:
                    if ft := form_tag_dict.get(token.tag):
                        candidates.extend(ft)
                if tt := node.tag_transitions.get(token.tag):
                    candidates.extend(tt)
                if ft2 := node.form_transitions.get(token.form):
                    candidates.extend(ft2)
                if token.batchim:
                    if bt := node.batchim_transitions.get(token.batchim):
                        candidates.extend(bt)
                    candidates.extend(node.any_batchim_transitions)

                for t in node.fallback_transitions:
                    if t.condition.match(token):
                        candidates.append(t)
                        
                for trans in candidates:
                    # 전이하면 안 되는 케이스 block. ANY는 상관없이 통과
                    if trans.spacing_rule == SpacingRule.SPACED and not has_space:
                        continue
                    elif trans.spacing_rule == SpacingRule.ATTACHED and has_space:
                        continue

                    target = trans.target_node

                    # context가 아닐 때만 index 갱신 (start_idx/end_idx를 직접 변경하지 않고 임시 변수 사용)
                    if target not in next_cursors or start_idx > next_cursors[target][0]:
                        new_start = i if (start_idx == -1 and not trans.is_context) else start_idx
                        new_end = i if not trans.is_context else end_idx
                        next_cursors[target] = (new_start, new_end)
            
            # ── Phase 3: 에러 yield & 커서 스왑 ──
            for msg, (err_type, start, end, output_path) in current_step_errors.items():
                yield SpellError(
                    error_type=err_type,
                    error_message=msg,
                    start_index=start,
                    end_index=end,
                    debug_path=output_path
                    )
            
            active_cursors, next_cursors = next_cursors, active_cursors

        # ── EOF epsilon: optional/NOT 전이를 엡실론으로 확장해 남은 출력 수집 ──
        if tokens:
            final_step_errors: dict[str, tuple[SpellErrorType, int, int, str | None]] = {}

            final_expanded: dict[_RuleNode, tuple[int, int]] = {}
            eof_queue = deque(active_cursors.items())

            while eof_queue:
                node, idxs = eof_queue.popleft()
                start_idx, end_idx = idxs

                if node in final_expanded and start_idx <= final_expanded[node][0]:
                    continue

                final_expanded[node] = (start_idx, end_idx)

                for trans in node._all_transitions:
                    is_not_any = isinstance(trans.condition, NotCondition) and trans.spacing_rule == SpacingRule.ANY
                    if trans.is_optional or is_not_any:
                        target = trans.target_node
                        if target not in final_expanded or start_idx > final_expanded[target][0]:
                            eof_queue.append((target, (start_idx, end_idx)))

            for node, idxs in final_expanded.items():
                start_idx, end_idx = idxs
                if node.output_message:
                    self._update_shortest_match(
                        storage=final_step_errors,
                        msg=node.output_message,
                        error_type=node.error_type,
                        start=tokens[start_idx].start,
                        end=tokens[end_idx].end,
                        output_path=node.output_path
                    )

            for msg, (err_type, start, end, output_path) in final_step_errors.items():
                yield SpellError(
                    error_type=err_type,
                    error_message=msg,
                    start_index=start,
                    end_index=end,
                    debug_path=output_path
                )
    
    def _update_shortest_match(self, storage: dict[str, tuple[SpellErrorType, int, int, str | None]], msg: str, error_type: SpellErrorType, start: int, end: int, output_path: str | None) -> None:
        if msg not in storage:
            storage[msg] = (error_type, start, end, output_path)
        else:
            _, old_start, old_end, _ = storage[msg]
            old_length = old_end - old_start
            new_length = end - start
            
            # 더 짧은 것 선택, 길이 같으면 더 뒤에 있는 것
            if new_length < old_length or (new_length == old_length and start > old_start):
                storage[msg] = (error_type, start, end, output_path)