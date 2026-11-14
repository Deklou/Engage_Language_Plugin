#!/usr/bin/env python3
"""ELP V10.22: targeted read-only hierarchy probe for TitleBarRootCanvas.
Applies to exact V10.21 source. Preserves all existing language refresh paths.
"""
from pathlib import Path
import shutil

p = Path('src/config_hook.rs')
if not Path('Cargo.toml').is_file() or not p.is_file():
    raise SystemExit('Lancer depuis la racine du projet Rust (Cargo.toml / src/config_hook.rs).')
s = p.read_text(encoding='utf-8')
checks = [
    ('fn elp_trace_settings_parent_siblings(seq: *const c_void) {', 1),
    ('    elp_trace_settings_parent_siblings(this);', 1),
    ('fn elp_trace_ui_transform(', 1),
    ('[ELP V10.21] Installing parent/sibling Settings UI trace (keeps V10.17 refresh)', 1),
]
for marker, count in checks:
    if s.count(marker) != count:
        raise SystemExit(f'Version source inattendue (signature absente ou dupliquee): {marker!r}. Aucun changement.')
if '[ELP V10.22]' in s:
    raise SystemExit('V10.22 deja appliquee. Aucun changement.')

anchor = 'fn elp_trace_settings_ui_tree(seq: *const c_void) {'
assert s.count(anchor) == 1
helper = r'''// V10.22: isolated read-only walk through GameUI/TitleBarRootCanvas.
// No component setters, no global Unity hooks, no persistent UI pointers.
unsafe fn elp_trace_titlebar_node(node: *const c_void, depth: usize, nodes: &mut usize) {
    if node.is_null() || depth > 8 || *nodes >= 220 { return; }
    *nodes += 1;
    let go = elp_ui_get_game_object(node, core::ptr::null());
    if go.is_null() { return; }
    let name_ptr = elp_ui_get_name(go, core::ptr::null());
    let name = if name_ptr.is_null() { String::from("<null>") }
        else { (&*name_ptr).get_string().unwrap_or_default() };
    let children = elp_ui_get_child_count(node, core::ptr::null());
    skyline::println!("[ELP V10.22] TITLEBAR depth={} transform={:p} go={:p} name={:?} children={}",
        depth, node, go, name, children);
    if children < 0 || children > 500 { return; }
    for i in 0..children.min(80) {
        if *nodes >= 220 { break; }
        let child = elp_ui_get_child(node, i, core::ptr::null());
        elp_trace_titlebar_node(child, depth + 1, nodes);
    }
}

fn elp_trace_titlebar_from_config(seq: *const c_void) {
    if seq.is_null() { return; }
    unsafe {
        let go = ((seq as *const u8).add(0x70) as *const *const c_void).read();
        if go.is_null() { return; }
        let root = elp_ui_get_transform(go, core::ptr::null());
        if root.is_null() { return; }
        // ConfigRoot(Clone) -> GameUI: locate the sibling by exact Unity name.
        let game_ui = elp_ui_get_parent(root, core::ptr::null());
        if game_ui.is_null() {
            skyline::println!("[ELP V10.22] no GameUI parent");
            return;
        }
        let count = elp_ui_get_child_count(game_ui, core::ptr::null());
        if count < 0 || count > 200 { return; }
        let mut found = false;
        for i in 0..count {
            let sibling = elp_ui_get_child(game_ui, i, core::ptr::null());
            if sibling.is_null() { continue; }
            let sibling_go = elp_ui_get_game_object(sibling, core::ptr::null());
            if sibling_go.is_null() { continue; }
            let p = elp_ui_get_name(sibling_go, core::ptr::null());
            if p.is_null() { continue; }
            if (&*p).get_string().as_deref() != Some("TitleBarRootCanvas") { continue; }
            found = true;
            skyline::println!("[ELP V10.22] TITLEBAR BEGIN sibling_index={} root={:p}", i, sibling);
            let mut nodes = 0usize;
            elp_trace_titlebar_node(sibling, 0, &mut nodes);
            skyline::println!("[ELP V10.22] TITLEBAR END nodes={} limit_reached={}", nodes, nodes >= 220);
            break;
        }
        if !found { skyline::println!("[ELP V10.22] TITLEBAR NOT FOUND among {} GameUI children", count); }
    }
}

'''
s = s.replace(anchor, helper + anchor, 1)
s = s.replace('    elp_trace_settings_parent_siblings(this);',
              '    elp_trace_settings_parent_siblings(this);\n    elp_trace_titlebar_from_config(this);', 1)
s = s.replace('[ELP V10.21] Installing parent/sibling Settings UI trace (keeps V10.17 refresh)',
              '[ELP V10.22] Installing targeted TitleBar hierarchy trace (keeps V10.17 refresh)', 1)
backup = Path('src/config_hook.rs.bak_v10_21')
if backup.exists():
    raise SystemExit(f'La sauvegarde existe deja ({backup}). Aucun changement.')
shutil.copy2(p, backup)
p.write_text(s, encoding='utf-8')
print('V10.22 appliquee. Sauvegarde:', backup)
print('Log: [ELP V10.22] TITLEBAR BEGIN / TITLEBAR depth= / TITLEBAR END')
