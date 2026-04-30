use std::collections::HashMap;
use std::collections::HashSet;
use std::collections::VecDeque;
use pyo3::prelude::*;

struct TrieNode {
    children: HashMap<char, usize>,
    output: HashSet<(String, usize, String)>,
    fail: usize,
}

impl TrieNode {
    fn new() -> Self {
        TrieNode {
            children: HashMap::new(),
            output: HashSet::new(),
            fail: 0,
        }
    }
}

#[pyclass]
struct RawStringSearcher {
    nodes: Vec<TrieNode>,
    built: bool,
}

#[pymethods]
impl RawStringSearcher {
    #[new]
    fn new() -> Self {
        RawStringSearcher {
            nodes: vec![TrieNode::new()],
            built: false,
        }
    }

    fn add_word(&mut self, word: String, msg: String, error_type: String) {
        let mut curr_node: usize = 0;
        for ch in word.chars() {
            if !self.nodes[curr_node].children.contains_key(&ch) {
                let new_index = self.nodes.len();
                self.nodes.push(TrieNode::new());
                self.nodes[curr_node].children.insert(ch, new_index);
            }
            curr_node = self.nodes[curr_node].children[&ch];
        }
        self.nodes[curr_node].output.insert((msg, word.chars().count(), error_type));
    }

    fn build(&mut self) {
        let mut queue: VecDeque<usize> = VecDeque::new();
        let root_children: Vec<usize> = self.nodes[0].children.values().copied().collect();

        for child_idx in root_children {
            self.nodes[child_idx].fail = 0;
            queue.push_back(child_idx);
        }

        while let Some(node_idx) = queue.pop_front() {
            let children: Vec<(char, usize)> = self.nodes[node_idx].children.iter().map(|(&c, &idx)| (c, idx)).collect();
            for (ch, child_node) in children {
                let mut dest = self.nodes[child_node].fail;

                while dest != 0 && !self.nodes[dest].children.contains_key(&ch) {
                    dest = self.nodes[dest].fail;
                }

                if self.nodes[dest].children.contains_key(&ch)  {
                    self.nodes[child_node].fail = self.nodes[dest].children[&ch];
                    
                    let fail_idx = self.nodes[child_node].fail;
                    if !self.nodes[fail_idx].output.is_empty() {
                        let fail_output: HashSet<_> = self.nodes[fail_idx].output.clone();
                        self.nodes[child_node].output.extend(fail_output);
                    }
                } else {
                    self.nodes[child_node].fail = 0;
                }
                queue.push_back(child_node);
            }
        }
    }

    fn search(&self, word: &str) -> Vec<(String, String, usize, usize)> {
        let mut current = 0;
        let mut result = Vec::new();

        for (idx, ch) in word.chars().enumerate() {
            while current != 0 && !self.nodes[current].children.contains_key(&ch) {
                current = self.nodes[current].fail;
            }

            if let Some(&next) = self.nodes[current].children.get(&ch) {
                current = next;
                for (msg, len, error_type) in self.nodes[current].output.iter() {
                    result.push((error_type.clone(), msg.clone(), idx + 1 - len, idx + 1));
                }
            }
        }

        result
    }
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RawStringSearcher>()?;
    Ok(())
}