use std::collections::VecDeque;
use std::sync::OnceLock;
use rustc_hash::{FxHashMap, FxHashSet};
use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple};

// ── 조건 인코딩 ─────────────────────────────────────────────────
// Python encode() 결과:
//   Leaf:    (kind: u8, value)           kind 1~9
//   TagSet:  (10, list[int])
//   FormSet: (11, list[int])
//   And:     (12, list[ConditionEncoded])
//   Or:      (13, list[ConditionEncoded])
//   Not:     (14, ConditionEncoded)
//
// kind 1=Tag, 2=Form, 3=TagAndForm(tag_id, form_id), 4=Batchim, 5=AnyBatchim,
//      6=Length, 7=Lemma, 8=Any, 9=FirstToken

#[derive(Clone, Debug)]
enum Condition {
    Tag(u32),
    Form(u32),
    TagAndForm(u32, u32),
    Batchim(u32),
    AnyBatchim,
    Length(u32),
    Lemma(u32),
    Any,
    FirstToken,
    TagSet(Vec<u32>),
    FormSet(Vec<u32>),
    And(Vec<Condition>),
    Or(Vec<Condition>),
    Not(Box<Condition>),
}

fn parse_condition(obj: &Bound<'_, PyAny>) -> PyResult<Condition> {
    let t: &Bound<'_, PyTuple> = obj.downcast()?;
    let kind: u8 = t.get_item(0)?.extract()?;
    match kind {
        1 => Ok(Condition::Tag(t.get_item(1)?.extract()?)),
        2 => Ok(Condition::Form(t.get_item(1)?.extract()?)),
        3 => Ok(Condition::TagAndForm(t.get_item(1)?.extract()?, t.get_item(2)?.extract()?)),
        4 => Ok(Condition::Batchim(t.get_item(1)?.extract()?)),
        5 => Ok(Condition::AnyBatchim),
        6 => Ok(Condition::Length(t.get_item(1)?.extract()?)),
        7 => Ok(Condition::Lemma(t.get_item(1)?.extract()?)),
        8 => Ok(Condition::Any),
        9 => Ok(Condition::FirstToken),
        10 => {
            let ids: Vec<u32> = t.get_item(1)?.extract()?;
            Ok(Condition::TagSet(ids))
        }
        11 => {
            let ids: Vec<u32> = t.get_item(1)?.extract()?;
            Ok(Condition::FormSet(ids))
        }
        12 => {
            let list = t.get_item(1)?.downcast_into::<PyList>()?;
            let children: PyResult<Vec<_>> = list.iter().map(|x| parse_condition(&x)).collect();
            Ok(Condition::And(children?))
        }
        13 => {
            let list = t.get_item(1)?.downcast_into::<PyList>()?;
            let children: PyResult<Vec<_>> = list.iter().map(|x| parse_condition(&x)).collect();
            Ok(Condition::Or(children?))
        }
        14 => Ok(Condition::Not(Box::new(parse_condition(&t.get_item(1)?)?))),
        _ => Err(pyo3::exceptions::PyValueError::new_err(format!("unknown condition kind: {kind}"))),
    }
}

// ── 토큰 데이터 ──────────────────────────────────────────────────

struct EnrichedToken {
    tag_id: u32,
    form_id: u32,
    tag_and_form_id: (u32, u32),
    batchim_id: u32,
    has_batchim: bool,
    length: u32,
    lemma_id: u32,
    start: i64,
}

// ── NFA 노드 ──────────────────────────────────────────────────────

const NOT_STARTED: i32 = -1;

struct Transition {
    condition: Condition,
    target: usize,
    spacing: u8, // 0=ANY, 1=SPACED, 2=ATTACHED
    is_optional: bool,
    is_context: bool,
}

struct RuleNode {
    tag_trans: FxHashMap<u32, Vec<usize>>,
    form_trans: FxHashMap<u32, Vec<usize>>,
    tag_and_form_trans: FxHashMap<(u32, u32), Vec<usize>>,
    batchim_trans: FxHashMap<u32, Vec<usize>>,
    any_batchim_trans: Vec<usize>,
    fallback_trans: Vec<usize>,
    all_trans: Vec<usize>,
    optional_closure: Option<Vec<usize>>,
    output_msg_idx: Option<usize>,
    error_type_idx: usize,
    rule_id_idx: usize,
}

impl RuleNode {
    fn new() -> Self {
        RuleNode {
            tag_trans: FxHashMap::default(),
            form_trans: FxHashMap::default(),
            tag_and_form_trans: FxHashMap::default(),
            batchim_trans: FxHashMap::default(),
            any_batchim_trans: Vec::new(),
            fallback_trans: Vec::new(),
            all_trans: Vec::new(),
            optional_closure: None,
            output_msg_idx: None,
            error_type_idx: 0,
            rule_id_idx: 0,
        }
    }
}

// ── 조건 평가 ─────────────────────────────────────────────────────

fn condition_matches(cond: &Condition, tok: &EnrichedToken) -> bool {
    match cond {
        Condition::Tag(id) => tok.tag_id == *id,
        Condition::Form(id) => tok.form_id == *id,
        Condition::TagAndForm(tag_id, form_id) => tok.tag_id == *tag_id && tok.form_id == *form_id,
        Condition::Batchim(id) => tok.batchim_id == *id,
        Condition::AnyBatchim => tok.has_batchim,
        Condition::Length(n) => tok.length >= *n,
        Condition::Lemma(id) => tok.lemma_id == *id,
        Condition::Any => true,
        Condition::FirstToken => tok.start == 0,
        Condition::TagSet(ids) => ids.contains(&tok.tag_id),
        Condition::FormSet(ids) => ids.contains(&tok.form_id),
        Condition::And(children) => children.iter().all(|c| condition_matches(c, tok)),
        Condition::Or(children) => children.iter().any(|c| condition_matches(c, tok)),
        Condition::Not(child) => !condition_matches(child, tok),
    }
}

fn is_not_any_context(trans: &Transition) -> bool {
    matches!(&trans.condition, Condition::Not(_)) && trans.spacing == 0 && trans.is_context
}

fn conditions_equal(a: &Condition, b: &Condition) -> bool {
    match (a, b) {
        (Condition::Tag(x), Condition::Tag(y)) => x == y,
        (Condition::Form(x), Condition::Form(y)) => x == y,
        (Condition::TagAndForm(t1, f1), Condition::TagAndForm(t2, f2)) => t1 == t2 && f1 == f2,
        (Condition::Batchim(x), Condition::Batchim(y)) => x == y,
        (Condition::AnyBatchim, Condition::AnyBatchim) => true,
        (Condition::Length(x), Condition::Length(y)) => x == y,
        (Condition::Lemma(x), Condition::Lemma(y)) => x == y,
        (Condition::Any, Condition::Any) => true,
        (Condition::FirstToken, Condition::FirstToken) => true,
        (Condition::TagSet(a), Condition::TagSet(b)) => {
            let sa: FxHashSet<_> = a.iter().collect();
            let sb: FxHashSet<_> = b.iter().collect();
            sa == sb
        }
        (Condition::FormSet(a), Condition::FormSet(b)) => {
            let sa: FxHashSet<_> = a.iter().collect();
            let sb: FxHashSet<_> = b.iter().collect();
            sa == sb
        }
        (Condition::And(a), Condition::And(b)) | (Condition::Or(a), Condition::Or(b)) => {
            a.len() == b.len() && a.iter().zip(b.iter()).all(|(x, y)| conditions_equal(x, y))
        }
        (Condition::Not(a), Condition::Not(b)) => conditions_equal(a, b),
        _ => false,
    }
}

// ── 정적 테이블 ──────────────────────────────────────────────────

static TAG_TO_INT_MAP: OnceLock<FxHashMap<&'static str, u32>> = OnceLock::new();
static BATCHIM_TO_INT_MAP: OnceLock<FxHashMap<&'static str, u32>> = OnceLock::new();

static TAG_LIST: &[&str] = &[
    "NNG", "NNP", "NNB", "NR", "NP",
    "VV", "VV-R", "VV-I", "VA", "VA-R", "VA-I",
    "VX", "VX-R", "VX-I", "VCP", "VCN",
    "MM", "MAG", "MAJ", "IC",
    "JKS", "JKC", "JKG", "JKO", "JKB", "JKV", "JKQ", "JX", "JC",
    "EP", "EF", "EC", "ETN", "ETM",
    "XPN", "XSN", "XSV", "XSA", "XSA-R", "XSA-I", "XSM", "XR",
    "SF", "SP", "SS", "SSO", "SSC", "SE", "SO", "SW", "SL", "SH", "SN", "SB",
    "UN",
    "W_URL", "W_EMAIL", "W_HASHTAG", "W_MENTION", "W_SERIAL", "W_EMOJI",
    "Z_CODA", "Z_SIOT",
    "USER0", "USER1", "USER2", "USER3", "USER4",
];

// Python BATCHIM_LIST에서 비어있지 않은 항목 (인덱스 1부터 시작)
static BATCHIM_LIST_RS: &[&str] = &[
    "ᆨ", "ᆩ", "ᆪ", "ᆫ", "ᆬ", "ᆭ", "ᆮ", "ᆯ", "ᆰ", "ᆱ", "ᆲ", "ᆳ", "ᆴ", "ᆵ", "ᆶ",
    "ᆷ", "ᆸ", "ᆹ", "ᆺ", "ᆻ", "ᆼ", "ᆽ", "ᆾ", "ᆿ", "ᇀ", "ᇁ", "ᇂ",
];

// Python: is_jamo → form[-1] 그대로, else → get_compatible_batchim(form[-1]) = BATCHIM_LIST[(code-0xAC00)%28]
fn compute_batchim(form: &str) -> String {
    let last = match form.chars().next_back() {
        Some(c) => c,
        None => return String::new(),
    };
    let code = last as u32;
    // jamo 범위: 0x3131(ㄱ)~0x3163(ㅣ)
    if code >= 0x3131 && code <= 0x3163 {
        return last.to_string();
    }
    // 합성 한글: 0xAC00~0xD7A3
    if code >= 0xAC00 && code <= 0xD7A3 {
        let jong_idx = (code - 0xAC00) % 28;
        if jong_idx == 0 {
            return String::new();
        }
        // BATCHIM_LIST_RS는 인덱스 1부터 시작 (0은 "" 이므로 제외됨)
        // jong_idx 1 → BATCHIM_LIST_RS[0]
        if let Some(&b) = BATCHIM_LIST_RS.get((jong_idx - 1) as usize) {
            return b.to_string();
        }
    }
    String::new()
}

fn tag_to_int(tag: &str) -> u32 {
    TAG_TO_INT_MAP.get_or_init(|| {
        TAG_LIST.iter().enumerate().map(|(i, &s)| (s, i as u32)).collect()
    }).get(tag).copied().unwrap_or(u32::MAX)
}

fn batchim_to_int(b: &str) -> u32 {
    BATCHIM_TO_INT_MAP.get_or_init(|| {
        BATCHIM_LIST_RS.iter().enumerate().map(|(i, &s)| (s, (i + 1) as u32)).collect()
    }).get(b).copied().unwrap_or(0)
}

// ── PyO3 클래스 ───────────────────────────────────────────────────

#[pyclass]
pub struct RustSpellChecker {
    nodes: Vec<RuleNode>,
    transitions: Vec<Transition>,
    strings: Vec<String>,
    py_messages: Vec<PyObject>,
    py_error_types: Vec<PyObject>,
    py_rule_ids: Vec<PyObject>,
    is_frozen: bool,
}

#[pymethods]
impl RustSpellChecker {
    #[new]
    fn new() -> Self {
        let mut nodes = Vec::with_capacity(256);
        nodes.push(RuleNode::new());
        RustSpellChecker {
            nodes,
            transitions: Vec::new(),
            strings: Vec::new(),
            py_messages: Vec::new(),
            py_error_types: Vec::new(),
            py_rule_ids: Vec::new(),
            is_frozen: false,
        }
    }

    fn set_strings(&mut self, strings: Vec<String>) {
        self.strings = strings;
    }

    fn add_rule(&mut self, py: Python<'_>, encoded_rule: &Bound<'_, PyTuple>) -> PyResult<()> {
        if self.is_frozen {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(
                "You cannot add rules after calling 'check' function.",
            ));
        }

        let steps_list = encoded_rule.get_item(0)?.downcast_into::<PyList>()?;
        let compiled_msg: PyObject = encoded_rule.get_item(1)?.into_py(py);
        let error_type: PyObject = encoded_rule.get_item(2)?.into_py(py);
        let rule_id: PyObject = encoded_rule.get_item(3)?.into_py(py);

        if steps_list.is_empty() {
            return Ok(());
        }

        let msg_idx = self.py_messages.len();
        self.py_messages.push(compiled_msg);
        let et_idx = self.py_error_types.len();
        self.py_error_types.push(error_type);
        let rid_idx = self.py_rule_ids.len();
        self.py_rule_ids.push(rule_id);

        let mut current_node = 0usize;

        for step_obj in steps_list.iter() {
            let step: &Bound<'_, PyTuple> = step_obj.downcast()?;
            let cond_obj = step.get_item(0)?;
            let spacing: u8 = step.get_item(1)?.extract()?;
            let is_optional: bool = step.get_item(2)?.extract()?;
            let is_context: bool = step.get_item(3)?.extract()?;

            let condition = parse_condition(&cond_obj)?;

            let existing = self.find_transition(current_node, &condition, spacing, is_optional, is_context);
            current_node = if let Some(target) = existing {
                target
            } else {
                let new_node = self.nodes.len();
                self.nodes.push(RuleNode::new());

                let trans_idx = self.transitions.len();
                self.transitions.push(Transition {
                    condition: condition.clone(),
                    target: new_node,
                    spacing,
                    is_optional,
                    is_context,
                });

                self.add_transition_to_node(current_node, &condition, trans_idx);
                self.nodes[current_node].all_trans.push(trans_idx);

                new_node
            };
        }

        self.nodes[current_node].output_msg_idx = Some(msg_idx);
        self.nodes[current_node].error_type_idx = et_idx;
        self.nodes[current_node].rule_id_idx = rid_idx;

        Ok(())
    }

    fn check(&mut self, py: Python<'_>, tokens: &Bound<'_, PyList>) -> PyResult<Vec<PyObject>> {
        if self.nodes[0].all_trans.is_empty() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "You must have at least one rule to check spelling.",
            ));
        }
        self.is_frozen = true;
        self.build_optional_closures();

        let enriched = self.parse_tokens(tokens)?;
        let n = enriched.len();

        let token_starts: Vec<i64> = tokens.iter()
            .map(|t| t.getattr("start").and_then(|v| v.extract()))
            .collect::<PyResult<_>>()?;
        let token_ends: Vec<i64> = tokens.iter()
            .map(|t| t.getattr("end").and_then(|v| v.extract()))
            .collect::<PyResult<_>>()?;

        let mut active_cursors: FxHashMap<usize, (i32, i32)> = FxHashMap::default();
        let mut next_cursors: FxHashMap<usize, (i32, i32)> = FxHashMap::default();
        let mut expanded_cursors: FxHashMap<usize, (i32, i32)> = FxHashMap::default();
        let mut yielded_outputs: FxHashSet<(usize, i32)> = FxHashSet::default();
        let mut result_errors: Vec<PyObject> = Vec::new();
        // (et_idx, start_char, end_char, rid_idx, _dummy)
        let mut current_step_errors: FxHashMap<String, (usize, i64, i64, usize, i64)> = FxHashMap::default();

        for i in 0..n {
            let tok = &enriched[i];
            let has_space = if i > 0 { token_starts[i] - token_ends[i - 1] > 0 } else { false };

            active_cursors.insert(0, (NOT_STARTED, i as i32));
            expanded_cursors.clear();

            // Phase 1: epsilon closure 확장
            for (&node, &idxs) in &active_cursors {
                let (si, _) = idxs;
                if !expanded_cursors.contains_key(&node) || si > expanded_cursors[&node].0 {
                    expanded_cursors.insert(node, idxs);
                }
                let closure = self.nodes[node].optional_closure.clone().unwrap_or_default();
                for &cn in &closure {
                    if !expanded_cursors.contains_key(&cn) || si > expanded_cursors[&cn].0 {
                        expanded_cursors.insert(cn, idxs);
                    }
                }
            }

            // BOS epsilon: i==0에서 NOT 전이를 엡실론으로 처리
            if i == 0 {
                let mut bos_queue: VecDeque<(usize, (i32, i32))> =
                    expanded_cursors.iter().map(|(&k, &v)| (k, v)).collect();

                while let Some((cur_node, (si, ei))) = bos_queue.pop_front() {
                    let fallbacks: Vec<usize> = self.nodes[cur_node].fallback_trans.clone();
                    for ti in fallbacks {
                        let trans = &self.transitions[ti];
                        if !matches!(&trans.condition, Condition::Not(_))
                            || trans.spacing != 0
                            || !trans.is_context
                        {
                            continue;
                        }
                        let target = trans.target;
                        let new_si = if si == NOT_STARTED && !trans.is_context { i as i32 } else { si };
                        let new_ei = if !trans.is_context { i as i32 } else { ei };

                        if !expanded_cursors.contains_key(&target) || new_si > expanded_cursors[&target].0 {
                            expanded_cursors.insert(target, (new_si, new_ei));
                            bos_queue.push_back((target, (new_si, new_ei)));

                            let opt_closure = self.nodes[target].optional_closure.clone().unwrap_or_default();
                            for on in opt_closure {
                                if !expanded_cursors.contains_key(&on) || new_si > expanded_cursors[&on].0 {
                                    expanded_cursors.insert(on, (new_si, new_ei));
                                    bos_queue.push_back((on, (new_si, new_ei)));
                                }
                            }
                        }
                    }
                }
            }

            // Phase 2: 출력 수집 & 전이 탐색
            next_cursors.clear();
            current_step_errors.clear();

            let expanded_snapshot: Vec<(usize, (i32, i32))> =
                expanded_cursors.iter().map(|(&k, &v)| (k, v)).collect();

            for (node, (si, ei)) in &expanded_snapshot {
                let node = *node;
                let si = *si;
                let ei = *ei;

                if let Some(msg_idx) = self.nodes[node].output_msg_idx {
                    if si < i as i32 && !yielded_outputs.contains(&(msg_idx, si)) {
                        yielded_outputs.insert((msg_idx, si));
                        let rendered = self.render_message(py, msg_idx, tokens, si as usize, ei as usize)?;
                        let start_char = token_starts[si as usize];
                        let end_char = token_ends[ei as usize];
                        let et_idx = self.nodes[node].error_type_idx;
                        let rid_idx = self.nodes[node].rule_id_idx;
                        self.update_shortest_match(&mut current_step_errors, rendered, et_idx, start_char, end_char, rid_idx);
                    }
                }

                // 전이 후보 수집
                let mut candidates: Vec<usize> = Vec::new();
                if let Some(tl) = self.nodes[node].tag_and_form_trans.get(&tok.tag_and_form_id) {
                    candidates.extend_from_slice(tl);
                }
                if let Some(tl) = self.nodes[node].tag_trans.get(&tok.tag_id) {
                    candidates.extend_from_slice(tl);
                }
                if let Some(tl) = self.nodes[node].form_trans.get(&tok.form_id) {
                    candidates.extend_from_slice(tl);
                }
                if tok.has_batchim {
                    if let Some(tl) = self.nodes[node].batchim_trans.get(&tok.batchim_id) {
                        candidates.extend_from_slice(tl);
                    }
                    candidates.extend_from_slice(&self.nodes[node].any_batchim_trans.clone());
                }
                let fallbacks: Vec<usize> = self.nodes[node].fallback_trans.clone();
                for ti in fallbacks {
                    if condition_matches(&self.transitions[ti].condition, tok) {
                        candidates.push(ti);
                    }
                }

                for ti in candidates {
                    let trans = &self.transitions[ti];
                    if trans.spacing == 1 && !has_space { continue; }
                    if trans.spacing == 2 && has_space { continue; }

                    let target = trans.target;
                    let new_si = if si == NOT_STARTED && !trans.is_context { i as i32 } else { si };
                    let new_ei = if !trans.is_context { i as i32 } else { ei };

                    if !next_cursors.contains_key(&target) || new_si > next_cursors[&target].0 {
                        next_cursors.insert(target, (new_si, new_ei));
                    }
                }
            }

            // Phase 3: 에러 yield
            for (msg_str, (et_idx, start_char, end_char, rid_idx, _)) in &current_step_errors {
                result_errors.push(self.build_spell_error(py, *et_idx, msg_str, *start_char, *end_char, *rid_idx)?);
            }

            std::mem::swap(&mut active_cursors, &mut next_cursors);
        }

        // EOF epsilon
        if n > 0 {
            let mut final_expanded: FxHashMap<usize, (i32, i32)> = FxHashMap::default();
            let mut eof_queue: VecDeque<(usize, (i32, i32))> =
                active_cursors.iter().map(|(&k, &v)| (k, v)).collect();

            while let Some((node, idxs)) = eof_queue.pop_front() {
                let (si, _) = idxs;
                if final_expanded.contains_key(&node) && si <= final_expanded[&node].0 {
                    continue;
                }
                final_expanded.insert(node, idxs);

                let all_trans: Vec<usize> = self.nodes[node].all_trans.clone();
                for ti in all_trans {
                    let trans = &self.transitions[ti];
                    if trans.is_optional || is_not_any_context(trans) {
                        let target = trans.target;
                        if !final_expanded.contains_key(&target) || si > final_expanded[&target].0 {
                            eof_queue.push_back((target, idxs));
                        }
                    }
                }
            }

            let mut final_step_errors: FxHashMap<String, (usize, i64, i64, usize, i64)> = FxHashMap::default();

            for (&node, &(si, ei)) in &final_expanded {
                if let Some(msg_idx) = self.nodes[node].output_msg_idx {
                    if !yielded_outputs.contains(&(msg_idx, si)) {
                        let rendered = self.render_message(py, msg_idx, tokens, si as usize, ei as usize)?;
                        let start_char = token_starts[si as usize];
                        let end_char = token_ends[ei as usize];
                        let et_idx = self.nodes[node].error_type_idx;
                        let rid_idx = self.nodes[node].rule_id_idx;
                        self.update_shortest_match(&mut final_step_errors, rendered, et_idx, start_char, end_char, rid_idx);
                    }
                }
            }

            for (msg_str, (et_idx, start_char, end_char, rid_idx, _)) in &final_step_errors {
                result_errors.push(self.build_spell_error(py, *et_idx, msg_str, *start_char, *end_char, *rid_idx)?);
            }
        }

        Ok(result_errors)
    }
}

impl RustSpellChecker {
    fn find_transition(&self, node: usize, cond: &Condition, spacing: u8, is_optional: bool, is_context: bool) -> Option<usize> {
        let candidates: &[usize] = match cond {
            Condition::TagAndForm(tag_id, form_id) =>
                self.nodes[node].tag_and_form_trans.get(&(*tag_id, *form_id)).map(|v| v.as_slice()).unwrap_or(&[]),
            Condition::Tag(id) =>
                self.nodes[node].tag_trans.get(id).map(|v| v.as_slice()).unwrap_or(&[]),
            Condition::Form(id) =>
                self.nodes[node].form_trans.get(id).map(|v| v.as_slice()).unwrap_or(&[]),
            Condition::Batchim(id) =>
                self.nodes[node].batchim_trans.get(id).map(|v| v.as_slice()).unwrap_or(&[]),
            Condition::AnyBatchim =>
                &self.nodes[node].any_batchim_trans,
            _ => &self.nodes[node].fallback_trans,
        };

        for &ti in candidates {
            let t = &self.transitions[ti];
            if t.spacing != spacing || t.is_optional != is_optional || t.is_context != is_context {
                continue;
            }
            // Tag/Form/TagAndForm/Batchim/AnyBatchim은 테이블 키로 이미 구분됨
            match cond {
                Condition::Tag(_) | Condition::Form(_) | Condition::TagAndForm(_, _)
                | Condition::Batchim(_) | Condition::AnyBatchim => return Some(t.target),
                _ => {
                    if conditions_equal(&t.condition, cond) {
                        return Some(t.target);
                    }
                }
            }
        }
        None
    }

    fn add_transition_to_node(&mut self, node: usize, cond: &Condition, trans_idx: usize) {
        match cond {
            Condition::TagAndForm(tag_id, form_id) => {
                self.nodes[node].tag_and_form_trans.entry((*tag_id, *form_id)).or_default().push(trans_idx);
            }
            Condition::Tag(id) => {
                self.nodes[node].tag_trans.entry(*id).or_default().push(trans_idx);
            }
            Condition::Form(id) => {
                self.nodes[node].form_trans.entry(*id).or_default().push(trans_idx);
            }
            Condition::Batchim(id) => {
                self.nodes[node].batchim_trans.entry(*id).or_default().push(trans_idx);
            }
            Condition::AnyBatchim => {
                self.nodes[node].any_batchim_trans.push(trans_idx);
            }
            _ => {
                self.nodes[node].fallback_trans.push(trans_idx);
            }
        }
    }

    fn build_optional_closures(&mut self) {
        for node_idx in 0..self.nodes.len() {
            if self.nodes[node_idx].optional_closure.is_some() {
                continue;
            }
            let mut closure: Vec<usize> = Vec::new();
            let mut queue: VecDeque<usize> = VecDeque::new();
            let mut visited: FxHashSet<usize> = FxHashSet::default();
            visited.insert(node_idx);
            queue.push_back(node_idx);

            while let Some(cur) = queue.pop_front() {
                for &ti in &self.nodes[cur].all_trans.clone() {
                    let trans = &self.transitions[ti];
                    if trans.is_optional && !visited.contains(&trans.target) {
                        visited.insert(trans.target);
                        closure.push(trans.target);
                        queue.push_back(trans.target);
                    }
                }
            }
            self.nodes[node_idx].optional_closure = Some(closure);
        }
    }

    fn parse_tokens(&self, tokens: &Bound<'_, PyList>) -> PyResult<Vec<EnrichedToken>> {
        tokens.iter().map(|t| {
            let form: String = t.getattr("form")?.extract()?;
            let tag: String = t.getattr("tag")?.extract()?;
            let lemma: String = t.getattr("lemma")?.extract()?;
            let start: i64 = t.getattr("start")?.extract()?;
            let end: i64 = t.getattr("end")?.extract()?;

            // Python spell_checker._check_impl과 동일한 방식으로 batchim 계산:
            //   last_char이 jamo이면 last_char 그대로, 아니면 get_compatible_batchim(last_char)
            let batchim_str = compute_batchim(&form);

            let form_id = self.strings.iter().position(|s| s == &form).map(|i| i as u32).unwrap_or(u32::MAX);
            let tag_id = tag_to_int(&tag);
            let lemma_id = self.strings.iter().position(|s| s == &lemma).map(|i| i as u32).unwrap_or(u32::MAX);
            let batchim_id = batchim_to_int(&batchim_str);
            let has_batchim = !batchim_str.is_empty();
            let length = (end - start) as u32;

            Ok(EnrichedToken {
                tag_id,
                form_id,
                tag_and_form_id: (tag_id, form_id),
                batchim_id,
                has_batchim,
                length,
                lemma_id,
                start,
            })
        }).collect()
    }

    fn render_message(&self, py: Python<'_>, msg_idx: usize, tokens: &Bound<'_, PyList>, start: usize, end: usize) -> PyResult<String> {
        let msg_obj = self.py_messages[msg_idx].bind(py);
        let token_slice = tokens.get_slice(start, end + 1);
        msg_obj.call_method1("render", (token_slice,))?.extract()
    }

    fn update_shortest_match(
        &self,
        storage: &mut FxHashMap<String, (usize, i64, i64, usize, i64)>,
        msg: String,
        et_idx: usize,
        start: i64,
        end: i64,
        rid_idx: usize,
    ) {
        let new_len = end - start;
        match storage.get(&msg) {
            None => { storage.insert(msg, (et_idx, start, end, rid_idx, 0)); }
            Some(&(_, old_start, old_end, _, _)) => {
                let old_len = old_end - old_start;
                if new_len < old_len || (new_len == old_len && start > old_start) {
                    storage.insert(msg, (et_idx, start, end, rid_idx, 0));
                }
            }
        }
    }

    fn build_spell_error(&self, py: Python<'_>, et_idx: usize, msg_str: &str, start: i64, end: i64, rid_idx: usize) -> PyResult<PyObject> {
        let iface = py.import_bound("korean_spell_checker.models.interface")?;
        let spell_error_cls = iface.getattr("SpellError")?;
        let error_type = self.py_error_types[et_idx].bind(py);
        let rule_id = self.py_rule_ids[rid_idx].bind(py);
        let obj = spell_error_cls.call((error_type, msg_str, start, end, rule_id), None)?;
        Ok(obj.unbind())
    }
}
