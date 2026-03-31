from korean_spell_checker.tokenizations.ko_tokenizer import KoTokenizer
from korean_spell_checker.tokenizations.utils import pprint_tokens

print("■ 초기화 중…")
tkn = KoTokenizer()
_ = tkn.tokenize("")
print("■ 초기화 완료!\n")

while True:
    try:
        u_input = input("■ 토크나이징할 문장을 입력하세요.\n")
        try:
            result = tkn.tokenize(u_input)
            
            if not result:
                continue

            print("-" * 18 + "결과" + "-" * 18)
            pprint_tokens(result, detailed=True)
            print("-" * 40 + "\n")
        except Exception as e:
            print(f"오류 발생! {e}")
    except KeyboardInterrupt:
        quit()
