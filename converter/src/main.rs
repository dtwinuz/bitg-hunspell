//! Reads one token per line from stdin and writes the 2026-alphabet form, one per line.
//!
//! Dictionary data is already correctly spelled, so bitg's text-oriented helpers are turned off:
//! no apostrophe restoration ("boda" must stay "boda", not become "böda"), no English guard
//! (every entry is an Uzbek dictionary word) and no Cyrillic conversion.
use std::io::{self, BufRead, Write};

fn main() {
    let opts = bitg_core::Options {
        english_guard: false,
        restore_apostrophes: false,
        cyrillic: false,
        ..Default::default()
    };
    let stdin = io::stdin();
    let mut out = io::BufWriter::new(io::stdout().lock());
    for line in stdin.lock().lines() {
        let line = line.expect("stdin must be UTF-8");
        let converted = if line.is_empty() { String::new() } else { bitg_core::convert(&line, &opts) };
        writeln!(out, "{converted}").unwrap();
    }
}
