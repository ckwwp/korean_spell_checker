from korean_spell_checker.configs.spell_checker_config_builder import *
from korean_spell_checker.models.interface import Tag, TagGroup, SpellErrorType

def rule() -> RuleBuilder:
    return RuleBuilder(SpellErrorType.MEANING)

MEANING_CONFLICT_ERRORS: list[KoSpellRules] = [
    *rule()
    .tag_form(Tag.일반부사, "미리")
    .AND(tag(Tag.일반명사), forms({"예견", "예방", "예언", "예습", "예고"}))
    .msg("'미리'에 '예(予)'의 의미가 들어 있습니다.")
    .build(),

    *rule()
    .tag_form(Tag.일반명사, "부상")
    .tag_form(Tag.동사불규칙활용, "입")
    .msg("'부상'에 '입다'의 뜻이 포함되어 있습니다.")
    .build(),
]