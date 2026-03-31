from korean_spell_checker.configs.spell_checker_config_builder import *
from korean_spell_checker.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.SPELLING)

_CERTAINS: list[KoSpellRules] = [
    

    *rule()
    .AND(any_batchim(), NOT(tag(Tag.닫는부호)))
    .tag_form(Tag.긍정지정사, "이")
    .tag_form(Tag.종결어미, "예요")
    .msg("'~이에요'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag(Tag.부정지정사)
    .tag_form(Tag.종결어미, "예요")
    .msg("'아니에요'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "있")
    .tag_form(Tag.선어말어미, "엇")
    .msg("'있었다'의 오타입니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "머리")
    .tag_form(Tag.일반명사, "속")
    .msg("'머릿속'이 올바른 표현입니다.")
    .build(),

    *rule()
    .batchim("ㄹ")
    .AND(tags(TagGroup.조사), form("으로"))
    .msg("받침이 ㄹ인 단어에는 '로'를 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.보조용언, "계시")
    .tag_form(Tag.종결어미, "군")
    .msg("'계시는군'의 형태로 써야 합니다.")
    .build(),

    *rule()
    .AND(tag(Tag.동사), length(2))
    .AND(tag(Tag.종결어미), forms({"구나", "군"}))
    .msg("동사 뒤에는 '-는구나', '-는군'의 형태로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "두르")
    .tag(Tag.연결어미)
    .tag_form(Tag.동사, "쌓이")
    .msg("'둘러싸이다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .OR(batchim("ㄴ"), NOT(any_batchim()))
    .tag_form(Tag.명사파생접미사, "률")
    .msg("ㄴ받침 혹은 받침 없는 명사에는 '율'를 사용해야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사파생접미사규칙활용, "스럽")
    .tag_form(Tag.관형사형전성어미, "ㄴ")
    .msg("'~스러운'을 '스런'으로 줄여 쓸 수 없습니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형격조사, "의")
    .tag_form(Tag.관형격조사, "의")
    .msg("조사 '의'가 중복으로 사용된 것 같습니다.")
    .build(),
    
    *rule()
    .OR(tag_form(Tag.동사, "하"), tag_form(Tag.동사파생접미사, "하"))
    .OR(tag_form(Tag.선어말어미, "었"), tag_form(Tag.선어말어미, "겠"))
    .tag_form(Tag.동사, "쓰")
    .AND(tag(Tag.종결어미), forms({"ㅂ니다", "ㅂ니까"}))
    .msg("'습니다'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.보조용언, "있")
    .tag_form(Tag.선어말어미, "엇")
    .msg("'있었'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.부정지정사, "아니")
    .tag_form(Tag.선어말어미, "였")
    .msg("'아니었다'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.부정지정사, "아니")
    .tag_form(Tag.연결어미, "예요")
    .msg("'아니에요'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "되")
    .OR(tag_form(Tag.동사, "있"), tag_form(Tag.연결어미, "서"))
    .msg("'돼'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "되")
    .tag_form(Tag.종결어미, "어")
    .tag_form(Tag.인용격조사, "라고")
    .msg("'되라고'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .AND(tag(Tag.동사), forms({"헤어나", "벗어나"}))
    .tag_form(Tag.선어말어미, "엇")
    .msg("'어났'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.보조용언, "않")
    .tag_form(Tag.동사, "되")
    .msg("'안 돼'의 오타가 아닌가요?")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "끈")
    .tag_form(Tag.주격조사, "이")
    .tag_form(Tag.명사형전성어미, "ㅁ")
    .OR(tag_form(Tag.일반부사, "없이"), tag_form(Tag.형용사, "없"))
    .msg("'끊임없이'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .AND(tag(Tag.일반명사), forms({"재미", "상관", "관심", "흥미"}))
    .form("잇")
    .msg("'있다'의 오타가 아닌가요?")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "간지르")
    .msg("'간질이다'가 올바른 표현입니다. 예: 간질임, 간질이다 등")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "왠")
    .msg("'웬'이 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "웬지")
    .msg("'왠지'가 올바른 표현입니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "어따")
    .tag_form(Tag.동사, "대")
    .tag_form(Tag.연결어미, "고")
    .msg("'얻다 대고'가 올바른 표현입니다.")
    .build(),

    *rule()
    .OR(tag_form(Tag.동사, "헤매이"), tag_form(Tag.동사, "헤메"))
    .msg("'헤매다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사파생접미사, "하")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "매")
    .msg("'헤매다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "떼우")
    .msg("'때우다'의 오타가 아닌가요?")
    .build(),

    *rule()
    .AND(tag(Tag.형용사), forms({"어줍잖", "어쭙찮", "어줍찮", "어쭙찮"}))
    .msg("'어쭙잖다'가 올바른 표현입니다.")
    .build(),
]

_OM = [
    *rule()
    .tag_form(Tag.동사, "뿜")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "나오")
    .msg("'뿜어져 나오다'로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반부사, "안절부절")
    .tag_form(Tag.동사, "하")
    .msg("'안절부절못하다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "가능")
    .tag_form(Tag.형용사파생접미사, "하")
    .tag_form(Tag.관형사형전성어미, "ㄴ")
    .tag(Tag.일반부사)
    .msg("'가능한 한~'으로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사규칙활용, "누렇")
    .tag_form(Tag.종결어미, "네")
    .msg("'누러네'로 써야 합니다.")
    .build(),
]

_ADD = [
    *rule()
    .tag_form(Tag.형용사, "힘들")
    .tag_form(Tag.연결어미, "으며")
    .msg("불필요한 '으'가 사용되었습니다.")
    .build(),

    *rule()
    .tag_form(Tag.연결어미, "ㄹ려고")
    .msg("'~려고'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "삼가하")
    .msg("'삼가다'가 올바른 표현입니다.")
    .build(),
]

_REP = [
    *rule()
    .tag_form(Tag.일반명사, "제미")
    .tag_form(Tag.동사, "있")
    .msg("'재미있다'의 오타가 아닌가요?")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "회손")
    .msg("'훼손'이 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "횟초리")
    .msg("'회초리'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사, "째째하")
    .msg("'쩨쩨하다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "수근거리")
    .msg("'수군거리다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .AND(tag(Tag.일반명사), forms({"정답", "답"}))
    .any()
    .opt()
    .any()
    .opt()
    .tag_form(Tag.동사, "맞추")
    .msg("정답/답을 '맞히다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.대명사, "이")
    .tag_form(Tag.부사격조사, "로서")
    .msg("'이것으로'의 의미일 경우 '이로써'가 올바른 표현입니다. (예시: 이로써 회의를 마치겠습니다.)")
    .build(),

    *rule()
    .AND(tags({Tag.종결어미, Tag.연결어미}), form("ㄹ께"))
    .msg("'-ㄹ게'로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.어근, "내노라")
    .msg("'내로라하다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "우겨넣")
    .msg("'욱여넣다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.대명사, "느")
    .tag_form(Tag.일반명사, "김")
    .if_not_spaced()
    .msg("'느낌'의 오타가 아닌가요?")
    .build(),

    *rule()
    .tag_form(Tag.일반부사, "되려")
    .msg("'오히려'의 의미라면 '되레'가 올바른 표현입니다. 예시: 그 사람이 되레 화를 냈다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사, "옳")
    .tag_form(Tag.형용사, "바르")
    .msg("'올바르다'의 오타가 아닌가요?")
    .build(),
]

_MIF = [
    *rule()
    .tag_form(Tag.주격조사, "이")
    .tag_form(Tag.긍정지정사, "이")
    .tag_form(Tag.선어말어미, "었")
    .msg("'이었다'로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.긍정지정사, "이")
    .tag_form(Tag.선어말어미, "였")
    .msg("'이었다'로 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "붙")
    .tag_form(Tag.연결어미, "히")
    .msg("'붙이다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.연결어미, "ㄹ래")
    .tag_form(Tag.보조사, "야")
    .msg("'~려야'가 올바른 표현입니다. 예: '하려야 할 수가 없다.'")
    .build(),

    *rule()
    .tag_form(Tag.형용사규칙활용, "낫")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "지")
    .msg("'나아지다'의 오타가 아닌가요?")
    .build(),

    *rule()
    .tag_form(Tag.동사, "본뜨")
    .OR(OR(tag_form(Tag.연결어미, "어서"), AND(tags({Tag.종결어미, Tag.연결어미}), form("어"))), tag_form(Tag.선어말어미, "었"))
    .msg("'본떠/본뜬'이 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "덮히")
    .msg("'덮이다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "돋히")
    .msg("'돋치다'가 올바른 표현입니다.")
    .build(),

    *rule()
    .form("안")
    .tag_form(Tag.일반명사, "밖")
    .if_not_spaced()
    .msg("'안팎'이 올바른 표현입니다.")
    .build(),
]

_SHIFT_MISS = [
    *rule()
    .tag_form(Tag.동사, "끄")
    .if_not_spaced()
    .tag_form(Tag.선어말어미, "었")
    .msg("'껏'의 오타가 아닌가요?")
    .build(),
]

_DEPENDS_ON_DICTIONARY = [
    *rule()
    .tag_form(Tag.동사, "건내")
    .msg("'건네다'의 오타가 아닌가요?")
    .build(),
]

_NOT_CERTAINS = [
    
]

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.NEED_ML_JUDGE)

_NEED_ML_JUDGE = [
    *rule()
    .tag_form(Tag.일반명사, "형상") # '현상'
    .msg("'현상'의 오타가 아닌가요?")
    .build(),

    *rule()
    .tag_form(Tag.동사, "빼")
    .tag_form(Tag.선어말어미, "었")
    .msg("'뺏다'의 오타가 아닌가요?")
    .build(),

    *rule()
    .tag_form(Tag.동사, "띄")
    .msg("'띠다'의 오기가 아닌가요?")
    .build(),
]

_LOANWORDS = [
    *rule()
    .tag_form(Tag.고유명사, "캐롤")
    .msg("'캐럴'로 써야 합니다.")
    .build(),
]

SPELL_MISS_ERRORS = [
    *_CERTAINS,
    *_NOT_CERTAINS,
    *_DEPENDS_ON_DICTIONARY,
    *_OM,
    *_ADD,
    *_REP,
    *_MIF,
    *_SHIFT_MISS,
    *_LOANWORDS
]