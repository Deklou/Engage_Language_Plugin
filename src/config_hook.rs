//! V10 diagnostic: ConfigMenu.OnInitialize() hook, Fire Emblem Engage 2.0.0.
//! No object field access, pointer chasing, mutation or pointer retention.
//! Ghidra VA 0x7102538570 => main NSO offset 0x2538570.

use core::ffi::c_void;
use std::sync::atomic::{AtomicUsize, Ordering};

static INITIALIZE_CALLS: AtomicUsize = AtomicUsize::new(0);

// Hypothesis for an IL2CPP instance method returning void:
// x0 = managed this; x1 = hidden MethodInfo pointer.
// This ABI has NOT yet been confirmed against the ARM64 prologue.
#[skyline::hook(offset = 0x2538570)]
fn config_menu_on_initialize(this: *mut c_void, method_info: *const c_void) {
    let call = INITIALIZE_CALLS.fetch_add(1, Ordering::Relaxed) + 1;
    if call <= 16 || call % 32 == 0 {
        skyline::println!(
            "[ELP V10] ConfigMenu.OnInitialize call={} this={:p} method={:p}",
            call, this, method_info
        );
    }
    // Preserve the game's actual initialization path.
    unsafe { original!()(this, method_info) };
}

pub fn install() {
    skyline::println!("[ELP V10] Installing ConfigMenu.OnInitialize diagnostic hook at 0x2538570");
    skyline::install_hook!(config_menu_on_initialize);
    skyline::println!("[ELP V10] Diagnostic hook installation requested");
}
