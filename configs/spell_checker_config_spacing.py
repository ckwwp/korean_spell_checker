from korean_spell_checker.configs.spell_checker_config_builder import *
from korean_spell_checker.models.interface import Tag, TagGroup, SpellErrorType

NUMBER_DETERMINERS = {"첫", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열", "백", "천", "만", "억"}
MONEY_DETERMINERS = {"골드", "엔", "원", "다이아"}
되다_EXCEPTIONS = {"얼마", "말", "기회", "부자", "배", "숙부", "여행", "형", "언니", "누나", "엄마", "아빠", "삼촌", "이모", "고모", "남편", "아내", "이튿날", "정도", "축제", "여정", "시간", "때", "돈", "습관", "상태", "말동무", "후반부"}

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.SPACING)

SPACING_ERRORS: list[KoSpellRules] = [
    *rule()
    .tag(Tag.일반명사)
    .tag(Tag.명사파생접미사)
    .if_spaced()
    .msg("명사파생접미사 앞은 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.관형사형전성어미)
    .AND(tag(Tag.의존명사), NOT(forms({"것", "데"})))
    .if_not_spaced()
    .msg("명사 앞은 띄어 써야 합니다.")
    .build(),

    *rule()
    .tags({Tag.일반명사, Tag.고유명사, Tag.의존명사})
    .tag(Tag.보조사)
    .if_spaced()
    .msg("조사를 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.의존명사)
    .tag(Tag.부사격조사)
    .if_spaced()
    .msg("조사를 붙여 써야 합니다.")
    .build(),

    *rule()
    .tags(TagGroup.부사)
    .tags(TagGroup.체언)
    .if_not_spaced()
    .msg("부사와 명사를 띄어 써야 합니다.")
    .build(),

    *rule()
    .AND(first(), AND(tag(Tag.일반명사), NOT(forms(되다_EXCEPTIONS))))
    .tag_form(Tag.동사, "되")
    .if_spaced()
    .NOT(tag_form(Tag.선어말어미, "시"))
    .msg("'되다'를 앞 말에 붙여 써야 합니다.")
    .build(),

    *rule()
    .NOT(tag(Tag.관형사형전성어미))
    .AND(tag(Tag.일반명사), NOT(forms(되다_EXCEPTIONS)))
    .tag_form(Tag.동사, "되")
    .if_spaced()
    .NOT(tag_form(Tag.선어말어미, "시"))
    .msg("'되다'를 앞 말에 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.동사파생접미사, "되")
    .if_spaced()
    .msg("'되다'를 앞 말에 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.동사파생접미사, "하")
    .if_spaced()
    .msg("'하다'를 앞 말에 붙여 써야 합니다.")
    .build(),

    *rule()
    .AND(tag(Tag.일반명사), length(3))
    .tag_form(Tag.동사, "하")
    .if_spaced()
    .msg("'하다'를 앞 말에 붙여 써야 합니다.")
    .build(),

    *rule()
    .tags(TagGroup.조사)
    .tag_form(Tag.동사, "하")
    .if_not_spaced()
    .msg("'하다'를 앞 말과 띄어 써야 합니다.")
    .build(),

    *rule()
    .AND(tag(Tag.일반명사), length(2))
    .tag(Tag.닫는부호)
    .opt()
    .tag(Tag.동사파생접미사)
    .tag(Tag.연결어미)
    .tag(Tag.보조용언)
    .if_not_spaced()
    .msg("보조 용언을 띄어 써야 합니다.")
    .build(),

    *rule()
    .tags({Tag.일반명사, Tag.대명사, Tag.고유명사})
    .tag(Tag.수사)
    .if_not_spaced()
    .msg("수사 앞은 띄어 써야 합니다.")
    .build(),

    *rule()
    .tags({Tag.일반명사, Tag.대명사})
    .tag(Tag.관형사)
    .if_not_spaced()
    .msg("관형사 앞을 띄어 써야 합니다.")
    .build(),

    *rule()
    .NOT(tag(Tag.숫자))
    .tag_form(Tag.구분부호, ",")
    .NOT(tag(Tag.숫자))
    .if_not_spaced()
    .msg("쉼표 뒤에 띄어쓰기가 없습니다.")
    .build(),
]

SPACING_SPECIFIC_ERRORS = [
    *rule()
    .AND(tag(Tag.관형사), forms(NUMBER_DETERMINERS))
    .tag(Tag.의존명사)
    .if_not_spaced()
    .msg("의존명사 앞을 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.의존명사, "번")
    .if_not_spaced()
    .tags(TagGroup.조사)
    .if_not_spaced()
    .msg("'한 번'으로 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.숫자)
    .tag(Tag.수사)
    .opt()
    .forms(MONEY_DETERMINERS)
    .if_not_spaced()
    .msg("통화 단위를 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.숫자)
    .tag_form(Tag.의존명사, "년")
    .AND(tag(Tag.일반명사), forms({"후", "뒤"}))
    .if_not_spaced()
    .msg("OO년 뒤/후로 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.부사격조사, "보다")
    .if_spaced()
    .tag_form(Tag.보조사, "는")
    .msg("비교의 의미인 '보다'는 앞 말과 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.숫자)
    .tag(Tag.의존명사)
    .tag_form(Tag.의존명사, "차")
    .if_not_spaced()
    .msg("'(기간) 차'로 띄어 써야 합니다.")
    .build(),

    *rule()
    .tags(TagGroup.체언)
    .form("시간")
    .if_not_spaced()
    .msg("'시간'을 띄어 써야 합니다.")
    .build(),

    *rule()
    .AND(tag(Tag.관형사형전성어미), batchim("ㄹ"))
    .tag_form(Tag.의존명사, "뿐")
    .if_spaced()
    .tag_form(Tag.부사격조사, "더러")
    .if_not_spaced() # '뿐더러'의 형태만 찾도록 붙여 썼을 때만 OK
    .msg("'-ㄹ뿐더러'는 앞 말에 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "끝")
    .tag_form(Tag.형용사, "없")
    .if_spaced()
    .msg("'끝없는'으로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.관형사형전성어미, "ㄹ")
    .tag_form(Tag.의존명사, "지")
    .if_spaced()
    .msg("'지'를 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.관형사형전성어미, "는")
    .tag_form(Tag.의존명사, "대로")
    .if_not_spaced()
    .msg("'대로'를 띄어 써야 합니다.")
    .build(),

    *rule()
    .tags({Tag.일반명사, Tag.대명사, Tag.고유명사})
    .tag_form(Tag.보조사, "대로")
    .if_spaced()
    .msg("'대로'를 앞 말에 붙여 써야 합니다.")
    .build(),

    # *rule()
    # .NOT(tag_form(Tag.연결어미, "지"))
    # .tag_form(Tag.일반부사, "못")
    # .tag_form(Tag.동사, "하")
    # .if_not_spaced()
    # .msg("'못 하다'로 띄어 써야 합니다.")
    # .build(),

    *rule()
    .NOT(tag_form(Tag.연결어미, "지"))
    .AND(NOT(tag_form(Tag.연결어미, "지")), NOT(tag_form(Tag.목적격조사, "ㄹ")))
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.동사, "하")
    .if_not_spaced()
    .msg("'못 하다'로 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.연결어미, "지")
    .any()
    .opt()
    .any()
    .opt()
    .tag_form(Tag.일반부사, "못")
    .any()
    .if_spaced()
    .msg("~지 못하다의 형태는 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.일반명사, "순")
    .if_spaced()
    .msg("순서를 나타낼 경우 '날짜순으로'와 같이 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.일반명사)
    .tag(Tag.의존명사)
    .if_not_spaced()
    .msg("의존명사 앞은 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.의존명사, "분")
    .if_not_spaced()
    .msg("'분'을 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.의존명사, "순")
    .if_spaced()
    .msg("순서를 나타낼 경우 '날짜순으로'와 같이 붙여 써야 합니다.")
    .build(),

    *rule()
    .tags(TagGroup.체언)
    .tag_form(Tag.명사파생접미사, "쯤")
    .if_spaced()
    .msg("'쯤'을 앞 말에 붙여 적어야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "어서")
    .tag_form(Tag.동사, "오")
    .if_not_spaced()
    .msg("'어서 오세요'로 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "하")
    .tag_form(Tag.선어말어미, "엇")
    .msg("'했'의 오기가 아닌지 확인해 주세요.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "시간")
    .tag_form(Tag.일반명사, "문제")
    .if_spaced()
    .tags({Tag.긍정지정사, Tag.종결어미})
    .msg("'시간문제'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "바라")
    .any()
    .tag_form(Tag.동사, "보")
    .if_spaced()
    .msg("'바라보다'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "주의")
    .tag_form(Tag.형용사, "깊")
    .if_not_spaced()
    .msg("'주의 깊다'로 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "욕심")
    .tag_form(Tag.동사, "부리")
    .if_spaced()
    .msg("'욕심부리다'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "기억")
    .tag_form(Tag.동사, "나")
    .if_spaced()
    .msg("'기억나다'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.보조사, "조차")
    .if_spaced()
    .msg("'조차'를 앞 말에 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반부사, "그만")
    .tag_form(Tag.동사, "두")
    .if_spaced()
    .msg("'멈추다'의 의미일 경우, '그만두다'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "들리")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "주")
    .if_spaced()
    .msg("'들려주다'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.명사파생접미사, "씩")
    .if_spaced()
    .msg("'씩'을 앞 말에 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "필요")
    .tag_form(Tag.형용사, "없")
    .if_not_spaced()
    .msg("'필요 없다'로 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.의존명사, "듯")
    .tag_form(Tag.형용사파생접미사, "하")
    .if_spaced()
    .msg("'듯하다'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "끊이")
    .tag_form(Tag.명사형전성어미, "ㅁ")
    .OR(tag_form(Tag.형용사, "없"), tag_form(Tag.일반부사, "없이"))
    .if_spaced()
    .msg("'끊임없다'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "비")
    .AND(tag_form(Tag.동사, "오"), tag_form(Tag.동사, "내리"))
    .msg("'비 오다', '비 내리다'로 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "주")
    .any()
    .tag_form(Tag.동사불규칙활용, "받")
    .if_spaced()
    .msg("'주고받다'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사파생접미사, "하")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "하")
    .if_spaced()
    .msg("~해하다로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "가지")
    .tag_form(Tag.연결어미, "어다")
    .AND(tag(Tag.보조용언), forms({"주", "드리"}))
    .msg("'주다', '드리다'를 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반부사, "안절부절")
    .tag_form(Tag.일반부사, "못")
    .if_spaced()
    .tag_form(Tag.동사, "하")
    .msg("'안절부절못하다'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반부사, "안절부절")
    .tag_form(Tag.일반부사, "못")
    .tag_form(Tag.동사, "하")
    .if_spaced()
    .msg("'안절부절못하다'로 붙여 써야 합니다.")
    .build(),
]

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.NEED_ML_JUDGE)

_NEED_ML_JUDGE = [
    *rule()
    .tag_form(Tag.일반명사, "열")
    .tag_form(Tag.동사불규칙활용, "받")
    .if_spaced()
    .msg("'화나다'의 의미일 경우 '열받다'로 붕여 써야 합니다.")
    .build(),
]