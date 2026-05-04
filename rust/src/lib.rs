mod raw_searcher;
mod spell_checker;

use pyo3::prelude::*;
use raw_searcher::RustRawStringSearcher;
use spell_checker::RustSpellChecker;

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RustRawStringSearcher>()?;
    m.add_class::<RustSpellChecker>()?;
    Ok(())
}
