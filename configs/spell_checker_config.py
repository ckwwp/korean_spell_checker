from korean_spell_checker.configs.spell_checker_config_builder import *
from korean_spell_checker.models.interface import Tag, TagGroup, SpellErrorType
from korean_spell_checker.configs import spell_checker_config_meaning, spell_checker_config_spacing, spell_checker_config_specific, spell_checker_config_spelling, spell_checker_config_warning

# 규칙 작성 예시
def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.TEST)

TEST_SPELL_CHECK_RULES = [
    *rule()
    .tags({Tag.형용사, Tag.형용사불규칙활용})
    .tag_form(Tag.연결어미, "지")
    .tag_form(Tag.보조용언, "않")
    .form("는")
    .msg("'merge(({dform[0]}, {dtag[0]}), (\"지\", \"연결어미\")) 않은'이 올바른 표현입니다.").build(),
]

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.NEED_ML_JUDGE)

ML_TRAINED = [
    *rule()
    .id("지_띄어쓰기")
    .AND(tags({Tag.의존명사, Tag.대명사}), form("지")).if_spaced()
    .msg("'지'를 붙여 써야 합니다.").build(),
    
    *rule()
    .id("같이_붙여쓰기")
    .tags({Tag.일반명사, Tag.고유명사, Tag.명사형전성어미, Tag.명사파생접미사, Tag.대명사, Tag.숫자, Tag.알파벳}).context()
    .form("같이").if_spaced()
    .msg("~처럼의 의미일 때는 '같이'를 붙여 써야 합니다.").build(),
]

ML_LABELINGS = [
    *rule()
    .id("같이_붙여쓰기")
    .tags({Tag.일반명사, Tag.고유명사, Tag.명사형전성어미, Tag.명사파생접미사, Tag.대명사, Tag.숫자, Tag.알파벳}).context()
    .form("같이").if_spaced()
    .msg("~처럼의 의미일 때는 '같이'를 붙여 써야 합니다.").build(),
]

SPELL_CHECK_RULES: list[KoSpellRules] = [
    *spell_checker_config_spacing.GENERAL_SPACING_ERRORS,
    *spell_checker_config_spacing.SPACING_ERRORS,
    *spell_checker_config_spelling.SPELL_MISS_ERRORS,
    *spell_checker_config_meaning.MEANING_CONFLICT_ERRORS,
    # *spell_checker_config_warning.WARNINGS,
    *spell_checker_config_specific.KIWI_EXCEPTION_ERRORS
 ]