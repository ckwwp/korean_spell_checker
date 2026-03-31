from collections import deque
from typing import Iterator

from korean_spell_checker.models.interface import SpellError, SpellErrorType

class TrieNode:
    __slots__ = ('children', 'output', 'fail', 'error_type')

    def __init__(self):
        self.children: dict[str, TrieNode] = {}
        self.output: set = set()
        self.fail: TrieNode = None
        self.error_type: SpellErrorType = SpellErrorType.NOT_SET

class RawStringSearcher():
    def __init__(self):
        self.root = TrieNode()

    def add_word(self, word: str, msg: str, error_type: SpellErrorType):
        if self.search == self._search_impl:
            raise RuntimeError("cannot add words after build.")
    
        curr_node = self.root

        for ch in word:
            if ch not in curr_node.children.keys():
                curr_node.children[ch] = TrieNode()
            curr_node = curr_node.children[ch]

        curr_node.output.add((msg, len(word)))
        curr_node.error_type = error_type

    def add_word_from_list(self, rule_list: tuple[list[tuple[tuple[str], str]]]):
        for words, err_type in rule_list:
            for word_group, msg in words:
                for word in word_group:
                    self.add_word(word, msg, err_type)

    def build(self):
        queue = deque()
        
        for node in self.root.children.values():
            node.fail = self.root
            queue.append(node)
        
        while queue:
            node: TrieNode = queue.popleft()
            
            for char, child_node in node.children.items():
                dest = node.fail
                
                while dest != self.root and char not in dest.children:
                    dest = dest.fail
                
                if char in dest.children:
                    child_node.fail = dest.children[char]
                    if child_node.fail.output:
                        child_node.output |= child_node.fail.output
                else:
                    child_node.fail = self.root
                
                queue.append(child_node)

    def search(self, word: str) -> Iterator[SpellError]:
        """단어가 포함되어 있는지 검색하는 함수.

        Args:
            word (str): 검색할 문자열.

        Raises:
            ValueError: 아무 규칙을 추가하지 않고 search했을 시 ValueError 발생.

        Yields:
            list[SpellError]: 발견된 맞춤법 오류 정보를 순차적으로 반환.
        """
        # 본 로직은 _search_impl 참조
        if not self.root.children:
            raise ValueError("You must have at least one word to search.")
        self.build()
        self.search = self._search_impl
        return self._search_impl(word)    
        
    def _search_impl(self, word: str) -> Iterator[SpellError]:
        current_node = self.root
        
        for idx, char in enumerate(word):
            while current_node != self.root and char not in current_node.children:
                current_node = current_node.fail
            
            if char in current_node.children:
                current_node = current_node.children[char]
                for msg, length in current_node.output:
                    yield SpellError(
                        error_type=current_node.error_type,
                        error_message=msg,
                        start_index=idx-length+1,
                        end_index=idx+1
                        )