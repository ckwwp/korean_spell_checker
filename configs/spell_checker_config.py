from korean_spell_checker.configs.spell_checker_config_builder import *
from korean_spell_checker.models.interface import Tag, TagGroup, SpellErrorType
from korean_spell_checker.configs import spell_checker_config_meaning, spell_checker_config_spacing, spell_checker_config_specific, spell_checker_config_spelling, spell_checker_config_warning

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.TEST)

_TEST_SPELL_CHECK_RULES = [
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
    .msg("'대로'를 붙여 써야 합니다.")
    .build(),
]

SPELL_CHECK_RULES: list[KoSpellRules] = [
    # *spell_checker_config_spacing.SPACING_ERRORS,
    # *spell_checker_config_spacing.SPACING_SPECIFIC_ERRORS,
    *spell_checker_config_spelling.SPELL_MISS_ERRORS,
    *spell_checker_config_meaning.MEANING_CONFLICT_ERRORS,
    *spell_checker_config_warning.WARNINGS,
    *spell_checker_config_specific.KIWI_EXCEPTION_ERRORS
 ]