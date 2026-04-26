import gzip
import importlib
import os
import pickle
import re
import sys
import threading

if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# __file__ 절대경로 보장
_script = os.path.abspath(__file__)
_project = os.path.normpath(os.path.join(os.path.dirname(_script), ".."))
_parent = os.path.dirname(_project)
_venv_site = os.path.join(_project, "venv", "Lib", "site-packages")
os.chdir(_project)
_scripts = os.path.dirname(_script)
sys.path.insert(0, _parent)
sys.path.insert(1, _venv_site)
sys.path.insert(2, _scripts)

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
from bktree import BKTree
from jamo import h2j

HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  :root {
    --bg: #f1f5f9;
    --surface: #ffffff;
    --border: #e2e8f0;
    --text: #0f172a;
    --muted: #64748b;
    --subtle: #94a3b8;
    --accent: #4f46e5;
    --accent-dark: #4338ca;
    --accent-bg: rgba(79,70,229,0.07);
    --danger: #ef4444;
    --danger-dark: #dc2626;
    --danger-bg: rgba(239,68,68,0.07);
    --warning: #f59e0b;
    --warning-dark: #d97706;
    --warning-bg: rgba(245,158,11,0.09);
    --success: #10b981;
    --r-sm: 5px;
    --r: 8px;
    --r-lg: 12px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.07);
    --shadow: 0 3px 10px rgba(0,0,0,0.09), 0 1px 3px rgba(0,0,0,0.05);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Malgun Gothic', system-ui, -apple-system, sans-serif;
    font-size: 14px;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }

  /* ── 탭 헤더 ── */
  .tab-header {
    display: flex;
    background: #1e293b;
    padding: 0 16px;
    position: sticky;
    top: 0;
    z-index: 100;
    gap: 2px;
  }
  .tab-btn {
    padding: 11px 18px;
    border: none;
    background: transparent;
    color: rgba(255,255,255,0.5);
    cursor: pointer;
    font-size: 13px;
    font-family: inherit;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    transition: color 0.15s, border-color 0.15s;
    letter-spacing: 0.01em;
  }
  .tab-btn:hover { color: rgba(255,255,255,0.85); }
  .tab-btn.active { color: #fff; border-bottom-color: #818cf8; }

  /* ── 탭 컨텐츠 ── */
  .tab-pane { display: none; padding: 18px 16px; }
  .tab-pane.active { display: block; }

  /* ── 공통 컴포넌트 ── */
  h2 { margin-bottom: 14px; font-size: 15px; font-weight: 600; color: var(--text); }
  textarea {
    width: 100%; height: 80px; padding: 10px 12px;
    border: 1px solid var(--border); border-radius: var(--r);
    resize: vertical; font-family: inherit; font-size: 14px;
    background: var(--surface); color: var(--text);
    outline: none; transition: border-color 0.15s, box-shadow 0.15s;
  }
  textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(79,70,229,0.12);
  }
  .toolbar {
    display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap;
  }
  button {
    padding: 7px 15px; border: none; border-radius: var(--r-sm);
    cursor: pointer; font-size: 13px; font-family: inherit; font-weight: 500;
    transition: background 0.15s, box-shadow 0.15s, transform 0.1s;
  }
  button:active:not(:disabled) { transform: translateY(1px); }
  button:disabled { opacity: 0.42; cursor: not-allowed; }
  .btn-primary { background: var(--accent); color: #fff; box-shadow: 0 1px 3px rgba(79,70,229,0.3); }
  .btn-primary:not(:disabled):hover { background: var(--accent-dark); box-shadow: 0 2px 8px rgba(79,70,229,0.35); }
  .btn-danger  { background: var(--danger); color: #fff; box-shadow: 0 1px 3px rgba(239,68,68,0.3); }
  .btn-danger:not(:disabled):hover  { background: var(--danger-dark); box-shadow: 0 2px 8px rgba(239,68,68,0.35); }
  .btn-warning { background: var(--warning); color: #fff; box-shadow: 0 1px 3px rgba(245,158,11,0.3); }
  .btn-warning:not(:disabled):hover { background: var(--warning-dark); box-shadow: 0 2px 8px rgba(245,158,11,0.35); }
  label {
    display: flex; align-items: center; gap: 6px;
    cursor: pointer; user-select: none; font-size: 13px; color: var(--muted);
  }
  label input[type="checkbox"] { width: 15px; height: 15px; accent-color: var(--accent); cursor: pointer; }
  .status { margin-top: 8px; font-size: 12px; color: var(--muted); min-height: 16px; }
  .result-area { margin-top: 14px; }

  /* ── 토크나이저 테이블 ── */
  table.token-table {
    width: 100%; border-collapse: collapse; background: var(--surface);
    border-radius: var(--r); overflow: hidden; box-shadow: var(--shadow);
  }
  table.token-table th {
    background: #1e293b; color: rgba(255,255,255,0.85);
    padding: 9px 12px; text-align: left; font-size: 12px;
    font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase;
  }
  table.token-table td { padding: 7px 12px; border-bottom: 1px solid var(--border); font-size: 13px; }
  table.token-table tr:last-child td { border-bottom: none; }
  table.token-table tr:hover td { background: var(--accent-bg); }
  .tag   { font-weight: 600; color: var(--accent); }
  .spaced { color: var(--danger); font-size: 11px; font-weight: 500; }

  /* ── 맞춤법 검사: 하이라이트 미리보기 ── */
  .spell-preview {
    margin-top: 12px; padding: 12px 14px; background: var(--surface);
    border: 1px solid var(--border); border-radius: var(--r); min-height: 52px;
    white-space: pre-wrap; word-break: break-word; line-height: 1.8;
    font-size: 14px; font-family: inherit; box-shadow: var(--shadow-sm);
  }
  .spell-preview:empty::before {
    content: '검사 결과가 여기에 표시됩니다.';
    color: var(--subtle);
  }
  .error-highlight {
    position: relative;
    text-decoration: underline;
    text-decoration-color: #ef4444;
    text-decoration-style: wavy;
    text-decoration-thickness: 1.5px;
    color: #dc2626;
    font-weight: 600;
    background: rgba(239,68,68,0.09);
    border-radius: 3px;
    cursor: help;
    padding: 0 1px;
  }
  .error-highlight::before {
    content: attr(data-error-msg);
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    margin-bottom: 10px;
    background: #1e293b;
    color: #e2e8f0;
    padding: 8px 12px;
    border-radius: var(--r);
    box-shadow: var(--shadow);
    white-space: pre-wrap;
    word-wrap: break-word;
    min-width: 200px;
    max-width: 320px;
    font-size: 12px;
    font-weight: 400;
    line-height: 1.6;
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
    margin-bottom: 4px;
    border: 5px solid transparent;
    border-top-color: #1e293b;
    opacity: 0; visibility: hidden;
    transition: opacity 0.15s, visibility 0.15s;
    z-index: 9999; pointer-events: none;
  }
  .error-highlight:hover::before,
  .error-highlight:hover::after { opacity: 1; visibility: visible; }

  /* ── 맞춤법 검사: 에러 목록 테이블 ── */
  table.error-table {
    width: 100%; border-collapse: collapse; background: var(--surface);
    border-radius: var(--r); overflow: hidden;
    box-shadow: var(--shadow-sm); margin-top: 12px;
  }
  table.error-table th {
    background: var(--danger); color: #fff; padding: 8px 12px;
    text-align: left; font-size: 12px; font-weight: 500; letter-spacing: 0.03em;
  }
  table.error-table td {
    padding: 7px 12px; border-bottom: 1px solid var(--border);
    font-size: 12px; vertical-align: top;
  }
  table.error-table tr:last-child td { border-bottom: none; }
  table.error-table tr:hover td { background: var(--danger-bg); }
  .err-type { font-weight: 600; color: var(--danger); white-space: nowrap; }
  .err-path { font-size: 11px; color: var(--subtle); margin-top: 3px; font-family: monospace; }
  .no-errors { color: var(--success); font-size: 13px; font-weight: 500; margin-top: 10px; }

  /* ── 사전 검색 ── */
  .dict-sticky-search {
    position: sticky;
    top: 40px;
    background: var(--bg);
    margin: 0 -16px;
    padding: 0 16px 10px;
    z-index: 50;
  }
  .dict-search-row { display: flex; gap: 8px; }
  .dict-regex-label { margin-top: 7px; }
  .dict-input {
    flex: 1; padding: 8px 12px; border: 1px solid var(--border);
    border-radius: var(--r-sm); font-size: 14px; font-family: inherit;
    background: var(--surface); color: var(--text);
    outline: none; transition: border-color 0.15s, box-shadow 0.15s;
  }
  .dict-input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(79,70,229,0.12);
  }
  .dict-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--r); margin-top: 10px; overflow: hidden;
    box-shadow: var(--shadow-sm); transition: box-shadow 0.15s;
  }
  .dict-card:hover { box-shadow: var(--shadow); }
  .dict-card-header {
    display: flex; align-items: baseline; gap: 8px;
    padding: 10px 14px; background: var(--accent-bg); border-bottom: 1px solid var(--border);
  }
  .dict-word { font-size: 16px; font-weight: 700; color: var(--text); }
  .dict-pos-badge {
    font-size: 11px; padding: 2px 8px; border-radius: 999px;
    background: var(--accent); color: #fff; white-space: nowrap; font-weight: 500;
  }
  .dict-card-body { padding: 12px 14px; }
  .dict-sense {
    margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid var(--border);
  }
  .dict-sense:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: none; }
  .dict-sense-num { font-size: 12px; color: var(--subtle); margin-right: 4px; }
  .dict-definition { font-size: 13px; color: var(--text); line-height: 1.6; }
  .dict-examples { margin-top: 5px; padding-left: 12px; }
  .dict-example { font-size: 12px; color: var(--muted); line-height: 1.6; }
  .dict-example::before { content: '• '; color: var(--subtle); }
  .dict-source { font-size: 11px; color: var(--subtle); font-style: italic; margin-left: 4px; }
  .dict-no-result { color: var(--muted); font-size: 13px; margin-top: 12px; }
  .dict-not-loaded { color: var(--danger); font-size: 13px; margin-top: 12px; }

  /* ── 유사어 제안 ── */
  .dict-suggestion-box {
    margin-top: 12px; padding: 12px 14px; background: var(--warning-bg);
    border: 1px solid rgba(245,158,11,0.25); border-radius: var(--r);
    display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
  }
  .dict-suggestion-label {
    font-size: 13px; color: var(--warning-dark); font-weight: 600; white-space: nowrap;
  }
  .dict-suggestion-chip {
    padding: 4px 12px; border: 1px solid rgba(245,158,11,0.4); border-radius: 999px;
    background: var(--surface); color: var(--text); font-size: 13px; cursor: pointer;
    font-family: inherit; font-weight: 500; transition: background 0.12s, border-color 0.12s;
  }
  .dict-suggestion-chip:hover { background: var(--warning-bg); border-color: var(--warning); }
</style>
</head>
<body>

<div class="tab-header">
  <button class="tab-btn active" onclick="switchTab('tokenizer')">토크나이저</button>
  <button class="tab-btn"        onclick="switchTab('spell')">맞춤법 검사</button>
  <button class="tab-btn"        onclick="switchTab('dict')">사전 검색</button>
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

<!-- ════ 사전 검색 탭 ════ -->
<div id="pane-dict" class="tab-pane">
  <h2>사전 검색</h2>
  <div class="dict-sticky-search">
    <div class="dict-search-row">
      <input id="dict-input" type="text" class="dict-input"
             placeholder="검색어를 입력하세요 (부분 일치 지원)">
      <button class="btn-primary" onclick="dictSearch()">검색</button>
    </div>
    <label class="dict-regex-label">
      <input type="checkbox" id="dict-regex"> 정규식 (Regex)
    </label>
  </div>
  <div class="status" id="dict-status"></div>
  <div id="dict-results"></div>
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

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
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
      ? '<div class="err-path">' + escapeHtml(e.debug_path) + '</div>' : '';
    return '<tr>'
      + '<td>' + (i + 1) + '</td>'
      + '<td class="err-type">' + e.type + '</td>'
      + '<td>' + e.msg + path + '</td>'
      + '</tr>';
  }).join('');
  errDiv.innerHTML =
    '<table class="error-table"><thead>' + th + '</thead><tbody>' + tbody + '</tbody></table>';
}

/* ════ 사전 검색 ════ */
document.getElementById('dict-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') dictSearch();
});

document.getElementById('dict-regex').addEventListener('change', function() {
  const input = document.getElementById('dict-input');
  input.placeholder = this.checked
    ? '정규표현식을 입력하세요 (예: ^가나.*다$)'
    : '검색어를 입력하세요 (부분 일치 지원)';
});

function dictSearch() {
  const query = document.getElementById('dict-input').value.trim();
  if (!query) return;
  const useRegex = document.getElementById('dict-regex').checked;
  document.getElementById('dict-status').textContent = '검색 중…';
  document.getElementById('dict-results').innerHTML = '';

  pywebview.api.dict_search(query, useRegex).then(result => {
    if (result.error) {
      document.getElementById('dict-status').textContent = '';
      document.getElementById('dict-results').innerHTML =
        '<div class="dict-not-loaded">' + escapeHtml(result.error) + '</div>';
      return;
    }
    const items = result.items;
    document.getElementById('dict-status').textContent =
      items.length ? items.length + '건 (최대 100건)' : '';
    if (!items.length) {
      const sugg = result.suggestions;
      if (sugg && sugg.length) {
        document.getElementById('dict-results').innerHTML = renderSuggestions(sugg);
      } else {
        document.getElementById('dict-results').innerHTML =
          '<div class="dict-no-result">검색 결과가 없습니다.</div>';
      }
      return;
    }
    document.getElementById('dict-results').innerHTML = items.map(renderDictCard).join('');
  });
}

function renderDictCard(item) {
  const posBadges = item.pos_senses
    .filter(ps => ps.pos)
    .map(ps => '<span class="dict-pos-badge">' + escapeHtml(ps.pos) + '</span>')
    .join(' ');

  let sensesHtml = '';
  item.pos_senses.forEach(ps => {
    ps.senses.forEach((s, idx) => {
      const num = ps.senses.length > 1
        ? '<span class="dict-sense-num">' + (idx + 1) + '.</span>' : '';
      const examplesHtml = s.examples.map(ex => {
        const src = ex.source
          ? ' <span class="dict-source">(' + escapeHtml(ex.source) + ')</span>' : '';
        return '<div class="dict-example">'
          + escapeHtml(ex.example) + src + '</div>';
      }).join('');
      sensesHtml +=
        '<div class="dict-sense">'
        + '<div class="dict-definition">' + num + escapeHtml(s.definition) + '</div>'
        + (examplesHtml ? '<div class="dict-examples">' + examplesHtml + '</div>' : '')
        + '</div>';
    });
  });

  return '<div class="dict-card">'
    + '<div class="dict-card-header">'
    + '<span class="dict-word">' + escapeHtml(item.word) + '</span>'
    + posBadges
    + '</div>'
    + '<div class="dict-card-body">' + (sensesHtml || '') + '</div>'
    + '</div>';
}

let _dictSuggestions = [];

function renderSuggestions(suggestions) {
  _dictSuggestions = suggestions;
  const chips = suggestions.map((s, i) =>
    '<button class="dict-suggestion-chip" onclick="dictSearchFor(' + i + ')">'
    + escapeHtml(s.word) + '</button>'
  ).join('');
  return '<div class="dict-suggestion-box">'
    + '<span class="dict-suggestion-label">이것을 찾으셨나요?</span>'
    + chips
    + '</div>';
}

function dictSearchFor(idx) {
  const s = _dictSuggestions[idx];
  if (!s) return;
  document.getElementById('dict-input').value = s.word_plain;
  document.getElementById('dict-regex').checked = false;
  dictSearch();
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


_dict_pkl = os.path.join(_project, "dictionary", "dict.pkl")


class Api:
    def __init__(self):
        self._tkn: KoTokenizer | None = None
        self._spell: SpellChecker | None = None
        self._raw: RawStringSearcher | None = None
        self._ready = False
        self._dict_data: list | None = None
        self._dict_loaded = False
        self._bktree: BKTree | None = None
        self._word_index: dict[str, dict] = {}

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

    # ── 사전 검색 API ───────────────────────────────────────────

    def _load_dict(self) -> str | None:
        """pickle 로드 (최초 1회). 오류 메시지 반환, 없으면 None."""
        if self._dict_loaded:
            return None
        self._dict_loaded = True
        if not os.path.exists(_dict_pkl):
            return (f"사전 파일이 없습니다: {_dict_pkl}\n"
                    "build_dict_pickle.py를 실행해 먼저 생성해 주세요.")
        try:
            with gzip.open(_dict_pkl, 'rb') as f:
                data = pickle.load(f)
            if isinstance(data, list):
                # 구버전 포맷 (BK-Tree 없음)
                self._dict_data = data
            else:
                self._dict_data = data['entries']
                self._bktree = data.get('bktree')
            for entry in self._dict_data:
                wp = entry['word_plain']
                if wp not in self._word_index:
                    self._word_index[wp] = entry
        except Exception as e:
            self._dict_data = None
            return f"사전 파일 로드 오류: {e}"
        return None

    def _match_score(self, query: str, word: str) -> float:
        word_norm = re.sub(r'[0-9]', '', word) or word
        if word_norm == query:
            return 1.0
        if word_norm.startswith(query):
            return 0.8 + len(query) / len(word_norm) * 0.2
        return len(query) / len(word_norm)

    def _fuzzy_suggest(self, query: str) -> list[dict]:
        """BK-Tree 로 유사어 최대 5건 반환. 숫자·기호 제거 후 중복 제거."""
        if not self._bktree:
            return []
        jlen = len(h2j(query))
        threshold = 1 if jlen <= 3 else (2 if jlen <= 7 else 3)
        candidates = self._bktree.search(query, threshold)
        seen_raw: set[str] = set()    # BK-Tree 후보 중복 방지
        seen_clean: set[str] = set()  # 정리 후 표시 단어 중복 방지
        results: list[dict] = []
        for _, word in candidates:
            if word in seen_raw:
                continue
            seen_raw.add(word)
            entry = self._word_index.get(word)
            if not entry:
                continue
            clean_word = re.sub(r'[0-9^\-\s]', '', entry['word'])
            clean_plain = re.sub(r'[0-9^\-\s]', '', entry['word_plain'])
            if not clean_plain or clean_plain in seen_clean:
                continue
            seen_clean.add(clean_plain)
            results.append({**entry, 'word': clean_word, 'word_plain': clean_plain})
            if len(results) >= 5:
                break
        return results

    def dict_search(self, query: str, use_regex: bool = False) -> dict:
        if err := self._load_dict():
            return {"error": err}
        if not query or not self._dict_data:
            return {"items": []}
        if use_regex:
            try:
                pattern = re.compile(query)
                matched = [e for e in self._dict_data if pattern.search(e['word_plain'])]
            except re.error as ex:
                return {"error": f"정규식 오류: {ex}"}
            return {"items": matched[:100]}
        plain_query = re.sub(r'[-^]', '', query)
        matched = [e for e in self._dict_data if plain_query in e['word_plain']]
        if matched:
            matched.sort(key=lambda e: self._match_score(plain_query, e['word_plain']), reverse=True)
            return {"items": matched[:100]}
        suggestions = self._fuzzy_suggest(plain_query)
        return {"items": [], "suggestions": suggestions}

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
        try:
            api._tkn = KoTokenizer()
            api._tkn.tokenize("")
            api._build_spell_checkers()
            api._ready = True
        except Exception as e:
            with open(os.path.join(_project, "launcher_error.log"), "w", encoding="utf-8") as f:
                import traceback
                f.write(traceback.format_exc())

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
