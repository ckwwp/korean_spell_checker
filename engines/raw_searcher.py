from _core import RustRawStringSearcher
from korean_spell_checker.models.interface import SpellError, SpellErrorType

class RawStringSearcher(RustRawStringSearcher):
    def __init__(self):
        super().__init__()
        
    def add_word_from_list(self, rule_list: list[tuple[list[tuple[tuple[str, ...], str]], SpellErrorType]]):
        for words, err_type in rule_list:
            for word_group, msg in words:
                for word in word_group:
                    super().add_word(word, msg, err_type.name)        
        
    def search(self, word: str) -> list[SpellError]:
        return [SpellError(error_type=SpellErrorType[r[0]], error_message=r[1], start_index=r[2], end_index=r[3]) 
            for r in super().search_raw(word)]