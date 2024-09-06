//! Rust module of the rimseval product.
//!
//! In this module, certain parts of the rimseval software that are especially slow in python
//! are implemented in Rust.
//!
//! The `lib.rs` only holds re-exports and interaction functions for python specific
//! things. All other functionality is implemented in submodules.

mod lst;

use pyo3::prelude::*;

/// Prints a message.
#[pyfunction]
fn hello() -> PyResult<String> {
    Ok("Hello from rimseval!".into())
}

#[pymodule]
fn _lowlevel(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello, m)?)?;
    Ok(())
}

//#[cfg(test)]
//mod tests {
//    use super::*;
//
//    #[test]
//    fn test_hello() {
//        assert_eq!(1, 1);
//    }
//}
