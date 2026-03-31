HANGUL_COMP_START = ord("가")
HANGUL_COMP_END = ord("힣")
HANGUL_JAMO_START = ord("ㄱ")
HANGUL_JAMO_END = ord("ㅣ")

JONGSEONG_IDX_POINT = 28
JUNGSEONG_IDX_POINT = 21
CHOSEONG_IDX_POINT = JUNGSEONG_IDX_POINT * JONGSEONG_IDX_POINT

CHO_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
JUNG_LIST = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
JONG_LIST = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

CHO_SET = {i for i in CHO_LIST}
JUNG_SET = {i for i in JUNG_LIST}
JONG_SET = {i for i in JONG_LIST}
JAMO_SET = CHO_SET | JUNG_SET | JONG_SET - {''}
JAEUM_SET = CHO_SET | JONG_SET
JAMO_CHARCODE_SET = {ord(i) for i in JAMO_SET}

BATCHIM_REPLACE_MAP = {
    "ᆯ": "ㄹ",
    "ᆫ": "ᆫ"
}

def is_hangul(char: str):
    charpoint = chr(char)
    if HANGUL_COMP_START <= charpoint <= HANGUL_COMP_END or HANGUL_JAMO_START <= charpoint <= HANGUL_JAMO_END:
        return True
    return False

def convert_to_hangul_charpoint(char: str) -> int:
    return ord(char) - HANGUL_COMP_START

def is_jamo(char: str) -> bool:
    return char in JAMO_SET

def get_choseong(char: str) -> str:
    return CHO_LIST[(convert_to_hangul_charpoint(char) // CHOSEONG_IDX_POINT)]

def get_jungseong(char: str) -> str:
    return JUNG_LIST[(convert_to_hangul_charpoint(char) % CHOSEONG_IDX_POINT) // JONGSEONG_IDX_POINT]

def get_jongseong(char: str) -> str:
    return JONG_LIST[(convert_to_hangul_charpoint(char) % JONGSEONG_IDX_POINT)]
    