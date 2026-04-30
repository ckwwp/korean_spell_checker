import timeit

text = "아무것도없는텍스트그냥읽기만함" * 10000

setup_rust = """
from _core import RawStringSearcher
searcher = RawStringSearcher()
searcher.add_word("여지껏", "테스트", "RAW")
searcher.add_word("돼", "테스트2", "RAW")
searcher.add_word("안돼", "테스트3", "RAW")
searcher.add_word("왠지", "테스트4", "RAW")
searcher.add_word("웬만하면", "테스트5", "RAW")
searcher.build()
"""

setup_python = """
from korean_spell_checker.engines.raw_searcher import RawStringSearcher
searcher = RawStringSearcher()
searcher.add_word("여지껏", "테스트", "RAW")
searcher.add_word("돼", "테스트2", "RAW")
searcher.add_word("안돼", "테스트3", "RAW")
searcher.add_word("왠지", "테스트4", "RAW")
searcher.add_word("웬만하면", "테스트5", "RAW")
searcher.build()
searcher.search = searcher._search_impl
"""

rust = timeit.timeit('searcher.search(text)', setup=setup_rust, globals={"text": text}, number=100)
python = timeit.timeit('list(searcher._search_impl(text))', setup=setup_python, globals={"text": text}, number=100)

print(f"Rust:   {rust/100*1000:.3f}ms")
print(f"Python: {python/100*1000:.3f}ms")
print(f"속도 차이: {python/rust:.1f}배")