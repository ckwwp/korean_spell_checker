from korean_spell_checker.configs.spell_checker_config_builder import *
from korean_spell_checker.models.interface import Tag, TagGroup, SpellErrorType

NUMBER_DETERMINERS = {"첫", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열", "백", "천", "만", "억"}
MONEY_DETERMINERS = {"골드", "엔", "원", "다이아"}
되다_EXCEPTIONS = {"얼마", "말", "기회", "부자", "배", "숙부", "여행", "형", "언니", "누나", "엄마", "아빠", "삼촌", "이모", "고모", "남편", "아내", "이튿날", "정도", "축제", "여정", "시간", "때", "돈", "습관", "파뿌리", "상태", "말동무", "후반부", "습관"}

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.SPACING)

GENERAL_SPACING_ERRORS: list[KoSpellRules] = [    
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
    .NOT(tags({Tag.관형사, Tag.관형사형전성어미, Tag.형용사파생접미사, Tag.관형격조사, Tag.목적격조사}))
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
    .tag(Tag.체언접두사)
    .tag(Tag.일반명사)
    .AND(tags({Tag.동사, Tag.형용사파생접미사}), form("하"))
    .if_spaced()
    .msg("'하다'를 앞 말에 붙여 써야 합니다.")
    .build(),

    *rule()
    .tags({Tag.목적격조사, Tag.주격조사})
    .tag_form(Tag.동사, "하")
    .if_not_spaced()
    .msg("'하다'를 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.일반명사)
    .tag(Tag.보조사)
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
    .NOT(tags({Tag.숫자, Tag.끝, Tag.닫는부호, Tag.구분부호, Tag.종결부호}))
    .if_not_spaced()
    .msg("쉼표 뒤에 띄어쓰기가 없습니다.")
    .build(),

    *rule()
    .tag(Tag.보격조사)
    .tag_form(Tag.동사, "되")
    .if_not_spaced()
    .msg("'되다'를 띄어 써야 합니다.")
    .build(),
]

_SPACING_ERRORS = [
    *rule()
    .AND(tag(Tag.관형사), forms(NUMBER_DETERMINERS))
    .tag(Tag.의존명사)
    .if_not_spaced()
    .msg("의존명사 앞을 띄어 써야 합니다.")
    .build(),

    *rule()
    .NOT(form("다시"))
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.의존명사, "번")
    .if_not_spaced()
    .AND(tags(TagGroup.조사), NOT(form("은")))
    .if_not_spaced()
    .msg("'한 번'으로 띄어 써야 합니다.")
    .build(),

    # *rule()
    # .tag(Tag.숫자)
    # .tag(Tag.수사)
    # .opt()
    # .forms(MONEY_DETERMINERS)
    # .if_not_spaced()
    # .msg("통화 단위를 띄어 써야 합니다.")
    # .build(),

    *rule()
    .tag(Tag.숫자)
    .tag_form(Tag.의존명사, "년")
    .AND(tag(Tag.일반명사), forms({"후", "뒤"}))
    .if_not_spaced()
    .msg("OO년 뒤/후로 띄어 써야 합니다.")
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
    .tag(Tag.일반명사)
    .form("부터")
    .if_spaced()
    .msg("'부터'를 앞 말과 붙여 써야 합니다.")
    .build(),

    *rule()
    .tags({Tag.의존명사, Tag.일반명사, Tag.명사파생접미사, Tag.대명사})
    .form("뿐")
    .if_spaced()
    .msg("'뿐'을 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tags({Tag.관형사형전성어미})
    .form("뿐")
    .if_not_spaced()
    .NOT(form("더러"))
    .msg("'뿐'을 앞 말과 띄어 써야 합니다.")
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
    .AND(tag(Tag.관형사형전성어미), forms({"ㄹ", "는"}))
    .AND(tags({Tag.의존명사, Tag.대명사}), form("지"))
    .if_spaced()
    .msg("'지'를 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.의존명사, "것")
    .tag_form(Tag.부사격조사, "보다")
    .if_spaced()
    .msg("'것보다'로 붙여 써야 합니다.")
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
    .tag_form(Tag.의존명사, "순")
    .if_spaced()
    .msg("순서를 나타낼 경우 '날짜순으로'와 같이 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "어서")
    .tag_form(Tag.동사, "오")
    .if_not_spaced()
    .msg("'어서 오세요'로 띄어 써야 합니다.")
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
    .tag_form(Tag.명사파생접미사, "쯤")
    .if_spaced()
    .msg("'쯤'을 앞 말에 붙여 적어야 합니다.")
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
    .if_spaced()
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
    
    *rule()
    .form("데")
    .if_not_spaced()
    .tag_form(Tag.부사격조사, "에")
    .msg("'데'를 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.감탄사, "아참")
    .msg("'아 참'으로 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.감탄사, "거")
    .tag_form(Tag.감탄사, "참")
    .if_spaced()
    .msg("'거참'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.대명사), forms({"그것", "그거"}))
    .tag_form(Tag.일반부사, "참")
    .if_spaced()
    .msg("'그것참'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.체언접두사, "제")
    .OR(tag(Tag.숫자), tag(Tag.수사))
    .if_spaced()
    .msg("'제1회'와 같이 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.체언접두사, "초")
    .any()
    .if_spaced()
    .msg("'초(超)-'는 접두사이므로 뒤에 오는 말과 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.체언접두사, "폐")
    .any()
    .if_spaced()
    .msg("'초(超)-'는 접두사이므로 뒤에 오는 말과 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .NOT(tag(Tag.관형사형전성어미))
    .form("쯤")
    .if_spaced()
    .msg("'쯤'을 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.명사파생접미사, "상")
    .if_spaced()
    .msg("위치 관계를 나타낼 경우 '네트워크상에'와 같이 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.명사파생접미사, "계")
    .if_spaced()
    .msg("분야/영역의 의미인 경우, '계'를 앞 말에 붙여 써야 합니다. (예시: 연예계)")
    .build(),
    
    *rule()
    .forms({"아르바이트", "회", "알바"})
    .form("비")
    .if_spaced()
    .msg("'비용'의 뜻인 경우, '-비'는 접미사이므로 붙여 씁니다.")
    .build(),
    
    *rule()
    .forms({"확인", "휴식", "관광", "격려", "연구", "답례", "응원"})
    .form("차")
    .if_spaced()
    .msg("'확인차'와 같이 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .form("어치")
    .if_spaced()
    .msg("'만 원어치'처럼 '어치'를 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .form("짜리")
    .if_spaced()
    .msg("'만 원짜리'처럼 '짜리'를 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .form("투성이")
    .if_spaced()
    .msg("'-투성이'는 접미사이므로 앞 말과 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사파생접미사, "거리")
    .if_spaced()
    .msg("'~거리다'를 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tags({Tag.일반명사, Tag.어근, Tag.일반부사})
    .tag_form(Tag.동사, "거리")
    .if_spaced()
    .msg("'~거리다'를 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tags(TagGroup.체언)
    .tag_form(Tag.일반명사, "하")
    .if_spaced()
    .tag_form(Tag.부사격조사, "에")
    .msg("'~의 아래'의 의미라면, 'OO하'로 붙여 써야 합니다. (예시: 그렇다는 전제하에)")
    .build(),
    
    *rule()
    .form("커녕")
    .if_spaced()
    .msg("'커녕'을 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.의존명사, "뻔")
    .tag_form(Tag.형용사파생접미사, "하")
    .if_spaced()
    .msg("'뻔하다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.의존명사, "체")
    .tag_form(Tag.동사파생접미사, "하")
    .if_spaced()
    .msg("'체하다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.의존명사, "척")
    .AND(tags({Tag.동사파생접미사, Tag.동사}), form("하"))
    .if_spaced()
    .msg("'척하다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.보조사, "부터")
    .if_spaced()
    .msg("'부터'를 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "차")
    .tag_form(Tag.연결어미, "고")
    .tag_form(Tag.동사, "넘치")
    .if_not_spaced()
    .msg("'차고 넘치다'로 띄어 써야 합니다.")
    .build(),
]

_NNB = [
    *rule()
    .tag(Tag.명사파생접미사)
    .tag_form(Tag.의존명사, "중")
    .if_not_spaced()
    .msg("'중'을 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.관형사), forms({"여러", "두", "세"}))
    .tag_form(Tag.의존명사, "번")
    .if_not_spaced()
    .msg("'번'을 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.관형사)
    .tag_form(Tag.의존명사, "가지")
    .if_not_spaced()
    .msg("종류를 나타내는 경우, '가지'를 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.일반명사, "입")
    .if_spaced()
    .msg("'한 번 베어 무는 단위'를 나타내는 경우, '한입'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "아무")
    .forms({"일", "걱정", "데", "곳", "쪽", "말"})
    .if_not_spaced()
    .msg("'아무' 뒤를 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "어느")
    .tags({Tag.의존명사, Tag.일반명사})
    .if_not_spaced()
    .msg("'어느' 뒤를 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "어느")
    .forms({"새", "덧"})
    .if_spaced()
    .msg("'{form[0]}{form[1]}'{으로,로} 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "더")
    .tag_form(Tag.일반명사, "이상")
    .if_not_spaced()
    .msg("'더 이상'으로 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.의존명사, "데")
    .if_not_spaced()
    .tag_form(Tag.보조사, "다")
    .if_not_spaced()
    .msg("'데'를 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "안")
    .AND(tag(Tag.동사), NOT(form("되")))
    .if_not_spaced()
    .msg("'안'과 동사를 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.의존명사, "수")
    .tag_form(Tag.형용사, "있")
    .if_not_spaced()
    .msg("'있다'를 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.의존명사, "수")
    .OR(tag_form(Tag.일반부사, "없이"), tag_form(Tag.형용사, "없"))
    .if_not_spaced()
    .msg("'없다'를 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tags({Tag.일반명사, Tag.고유명사, Tag.대명사, Tag.명사파생접미사})
    .tag_form(Tag.의존명사, "때문")
    .if_not_spaced()
    .msg("'때문'은 의존명사이므로, 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.숫자)
    .tag_form(Tag.명사파생접미사, "여")
    .AND(tag(Tag.의존명사), forms({"개", "개국", "명", "곳", "초", "분", "시간", "일", "주", "개월", "년", "군데", "차례"}))
    .if_not_spaced()
    .msg("'개'는 의존명사이므로, 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tags({Tag.일반명사, Tag.고유명사, Tag.대명사, Tag.명사파생접미사})
    .tag_form(Tag.의존명사, "간")
    .if_not_spaced()
    .msg("사이를 나타내는 '간'을 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tags({Tag.관형사형전성어미, Tag.관형사, Tag.관형격조사})
    .AND(tag(Tag.의존명사), forms({"것"}))
    .if_not_spaced()
    .msg("'것'을 앞 말과 띄어 써야 합니다.")
    .build(),

    *rule()
    .NOT(tag_form(Tag.형용사, "달"))
    .tags({Tag.관형사형전성어미, Tag.관형사, Tag.관형격조사})
    .AND(tag(Tag.의존명사), forms({"거"}))
    .if_not_spaced()
    .NOT(tag_form(Tag.주격조사, "이"))
    .msg("'것'을 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tags({Tag.관형사형전성어미, Tag.관형사, Tag.관형격조사})
    .AND(tag(Tag.의존명사), forms({"채", "만큼", "바", "적", "둥", "듯", "지", "척", "리", "뻔", "만", "터", "줄", "대로", "김", "등"}))
    .if_not_spaced()
    .msg("'{form}'{을,를} 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tags({Tag.관형사형전성어미})
    .AND(tag(Tag.의존명사), forms({"분"}))
    .if_not_spaced()
    .msg("'{form}'{을,를} 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.의존명사, "방")
    .if_not_spaced()
    .msg("'한 방'으로 띄어 써야 합니다.")
    .build(),
]

_NNG = [
    *rule()
    .AND(tag(Tag.일반명사), forms({"글자", "소지"}))
    .tag_form(Tag.일반명사, "수")
    .if_not_spaced()
    .msg("수량을 나타내는 '수'는 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.일반명사), forms({"인원", "상당", "과반", "번지"}))
    .tag_form(Tag.일반명사, "수")
    .if_spaced()
    .msg("'수'를 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.고유명사)
    .tag_form(Tag.일반명사, "경")
    .if_not_spaced()
    .msg("작위를 나타내는 '경(卿)'은 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.일반명사, "자리")
    .if_not_spaced()
    .msg("'자리'를 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tags({Tag.일반명사, Tag.대명사, Tag.관형격조사, Tag.고유명사})
    .AND(tag(Tag.일반명사), forms({"편", "정도", "말"}))
    .if_not_spaced()
    .msg("'{form}'{을,를} 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "짓")
    .if_not_spaced()
    .msg("'짓'을 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "그")
    .tag_form(Tag.의존명사, "중")
    .if_spaced()
    .msg("'그 가운데서'의 의미인 경우, '그중'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "그")
    .tag_form(Tag.일반명사, "밖")
    .if_not_spaced()
    .tag_form(Tag.부사격조사, "에")
    .tag_form(Tag.보조사, "도")
    .msg("'그 밖'으로 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.대명사, "너")
    .tag_form(Tag.관형격조사, "의")
    .tag_form(Tag.의존명사, "놈")
    .if_spaced()
    .msg("'네놈'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.관형사), forms({"이", "그", "저"}))
    .AND(tag(Tag.의존명사), forms({"따위", "놈", "분"}))
    .if_spaced()
    .msg("'{form[0]} {form[1]}'{으로,로} 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.관형사), forms({"이", "그", "저"}))
    .AND(tag(Tag.의존명사), form("녀석"))
    .if_not_spaced()
    .msg("'{form[0]} 녀석'으로 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.관형사), forms({"이", "그", "저"}))
    .AND(tag(Tag.일반명사), forms({"곳"}))
    .if_spaced()
    .msg("'{form[0]} {form[1]}'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.관형사), forms({"이", "그", "저"}))
    .AND(tag(Tag.일반명사), forms({"자식", "사람"}))
    .if_not_spaced()
    .msg("'{form[0]} {form[1]}'으로 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "그")
    .AND(tag(Tag.일반명사), forms({"후", "자체", "틈"}))
    .if_not_spaced()
    .msg("'{form[0]} {form[1]}'{으로,로} 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "이")
    .AND(tag(Tag.일반명사), forms({"틈"}))
    .if_not_spaced()
    .msg("'{form[0]} {form[1]}'{으로,로} 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.관형사, "별")
    .AND(tag(Tag.의존명사), forms({"것", "거", "수"}))
    .if_spaced()
    .msg("'별다른 {form[1]}'{이라,라}는 의미의 '{form[0]}{form[1]}'{은,는} 한 단어이므로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.관형사, "별")
    .AND(tag(Tag.일반명사), forms({"말씀", "생각", "걱정"}))
    .if_spaced()
    .msg("'별다른 {form[1]}'{이라,라}는 의미의 '{form[0]}{form[1]}'{은,는} 한 단어이므로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.관형사, "첫")
    .AND(tag(Tag.일반명사), forms({"해", "날"}))
    .if_spaced()
    .msg("'첫{form[1]}'{으로,로} 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.일반명사, "때")
    .if_spaced()
    .msg("'한때'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "산")
    .tag_form(Tag.일반명사, "속")
    .if_spaced()
    .msg("'산속'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.일반명사), forms({"수건", "휴지"}))
    .tag_form(Tag.일반명사, "걸이")
    .if_spaced()
    .msg("'{form[0]}걸이'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "입")
    .AND(tag(Tag.일반명사), forms({"안", "속"}))
    .if_spaced()
    .msg("'입안'으로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "몸")
    .tag_form(Tag.일반명사, "속")
    .if_spaced()
    .msg("'몸속'으로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "눈")
    .tag_form(Tag.일반명사, "앞")
    .if_spaced()
    .msg("'눈앞'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.형용사, "달")
    .tag_form(Tag.관형사형전성어미, "ㄴ")
    .AND(tag(Tag.의존명사), forms({"것", "거"}))
    .if_spaced()
    .msg("'단 음식'을 가리킬 때는 '단{form[1]}'{으로,로} 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "단")
    .tag_form(Tag.수사, "둘")
    .if_spaced()
    .msg("'단둘'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "쓰")
    .tag_form(Tag.관형사형전성어미, "ㄹ")
    .tag_form(Tag.의존명사, "데")
    .if_spaced()
    .msg("'쓸데'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.관형사, "온")
    .tag_form(Tag.일반명사, "몸")
    .if_spaced()
    .msg("'몸 전체'를 의미할 경우, '온몸'으로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.형용사, "크")
    .tag_form(Tag.관형사형전성어미, "ㄴ")
    .tag_form(Tag.일반명사, "돈")
    .if_spaced()
    .msg("'큰돈'으로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "창")
    .tag_form(Tag.일반명사, "밖")
    .if_spaced()
    .msg("'창밖'으로 붙여 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.관형사, "한")
    .AND(tag(Tag.의존명사), forms({"쪽"}))
    .if_spaced()
    .msg("'한{form[1]}'{으로,로} 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "한")
    .AND(tag(Tag.일반명사), forms({"몫"}))
    .if_spaced()
    .msg("'한{form[1]}'{으로,로} 붙여 써야 합니다.")
    .build(),

    *rule()
    .NOT(tags({Tag.일반부사, Tag.관형사형전성어미}))
    .tag_form(Tag.동사, "비")
    .tag_form(Tag.관형사형전성어미, "ㄴ")
    .tag_form(Tag.일반명사, "방")
    .if_spaced()
    .msg("'빈방'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.관형사), forms({"오른", "왼"}))
    .tag_form(Tag.의존명사, "쪽")
    .if_spaced()
    .msg("'{form[0]}쪽'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.체언접두사, "날")
    .tag_form(Tag.의존명사, "것")
    .if_spaced()
    .msg("'날것'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.형용사, "쓰")
    .tag_form(Tag.관형사형전성어미, "ㄴ")
    .tag_form(Tag.일반명사, "맛")
    .if_spaced()
    .msg("'쓴맛'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "문")
    .tag_form(Tag.일반명사, "밖")
    .if_spaced()
    .msg("'문밖'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "그")
    .tag_form(Tag.일반명사, "동안")
    .if_spaced()
    .msg("'그동안'으로 붙여 써야 합니다.")
    .build(),
    
]

_NR = [
    *rule()
    .tag_form(Tag.관형사, "수")
    .AND(tag(Tag.수사,), forms({"천", "십", "백", "만"}))
    .if_spaced()
    .msg("'{form[0]}{form[1]}'{으로,로} 붙여 써야 합니다.")
    .build(),
]

_VV = [
    *rule()
    .tag_form(Tag.대명사, "뭐")
    .tag_form(Tag.동사, "하")
    .if_not_spaced()
    .any()
    .opt()
    .any()
    .opt()
    .tag_form(Tag.의존명사, "거")
    .msg("'뭐 하다'로 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.연결어미, "더니")
    .tag_form(Tag.대명사, "뭐")
    .tag_form(Tag.동사, "하")
    .if_not_spaced()
    .msg("'뭐 하다'로 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "잘못")
    .tag_form(Tag.동사, "되")
    .if_spaced()
    .msg("'잘못되다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "달")
    .tag_form(Tag.연결어미, "라")
    .tag_form(Tag.동사, "붙")
    .if_spaced()
    .msg("'달라붙다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "들르")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "붙")
    .if_spaced()
    .msg("'들러붙다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "뒤")
    .tag_form(Tag.부사격조사, "로")
    .tag_form(Tag.동사, "하")
    .if_spaced()
    .msg("'뒤로하다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "물")
    .tag_form(Tag.동사, "흐르")
    .if_not_spaced()
    .msg("'물 흐르다'로 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.연결어미)
    .tag_form(Tag.동사, "되")
    .if_not_spaced()
    .msg("'되다'를 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .NOT(tag(Tag.관형사형전성어미))
    .forms({"축복", "축하", "평가", "주목", "허락"})
    .tag_form(Tag.동사불규칙활용, "받")
    .if_spaced()
    .msg("'받다'를 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "야심")
    .tag_form(Tag.동사, "차")
    .if_not_spaced()
    .msg("'야심 차다'로 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "뒤따르")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "오")
    .if_spaced()
    .msg("'뒤따라오다'는 한 단어이므로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.동사, "말")
    .if_not_spaced()
    .msg("'말다'를 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "보잘것")
    .tag_form(Tag.형용사, "없")
    .if_spaced()
    .msg("'보잘것없다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사, "알")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "보")
    .if_spaced()
    .msg("'알아보다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.동사불규칙활용, "잡")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.동사, "당기")
    .if_spaced()
    .msg("'잡아당기다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "눈독")
    .tag_form(Tag.동사, "들이")
    .if_not_spaced()
    .msg("'눈독 들이다'로 띄어 써야 합니다.")
    .build(),

    *rule()
    .tag_form(Tag.동사, "타")
    .tag_form(Tag.연결어미, "고")
    .tag_form(Tag.동사, "나")
    .if_spaced()
    .msg("'천부적인'의 의미인 경우 '타고나다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반명사, "큰일")
    .tag_form(Tag.동사, "나")
    .if_not_spaced()
    .msg("'큰일 나다'로 띄어 써야 합니다.")
    .build(),
]

_VX = [
    *rule()
    .tag_form(Tag.연결어미, "고")
    .tag_form(Tag.보조용언, "싶")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "하")
    .if_not_spaced()
    .msg("'~고 싶어 하다'로 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.명사형전성어미, "기")
    .AND(tag(Tag.보조사), forms({"ㄴ", "는"}))
    .tag_form(Tag.보조용언, "하")
    .if_not_spaced()
    .msg("'기는/긴 하다'로 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.연결어미, "게")
    .tag_form(Tag.보조용언, "하")
    .tag_form(Tag.연결어미, "어")
    .tag_form(Tag.보조용언, "주")
    .if_not_spaced()
    .msg("'~게 해 주다'로 띄어 써야 합니다.")
    .build(),
]

_있다_없다_띄어쓰기_set = {"인기", "필요", "품위"}

_VA = [
    *rule()
    .forms({"걱정"})
    .OR(tag_form(Tag.형용사, "없"), tag_form(Tag.일반부사, "없이"))
    .if_not_spaced()
    .msg("'{form[0]} 없다'로 띄어 써야 합니다.")
    .build(),

    *rule()
    .forms({"꼼짝", "쓸데"})
    .OR(tag_form(Tag.형용사, "없"), tag_form(Tag.일반부사, "없이"))
    .if_spaced()
    .msg("'{form[0]}없다'로 붙여 써야 합니다.")
    .build(),

    *rule()
    .forms(_있다_없다_띄어쓰기_set)
    .OR(tag_form(Tag.형용사, "없"), tag_form(Tag.일반부사, "없이"))
    .if_not_spaced()
    .msg("'{form[0]} 없다'로 띄어 써야 합니다.")
    .build(),

    *rule()
    .forms(_있다_없다_띄어쓰기_set)
    .tag_form(Tag.동사, "있")
    .if_not_spaced()
    .msg("'{form[0]} 있다'로 띄어 써야 합니다.")
    .build(),
]

_VCP = [
    *rule()
    .tag(Tag.긍정지정사)
    .if_spaced()
    .tag(Tag.선어말어미)
    .msg("'이다'를 앞 말에 붙여 써야 합니다.")
    .build(),
]

_MAG = [
    *rule()
    .tag_form(Tag.일반부사, "내내")
    .if_not_spaced()
    .msg("'내내'를 앞 말과 띄어 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.의존명사, "번")
    .if_spaced()
    .NOT(form("더"))
    .NOT(form("더"))
    .opt()
    .NOT(form("더"))
    .opt()
    .AND(tag(Tag.연결어미), forms({"면", "으면"}))
    .msg("'한번 ~하면'의 형태가 쓰였을 경우에는 '한번'을 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사, "한")
    .tag_form(Tag.의존명사, "번")
    .if_spaced()
    .NOT(form("더"))
    .NOT(form("더"))
    .opt()
    .NOT(form("더"))
    .opt()
    .tag_form(Tag.보조용언, "두")
    .tag_form(Tag.연결어미, "어서")
    .msg("'한번 ~하면'의 형태가 쓰였을 경우에는 '한번'을 붙여 써야 합니다.")
    .build(),
]

_JX = [
    *rule()
    .tag(Tag.일반명사)
    .tag_form(Tag.부사격조사, "보다")
    .if_spaced()
    .tag_form(Tag.보조사, "는")
    .msg("비교의 의미인 '보다'는 앞 말과 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tags(TagGroup.체언)
    .tag_form(Tag.보조사, "밖에")
    .if_spaced()
    .msg("'밖에'를 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tags(TagGroup.체언)
    .tag_form(Tag.보조사, "조차")
    .if_spaced()
    .msg("'조차'를 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tags(TagGroup.체언)
    .AND(tag(Tag.보조사), forms({"야", "이야"}))
    .form("말")
    .if_spaced()
    .form("로")
    .msg("'~이야말로'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.관형사형전성어미)
    .tag_form(Tag.일반명사, "때")
    .if_not_spaced()
    .msg("'때'를 앞 말과 띄어 써야 합니다.")
    .build(),
]

_JKB = [
    *rule()
    .tag_form(Tag.부사격조사, "처럼")
    .if_spaced()
    .msg("'처럼'을 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tags({Tag.명사형전성어미, Tag.대명사, Tag.일반명사, Tag.고유명사, Tag.명사파생접미사})
    .tag_form(Tag.부사격조사, "보다")
    .if_spaced()
    .msg("비교의 의미인 '보다'는 앞 말에 붙여 써야 합니다.")
    .build(),
]

_EF = [
    *rule()
    .tag(Tag.종결어미)
    .if_spaced()
    .msg("어미를 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.관형사형전성어미), forms({"라는", "다는", "는"}))
    .form("군")
    .if_spaced()
    .msg("'-군'은 어미이므로, 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .AND(tag(Tag.연결어미), forms({"는군", "군"}))
    .tag_form(Tag.감탄사, "그래")
    .if_spaced()
    .msg("'~군 뒤의 '그래'는 어미이므로 앞 말과 붙여 써야 합니다.")
    .build(),
]

_EC = [
    *rule()
    .tag_form(Tag.연결어미, "자")
    .form("마")
    .if_spaced()
    .tag_form(Tag.연결어미, "자")
    .msg("'-자마자'로 붙여 써야 합니다. (예: 버튼을 누르자마자)")
    .build(),
    
    *rule()
    .tag_form(Tag.의존명사, "거")
    .tag(Tag.긍정지정사)
    .if_spaced()
    .AND(tag(Tag.연결어미), forms({"라고", "래서"}))
    .msg("'~래서', '랬'을 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag(Tag.긍정지정사)
    .tag_form(Tag.관형사형전성어미, "ㄹ")
    .form("수록")
    .if_spaced()
    .msg("'~일수록'으로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.보조사, "거나")
    .if_spaced()
    .msg("'~거나'를 앞 말에 붙여 써야 합니다.")
    .build(),
]

_ETM = [
    *rule()
    .AND(tags({Tag.일반명사, Tag.고유명사, Tag.명사파생접미사, Tag.대명사}), NOT(forms({"꿈", "한결", "굴뚝", "주옥", "감쪽", "쏜살", "악착", "벼락", "철벽", "철통", "찰떡", "불꽃", "목석", "실낱", "뚱딴지", "실날"})))
    .tag_form(Tag.형용사, "같")
    .if_not_spaced()
    .msg("'같다'를 앞 말과 띄어 써야 합니다.")
    .build(),
]

_XSA = [
    *rule()
    .NOT(tags({Tag.종결부호, Tag.닫는부호, Tag.줄임표}))
    .tag_form(Tag.형용사파생접미사규칙활용, "답")
    .if_spaced()
    .msg("'답다'를 앞 말에 붙여 써야 합니다.")
    .build(),
]

_XSN = [
    *rule()
    .tag_form(Tag.일반명사, "며칠")
    .tag_form(Tag.명사파생접미사, "째")
    .if_spaced()
    .msg("'며칠째'로 붙여 써야 합니다.")
    .build(),
]

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.NEED_ML_JUDGE)

_NEED_ML_JUDGE = [
    *rule()
    .tag_form(Tag.일반명사, "열")
    .tag_form(Tag.동사불규칙활용, "받")
    .if_spaced()
    .msg("'화나다'의 의미일 경우 '열받다'로 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.일반부사, "같이")
    .if_spaced()
    .msg("~처럼의 의미일 때는 '같이'를 붙여 써야 합니다.")
    .build(),
    
    # 오늘따라 운이 좋네.	오늘 따라 운이 좋네.
    *rule()
    .tag_form(Tag.동사, "따르")
    .if_spaced()
    .tag_form(Tag.연결어미, "어")
    .msg("'따라'를 앞 말에 붙여 써야 합니다.")
    .build(),
    
    *rule()
    .tag_form(Tag.관형사형전성어미, "ㄹ")
    .form("수록")
    .if_spaced()
    .msg("'ㄹ수록'은 어미이므로 앞 말에 붙여 써야 합니다. (예: 하면 할수록)")
    .build(),
]

SPACING_ERRORS = [
    *_SPACING_ERRORS,
    *_NNB,
    *_NNG,
    *_NR,
    *_VV,
    *_VX,
    *_VA,
    *_VCP,
    *_MAG,
    *_JX,
    *_JKB,
    *_EF,
    *_EC,
    *_ETM,
    *_XSA,
    *_XSN,
]