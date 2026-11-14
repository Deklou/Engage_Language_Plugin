//! V10.1 diagnostic for Fire Emblem Engage 2.0.0.
//! Observe two Ghidra-confirmed code addresses without reading or storing menu pointers.
//! Hook signatures are hypotheses pending ARM64 ABI verification in Ghidra.

use core::ffi::c_void;
use std::sync::atomic::{AtomicUsize, Ordering};

static INITIALIZE_CALLS: AtomicUsize = AtomicUsize::new(0);
static CREATE_CALLS: AtomicUsize = AtomicUsize::new(0);

// Ghidra VA 0x7102538570 (assuming main text base 0x7100000000).
// Assumed IL2CPP instance method: void(this, MethodInfo*).
#[skyline::hook(offset = 0x2538570)]
fn config_menu_on_initialize(this: *mut c_void, method_info: *const c_void) {
    let n = INITIALIZE_CALLS.fetch_add(1, Ordering::Relaxed) + 1;
    if n <= 16 || n % 32 == 0 {
        skyline::println!(
            "[ELP V10.1] OnInitialize called #{} this={:p} method={:p}",
            n, this, method_info
        );
    }
    original!()(this, method_info);
}

// Ghidra VA 0x710253A470. ConfigSequence.CreateConfigMenu() invokes
// ConfigMenu.CreateBind() and assigns the resulting GameObject to m_ConfigObject.
// Assumed IL2CPP instance method: void(this, MethodInfo*).
// No return-value handling or object access is attempted.
#[skyline::hook(offset = 0x253A470)]
fn config_sequence_create_config_menu(this: *mut c_void, method_info: *const c_void) {
    let n = CREATE_CALLS.fetch_add(1, Ordering::Relaxed) + 1;
    if n <= 16 || n % 32 == 0 {
        skyline::println!(
            "[ELP V10.1] CreateConfigMenu ENTER #{} this={:p} method={:p}",
            n, this, method_info
        );
    }
    original!()(this, method_info);
    if n <= 16 || n % 32 == 0 {
        skyline::println!("[ELP V10.1] CreateConfigMenu EXIT #{}", n);
    }
}

pub fn install() {
    skyline::println!("[ELP V10.1] Installing 2 diagnostic hooks (2.0.0)");
    skyline::install_hooks!(
        config_menu_on_initialize,
        config_sequence_create_config_menu
    );
    skyline::println!("[ELP V10.1] Installation requested; watching CreateConfigMenu and OnInitialize");
}
