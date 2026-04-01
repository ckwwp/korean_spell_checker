from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from typing import Iterator

from korean_spell_checker.models.interface import KoToken, SpellError, SpellErrorType
from korean_spell_checker.models.spell_checker_classes import SpacingRule, Condition, TagCondition, FormCondition, TagAndFormCondition
from korean_spell_checker.configs.spell_checker_config_builder import KoSpellRules

@dataclass(frozen=True, slots=True)
class _Transition:
    condition: Condition
    target_node: _RuleNode
    spacing_rule: SpacingRule = SpacingRule.ANY
    is_optional: bool = False

class _RuleNode:
    __slots__ = ('tag_transitions', 'form_transitions', 'form_and_tag_transitions', 'fallback_transitions', '_all_transitions', '_optional_closure', 'output_message', 'output_path', 'error_type')

    def __repr__(self):
        n = len(self._all_transitions)
        out = self.output_message or "None"
        return f"_RuleNode(transitions={n}, output={out!r})"

    def __init__(self):
        self.tag_transitions: dict[str, list[_Transition]] = {}
        self.form_transitions: dict[str, list[_Transition]] = {}
        self.form_and_tag_transitions: dict[str, dict[str, list[_Transition]]] = {}
        
        self.fallback_transitions: list[_Transition] = []
        
        self._all_transitions: list[_Transition] = []
        self._optional_closure: set["_RuleNode"] | None = None

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
    
    def get_or_create_next_node(self, condition: Condition, spacing_rule: SpacingRule, is_optional: bool) -> "_RuleNode":
        """조건에 맞는 간선을 찾거나 새로 생성하여 다음 노드를 반환하는 함수."""
        
        existing_node = self._find_transition(condition, spacing_rule, is_optional)
        if existing_node:
            return existing_node
        
        next_node = _RuleNode()
        new_trans = _Transition(condition=condition, target_node=next_node, spacing_rule=spacing_rule, is_optional=is_optional)
        
        self._add_transition_to_node(condition, new_trans)
        
        return next_node
    
    def _find_transition(self, cond: Condition, spacing: SpacingRule, optional: bool) -> "_RuleNode" | None:
        target_list = []
        
        if isinstance(cond, TagAndFormCondition):
            tag_dict = self.form_and_tag_transitions.get(cond.form)
            if tag_dict is not None:
                target_list = tag_dict.get(cond.tag, [])
        elif isinstance(cond, TagCondition):
            target_list = self.tag_transitions.get(cond.tag, [])
        elif isinstance(cond, FormCondition):
            target_list = self.form_transitions.get(cond.form, [])
        else:
            for t in self.fallback_transitions:
                if t.condition == cond and t.spacing_rule == spacing and t.is_optional == optional:
                    return t.target_node
            return None

        for t in target_list:
            if t.spacing_rule == spacing and t.is_optional == optional:
                return t.target_node
        return None

    def _add_transition_to_node(self, cond: Condition, trans: _Transition):
        if isinstance(cond, TagAndFormCondition):
            self.form_and_tag_transitions.setdefault(cond.form, {}).setdefault(cond.tag, []).append(trans)
        elif isinstance(cond, TagCondition):
            self.tag_transitions.setdefault(cond.tag, []).append(trans)
        elif isinstance(cond, FormCondition):
            self.form_transitions.setdefault(cond.form, []).append(trans)
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
          
        for cond, spacing, optional in conditions:
            current = current.get_or_create_next_node(condition=cond, spacing_rule=spacing, is_optional=optional)
            if self._debug:
                path.append(f"{cond}, {spacing}, {optional}")
            
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
        3) 출력 가능한 노드에서 에러 수집
        4) 현재 토큰과 매칭되는 전이를 따라 커서 전진
        
        동일 노드에 여러 커서가 도달하면 가장 늦은 시작점만 유지 (최단 매치 우선).
        """
        active_cursors: dict[_RuleNode, int] = {}
        next_cursors: dict[_RuleNode, int] = {}
        expanded_cursors: dict[_RuleNode, int] = {}
        
        for i, token in enumerate(tokens):
            has_space = (token.start - tokens[i-1].end > 0) if i > 0 else False

            active_cursors[self._root] = i

            expanded_cursors.clear()
            
            # ── Phase 1: epsilon closure 확장 ──
            for node, start_idx in active_cursors.items():
                if node not in expanded_cursors or start_idx > expanded_cursors[node]:
                    expanded_cursors[node] = start_idx
                    
                for closure_node in node.get_optional_closure():
                    if closure_node not in expanded_cursors or start_idx > expanded_cursors[closure_node]:
                        expanded_cursors[closure_node] = start_idx
            
            # ── Phase 2: 출력 수집 & 전이 탐색 ──
            next_cursors.clear()
            current_step_errors: dict[str, tuple[SpellErrorType, int, int, str]] = {}

            for node, start_idx in expanded_cursors.items():
                if node.output_message and start_idx < i:
                    self._update_shortest_match(
                        current_step_errors,
                        node.output_message,
                        node.error_type,
                        tokens[start_idx].start,
                        tokens[i - 1].end,
                        node.output_path
                    )
            
                candidates = []
                form_tag_dict = node.form_and_tag_transitions.get(token.form)
                if form_tag_dict is not None:
                    if ft := form_tag_dict.get(token.tag):
                        candidates.extend(ft)
                if tt := node.tag_transitions.get(token.tag):
                    candidates.extend(tt)
                if ft2 := node.form_transitions.get(token.form):
                    candidates.extend(ft2)

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
                    if target not in next_cursors or start_idx > next_cursors[target]:
                        next_cursors[target] = start_idx
            
            # ── Phase 3: 에러 yield & 커서 스왑 ──
            for msg, (err_type, start, end, output_path) in current_step_errors.items():
                yield SpellError(
                    error_type=err_type,
                    error_message=msg,
                    start_index= start,
                    end_index=end,
                    debug_path=output_path
                    )
            
            active_cursors, next_cursors = next_cursors, active_cursors

        # 마지막 남은 토큰 처리
        if tokens:
            final_step_errors: dict[str, tuple[SpellErrorType, int, int, str]] = {}

            for node, start_idx in active_cursors.items():
                for closure_node in node.get_optional_closure():
                    if closure_node.output_message:
                        self._update_shortest_match(
                            storage=final_step_errors,
                            msg=closure_node.output_message,
                            error_type=closure_node.error_type,
                            start=tokens[start_idx].start,
                            end=tokens[-1].end,
                            output_path=closure_node.output_path
                        )

            for msg, (err_type, start, end, output_path) in final_step_errors.items():
                yield SpellError(
                    error_type=err_type,
                    error_message=msg,
                    start_index=start,
                    end_index=end,
                    debug_path=output_path
                )
    
    def _update_shortest_match(self, storage: dict[str, tuple[SpellErrorType, int, int, str]], msg: str, error_type: SpellErrorType, start: int, end: int, output_path: str) -> None:
        if msg not in storage:
            storage[msg] = (error_type, start, end, output_path)
        else:
            _, old_start, old_end, _ = storage[msg]
            old_length = old_end - old_start
            new_length = end - start
            
            # 더 짧은 것 선택, 길이 같으면 더 뒤에 있는 것
            if new_length < old_length or (new_length == old_length and start > old_start):
                storage[msg] = (error_type, start, end, output_path)