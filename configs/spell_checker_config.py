from korean_spell_checker.configs.spell_checker_config_builder import *
from korean_spell_checker.models.interface import Tag, TagGroup, SpellErrorType
from korean_spell_checker.configs import spell_checker_config_meaning, spell_checker_config_spacing, spell_checker_config_specific, spell_checker_config_spelling, spell_checker_config_warning

# 규칙 작성 예시
def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.TEST)

_TEST_SPELL_CHECK_RULES = [
    *rule()
    .tag(Tag.연결어미)
    .AND(tag(Tag.보조용언), forms({"않"})).if_not_spaced()
    .AND(tag(Tag.관형사형전성어미), forms({"는", "은"}))
    .msg("'{form[0]}다'를 앞 말과 띄어 써야 합니다.").build(),
]

SPELL_CHECK_RULES = [
    *_TEST_SPELL_CHECK_RULES
]

SPELL_CHECK_RULES: list[KoSpellRules] = [
    *spell_checker_config_spacing.GENERAL_SPACING_ERRORS,
    *spell_checker_config_spacing.SPACING_ERRORS,
    *spell_checker_config_spelling.SPELL_MISS_ERRORS,
    *spell_checker_config_meaning.MEANING_CONFLICT_ERRORS,
    # *spell_checker_config_warning.WARNINGS,
    *spell_checker_config_specific.KIWI_EXCEPTION_ERRORS
 ]