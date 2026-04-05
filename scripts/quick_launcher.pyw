import importlib
import os
import sys
import threading

# 더블클릭 실행 시 venv 및 프로젝트 루트 경로 고정
_project = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
_parent = os.path.dirname(_project)
_venv_site = os.path.join(_project, "venv", "Lib", "site-packages")
os.chdir(_project)
sys.path.insert(0, _parent)
sys.path.insert(1, _venv_site)

import webview

from korean_spell_checker.tokenizations.ko_tokenizer import KoTokenizer
from korean_spell_checker.models.interface import Tag
from korean_spell_checker.engines.spell_checker import SpellChecker
from korean_spell_checker.engines.raw_searcher import RawStringSearcher
import korean_spell_checker.configs.spell_checker_config_meaning as _spell_meaning_cfg
import korean_spell_checker.configs.spell_checker_config_spacing as _spell_spacing_cfg
import korean_spell_checker.configs.spell_checker_config_specific as _spell_specific_cfg
import korean_spell_checker.configs.spell_checker_config_spelling as _spell_spelling_cfg
import korean_spell_checker.configs.spell_checker_config_warning as _spell_warning_cfg
import korean_spell_checker.configs.spell_checker_config as _spell_cfg
import korean_spell_checker.configs.raw_string_searcher_config as _raw_cfg
from korean_spell_checker.reporters.html_reporter import highlight_text, get_error_type_name

HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Malgun Gothic', sans-serif; font-size: 14px;
    background: #f5f5f5;
  }

  /* ── 탭 헤더 ── */
  .tab-header {
    display: flex; background: #3a6fd5; padding: 0 12px;
    position: sticky; top: 0; z-index: 100;
  }
  .tab-btn {
    padding: 10px 18px; border: none; background: transparent;
    color: rgba(255,255,255,0.7); cursor: pointer; font-size: 13px;
    font-family: inherit; border-bottom: 3px solid transparent;
    transition: color 0.15s, border-color 0.15s;
  }
  .tab-btn:hover { color: white; }
  .tab-btn.active { color: white; border-bottom-color: white; }

  /* ── 탭 컨텐츠 ── */
  .tab-pane { display: none; padding: 16px; }
  .tab-pane.active { display: block; }

  /* ── 공통 컴포넌트 ── */
  h2 { margin-bottom: 12px; font-size: 15px; color: #333; }
  textarea {
    width: 100%; height: 80px; padding: 8px; border: 1px solid #ccc;
    border-radius: 4px; resize: vertical; font-family: inherit; font-size: 14px;
  }
  .toolbar {
    display: flex; align-items: center; gap: 10px; margin-top: 8px; flex-wrap: wrap;
  }
  button {
    padding: 6px 14px; border: none; border-radius: 4px;
    cursor: pointer; font-size: 13px; font-family: inherit;
  }
  button:disabled { background: #aaa !important; cursor: not-allowed; }
  .btn-primary { background: #4a7fe5; color: white; }
  .btn-primary:not(:disabled):hover { background: #3a6fd5; }
  .btn-danger  { background: #e55a5a; color: white; }
  .btn-danger:not(:disabled):hover  { background: #cc4444; }
  .btn-warning { background: #e5913a; color: white; }
  .btn-warning:not(:disabled):hover { background: #cc7a2a; }
  label { display: flex; align-items: center; gap: 4px; cursor: pointer; user-select: none; }
  .status { margin-top: 8px; font-size: 13px; color: #555; min-height: 18px; }
  .result-area { margin-top: 12px; }

  /* ── 토크나이저 테이블 ── */
  table.token-table {
    width: 100%; border-collapse: collapse; background: white;
    border-radius: 4px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
  table.token-table th {
    background: #4a7fe5; color: white; padding: 7px 10px;
    text-align: left; font-size: 13px;
  }
  table.token-table td { padding: 6px 10px; border-bottom: 1px solid #eee; font-size: 13px; }
  table.token-table tr:last-child td { border-bottom: none; }
  table.token-table tr:hover td { background: #f0f5ff; }
  .tag   { font-weight: bold; color: #4a7fe5; }
  .spaced { color: #e55a5a; font-size: 11px; }

  /* ── 맞춤법 검사: 하이라이트 미리보기 ── */
  .spell-preview {
    margin-top: 12px; padding: 10px 12px; background: white;
    border: 1px solid #ddd; border-radius: 4px; min-height: 48px;
    white-space: pre-wrap; word-break: break-word; line-height: 1.7;
    font-size: 14px; font-family: inherit;
  }
  .spell-preview:empty::before {
    content: '검사 결과가 여기에 표시됩니다.';
    color: #bbb;
  }
  .error-highlight {
    position: relative;
    text-decoration: underline;
    text-decoration-color: #ef4444;
    text-decoration-style: wavy;
    text-decoration-thickness: 1px;
    color: #dc2626;
    font-weight: 600;
    background: rgba(239,68,68,0.1);
    border-radius: 3px;
    cursor: help;
  }
  .error-highlight::before {
    content: attr(data-error-msg);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    margin-bottom: 8px;
    background: white;
    color: #333;
    padding: 8px 12px;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    white-space: pre-wrap;
    word-wrap: break-word;
    min-width: 200px;
    max-width: 320px;
    font-size: 12px;
    font-weight: 400;
    line-height: 1.5;
    opacity: 0; visibility: hidden;
    transition: opacity 0.15s, visibility 0.15s;
    z-index: 9999; pointer-events: none;
  }
  .error-highlight::after {
    content: '';
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    margin-bottom: 2px;
    border: 5px solid transparent;
    border-top-color: white;
    filter: drop-shadow(0 1px 1px rgba(0,0,0,0.1));
    opacity: 0; visibility: hidden;
    transition: opacity 0.15s, visibility 0.15s;
    z-index: 9999; pointer-events: none;
  }
  .error-highlight:hover::before,
  .error-highlight:hover::after { opacity: 1; visibility: visible; }

  /* ── 맞춤법 검사: 에러 목록 테이블 ── */
  table.error-table {
    width: 100%; border-collapse: collapse; background: white;
    border-radius: 4px; overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-top: 10px;
  }
  table.error-table th {
    background: #e55a5a; color: white; padding: 6px 10px;
    text-align: left; font-size: 12px;
  }
  table.error-table td {
    padding: 5px 10px; border-bottom: 1px solid #eee;
    font-size: 12px; vertical-align: top;
  }
  table.error-table tr:last-child td { border-bottom: none; }
  table.error-table tr:hover td { background: #fff5f5; }
  .err-type { font-weight: bold; color: #e55a5a; white-space: nowrap; }
  .err-path { font-size: 11px; color: #999; margin-top: 2px; font-family: monospace; }
  .no-errors { color: #22a355; font-size: 13px; margin-top: 8px; }
</style>
</head>
<body>

<div class="tab-header">
  <button class="tab-btn active" onclick="switchTab('tokenizer')">토크나이저</button>
  <button class="tab-btn"        onclick="switchTab('spell')">맞춤법 검사</button>
</div>

<!-- ════ 토크나이저 탭 ════ -->
<div id="pane-tokenizer" class="tab-pane active">
  <h2>토크나이저 결과 미리보기</h2>
  <textarea id="tkn-input" placeholder="토크나이징할 문장을 입력하세요.&#10;Enter로 검사, Shift+Enter로 줄바꿈"></textarea>
  <div class="toolbar">
    <button id="btn-tokenize" class="btn-primary" onclick="tokenize()">토크나이징</button>
    <button id="btn-tkn-rebuild" class="btn-warning" onclick="rebuildTokenizer()">재빌드</button>
    <label><input type="checkbox" id="detailed" checked> detailed</label>
  </div>
  <div class="status" id="tkn-status"></div>
  <div class="result-area" id="tkn-result"></div>
</div>

<!-- ════ 맞춤법 검사 탭 ════ -->
<div id="pane-spell" class="tab-pane">
  <h2>맞춤법 검사</h2>
  <textarea id="spell-input" placeholder="검사할 문장을 입력하세요.&#10;Enter로 검사, Shift+Enter로 줄바꿈"></textarea>
  <div class="toolbar">
    <button id="btn-spell-check"  class="btn-primary" onclick="runSpellCheck()">검사</button>
    <button id="btn-spell-rebuild" class="btn-warning" onclick="rebuildSpellRules()">규칙 재빌드</button>
    <div class="status" id="spell-status" style="margin-top:0; flex:1;"></div>
  </div>
  <div id="spell-preview" class="spell-preview"></div>
  <div id="spell-errors"></div>
</div>

<script>
/* ── 탭 전환 ── */
function switchTab(name) {
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('pane-' + name).classList.add('active');
  event.currentTarget.classList.add('active');
}

/* ════ 토크나이저 ════ */
function setTknLoading(on) {
  document.getElementById('btn-tokenize').disabled   = on;
  document.getElementById('btn-tkn-rebuild').disabled = on;
}
function setTknStatus(msg) {
  document.getElementById('tkn-status').textContent = msg;
}

function tokenize() {
  const text = document.getElementById('tkn-input').value.trim();
  if (!text) return;
  const detailed = document.getElementById('detailed').checked;
  setTknLoading(true);
  setTknStatus('토크나이징 중…');
  document.getElementById('tkn-result').innerHTML = '';

  pywebview.api.tokenize(text).then(result => {
    setTknLoading(false);
    if (result.error) { setTknStatus('오류: ' + result.error); return; }
    setTknStatus('완료 (' + result.tokens.length + '개 토큰)');
    renderTokenTable(result.tokens, detailed);
  });
}

function rebuildTokenizer() {
  setTknLoading(true);
  setTknStatus('토크나이저 재빌드 중…');
  document.getElementById('tkn-result').innerHTML = '';

  pywebview.api.rebuild_tokenizer().then(result => {
    setTknLoading(false);
    if (result.error) setTknStatus('오류: ' + result.error);
    else setTknStatus('재빌드 완료!');
  });
}

function renderTokenTable(tokens, detailed) {
  if (!tokens.length) {
    document.getElementById('tkn-result').innerHTML =
      '<div style="color:#888;margin-top:8px;">결과 없음</div>';
    return;
  }
  let headers, rows;
  if (detailed) {
    headers = ['#', 'form', 'tag', 'raw_form', 'lemma', 'word_position', 'spaced'];
    rows = tokens.map(t => [
      t.i, t.form, t.tag, t.raw_form, t.lemma, t.word_position,
      t.spaced ? '<span class="spaced">공백 있음</span>' : ''
    ]);
  } else {
    headers = ['#', 'form (base_form)', 'tag'];
    rows = tokens.map(t => [t.i, t.form + ' (' + t.base_form + ')', t.tag]);
  }
  const th = headers.map(h => '<th>' + h + '</th>').join('');
  const tbody = rows.map(cells => {
    const tds = cells.map((c, i) =>
      i === 2 ? '<td class="tag">' + c + '</td>' : '<td>' + c + '</td>'
    ).join('');
    return '<tr>' + tds + '</tr>';
  }).join('');
  document.getElementById('tkn-result').innerHTML =
    '<table class="token-table"><thead><tr>' + th + '</tr></thead><tbody>' + tbody + '</tbody></table>';
}

document.getElementById('tkn-input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); tokenize(); }
});

/* ════ 맞춤법 검사 ════ */
function setSpellLoading(on) {
  document.getElementById('btn-spell-check').disabled  = on;
  document.getElementById('btn-spell-rebuild').disabled = on;
  document.getElementById('spell-input').disabled      = on;
}
function setSpellStatus(msg) {
  document.getElementById('spell-status').textContent = msg;
}

document.getElementById('spell-input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); runSpellCheck(); }
});

function runSpellCheck() {
  const text = document.getElementById('spell-input').value;
  if (!text.trim()) return;
  setSpellLoading(true);
  setSpellStatus('검사 중…');
  document.getElementById('spell-preview').innerHTML = '';
  document.getElementById('spell-errors').innerHTML  = '';

  pywebview.api.spell_check(text).then(result => {
    setSpellLoading(false);
    if (result.error) { setSpellStatus('오류: ' + result.error); return; }
    const cnt = result.errors.length;
    setSpellStatus(cnt > 0 ? '오류 ' + cnt + '건 발견' : '오류 없음');
    renderSpellResult(result);
  });
}

function renderSpellResult(result) {
  document.getElementById('spell-preview').innerHTML = result.highlighted;

  const errDiv = document.getElementById('spell-errors');
  if (!result.errors.length) {
    errDiv.innerHTML = '<div class="no-errors">오류가 없습니다.</div>';
    return;
  }
  const th = '<tr><th>#</th><th>Type</th><th>Message</th></tr>';
  const tbody = result.errors.map((e, i) => {
    const path = e.debug_path
      ? '<div class="err-path">' + e.debug_path + '</div>' : '';
    return '<tr>'
      + '<td>' + (i + 1) + '</td>'
      + '<td class="err-type">' + e.type + '</td>'
      + '<td>' + e.msg + path + '</td>'
      + '</tr>';
  }).join('');
  errDiv.innerHTML =
    '<table class="error-table"><thead>' + th + '</thead><tbody>' + tbody + '</tbody></table>';
}

function rebuildSpellRules() {
  setSpellLoading(true);
  setSpellStatus('규칙 재빌드 중… (잠시 기다려 주세요)');
  document.getElementById('spell-preview').innerHTML = '';
  document.getElementById('spell-errors').innerHTML  = '';

  pywebview.api.rebuild_spell_checker().then(result => {
    setSpellLoading(false);
    if (result.error) setSpellStatus('오류: ' + result.error);
    else setSpellStatus('재빌드 완료!');
  });
}
</script>
</body>
</html>
"""


class Api:
    def __init__(self):
        self._tkn: KoTokenizer | None = None
        self._spell: SpellChecker | None = None
        self._raw: RawStringSearcher | None = None
        self._ready = False

    # ── 내부 헬퍼 ──────────────────────────────────────────────

    def _ensure_ready(self) -> dict | None:
        if not self._ready:
            return {"error": "초기화 중입니다. 잠시 후 다시 시도해주세요."}
        return None

    def _build_spell_checkers(self):
        importlib.reload(_spell_meaning_cfg)
        importlib.reload(_spell_spacing_cfg)
        importlib.reload(_spell_specific_cfg)
        importlib.reload(_spell_spelling_cfg)
        importlib.reload(_spell_warning_cfg)
        importlib.reload(_spell_cfg)
        importlib.reload(_raw_cfg)
        self._spell = SpellChecker(True)
        self._raw = RawStringSearcher()
        self._spell.add_rule_from_list(_spell_cfg.SPELL_CHECK_RULES)
        self._raw.add_word_from_list(_raw_cfg.RAW_STRING_RULES)

    # ── 토크나이저 API ──────────────────────────────────────────

    def tokenize(self, text: str) -> dict:
        if err := self._ensure_ready():
            return err
        try:
            raw = self._tkn.tokenize(text)
            if not raw:
                return {"tokens": []}
            tokens = []
            for i, token in enumerate(raw):
                spaced = i > 0 and (token.start - raw[i - 1].end > 0)
                tokens.append({
                    "i": i,
                    "form": token.form,
                    "tag": f"{Tag(token.tag).name}({token.tag})",
                    "base_form": getattr(token, "base_form", token.form),
                    "raw_form": getattr(token, "raw_form", ""),
                    "lemma": getattr(token, "lemma", ""),
                    "word_position": getattr(token, "word_position", ""),
                    "spaced": spaced,
                })
            return {"tokens": tokens}
        except Exception as e:
            return {"error": str(e)}

    def rebuild_tokenizer(self) -> dict:
        """KoTokenizer 인스턴스를 새로 생성합니다."""
        if err := self._ensure_ready():
            return err
        try:
            self._tkn = KoTokenizer.reset()
            self._tkn.tokenize("")  # 워밍업
            return {"ok": True}
        except Exception as e:
            return {"error": str(e)}

    # ── 맞춤법 검사 API ─────────────────────────────────────────

    def spell_check(self, text: str) -> dict:
        if err := self._ensure_ready():
            return err
        if not text:
            return {"highlighted": "", "errors": []}
        try:
            errors = list(self._raw.search(text))
            errors.extend(self._spell.check(self._tkn.tokenize(text)))

            highlighted = highlight_text(text, errors)
            error_list = [
                {
                    "type": get_error_type_name(e),
                    "msg": e.error_message,
                    "start": e.start_index,
                    "end": e.end_index,
                    "debug_path": e.debug_path or "",
                }
                for e in errors
            ]
            return {"highlighted": highlighted, "errors": error_list}
        except Exception as e:
            return {"error": str(e)}

    def rebuild_spell_checker(self) -> dict:
        """SpellChecker와 RawStringSearcher를 새로 생성하고 규칙을 재적용합니다."""
        if err := self._ensure_ready():
            return err
        self._ready = False
        try:
            self._build_spell_checkers()
            self._ready = True
            return {"ok": True}
        except Exception as e:
            self._ready = True
            return {"error": str(e)}


if __name__ == "__main__":
    api = Api()

    def init_all():
        print("■ 초기화 중…")
        api._tkn = KoTokenizer()
        api._tkn.tokenize("")  # 워밍업
        api._build_spell_checkers()
        api._ready = True
        print("■ 초기화 완료!")

    t = threading.Thread(target=init_all, daemon=True)
    t.start()

    window = webview.create_window(
        title="Korean Spell Checker Tools",
        html=HTML,
        js_api=api,
        width=860,
        height=680,
        text_select=True,
    )
    webview.start()
