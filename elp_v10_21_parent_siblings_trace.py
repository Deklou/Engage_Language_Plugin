#!/usr/bin/env python3
"""ELP V10.21: read-only parent/sibling traversal of ConfigRoot (Engage 2.0.0).
Requires the exact V10.20 config_hook.rs. No new Skyline hooks.
"""
from pathlib import Path
import shutil

p = Path('src/config_hook.rs')
if not Path('Cargo.toml').is_file() or not p.is_file():
    raise SystemExit('Lancer depuis la racine du projet Rust (Cargo.toml et src/config_hook.rs requis).')
s = p.read_text(encoding='utf-8')
if ('[ELP V10.20]' not in s or
        s.count('    elp_trace_settings_ui_tree(this);') != 1 or
        s.count('fn elp_trace_ui_transform(') != 1):
    raise SystemExit('Code V10.20 non reconnu ; aucun fichier modifie.')
if '[ELP V10.21]' in s:
    raise SystemExit('La V10.21 est deja appliquee ; aucun fichier modifie.')

anchor = 'fn elp_trace_settings_ui_tree(seq: *const c_void) {'
assert s.count(anchor) == 1
helper = r'''// V10.21: traverse upwards from ConfigRoot, then inspect siblings in read-only mode.
// UnityEngine.Transform.get_parent (Engage 2.0.0).
#[skyline::from_offset(0x37909f0)]
fn elp_ui_get_parent(transform: *const c_void, mi: *const c_void) -> *const c_void;

fn elp_trace_settings_parent_siblings(seq: *const c_void) {
    if seq.is_null() { return; }
    unsafe {
        let go = ((seq as *const u8).add(0x70) as *const *const c_void).read();
        if go.is_null() { return; }
        let mut node = elp_ui_get_transform(go, core::ptr::null());
        if node.is_null() { return; }
        skyline::println!("[ELP V10.21] PARENT/SIBLING TRACE BEGIN config_root={:p}", node);
        // Walk at most four levels; do not revisit previously-seen nodes.
        let mut visited: [*const c_void; 5] = [core::ptr::null(); 5];
        visited[0] = node;
        let mut nodes = 0usize;
        for level in 1..=4usize {
            let parent = elp_ui_get_parent(node, core::ptr::null());
            if parent.is_null() {
                skyline::println!("[ELP V10.21] reached null parent at level={}", level);
                break;
            }
            if visited[..level].contains(&parent) {
                skyline::println!("[ELP V10.21] repeated parent at level={}", level);
                break;
            }
            visited[level] = parent;
            let parent_go = elp_ui_get_game_object(parent, core::ptr::null());
            if parent_go.is_null() { break; }
            let name_ptr = elp_ui_get_name(parent_go, core::ptr::null());
            let name = if name_ptr.is_null() { String::from("<null>") }
                else { (&*name_ptr).get_string().unwrap_or_default() };
            let children = elp_ui_get_child_count(parent, core::ptr::null());
            skyline::println!("[ELP V10.21] PARENT level={} ptr={:p} name={:?} children={}",
                level, parent, name, children);
            if children < 0 || children > 2000 { break; }
            // The first 24 siblings per parent, including the current branch.
            // Only two levels beneath siblings, to keep this probe bounded.
            for i in 0..children.min(24) {
                if nodes >= 360 { break; }
                let sibling = elp_ui_get_child(parent, i, core::ptr::null());
                if sibling.is_null() { continue; }
                let sibling_go = elp_ui_get_game_object(sibling, core::ptr::null());
                if sibling_go.is_null() { continue; }
                let sibling_name_ptr = elp_ui_get_name(sibling_go, core::ptr::null());
                let sibling_name = if sibling_name_ptr.is_null() { String::from("<null>") }
                    else { (&*sibling_name_ptr).get_string().unwrap_or_default() };
                skyline::println!("[ELP V10.21] SIBLING parent_level={} idx={} current={} name={:?}",
                    level, i, sibling == node, sibling_name);
                if sibling != node {
                    // The V10.20 helper stops at depth>7; starting at 6 gives
                    // sibling + direct children without exploring all scene objects.
                    elp_trace_ui_transform(sibling, 6, &mut nodes);
                }
            }
            node = parent;
            if nodes >= 360 {
                skyline::println!("[ELP V10.21] node cap reached");
                break;
            }
        }
        skyline::println!("[ELP V10.21] PARENT/SIBLING TRACE END nodes={}", nodes);
    }
}

'''
s = s.replace(anchor, helper + anchor, 1)
s = s.replace('    elp_trace_settings_ui_tree(this);',
              '    elp_trace_settings_ui_tree(this);\n    elp_trace_settings_parent_siblings(this);', 1)
old = '[ELP V10.20] Installing Settings UI hierarchy trace (keeps V10.17 refresh)'
new = '[ELP V10.21] Installing parent/sibling Settings UI trace (keeps V10.17 refresh)'
if s.count(old) != 1:
    raise SystemExit('Signature install V10.20 non reconnue ; aucun fichier modifie.')
s = s.replace(old, new, 1)
backup = Path('src/config_hook.rs.bak_v10_20')
if backup.exists():
    raise SystemExit(f'Sauvegarde deja presente : {backup}. Aucun fichier modifie.')
shutil.copy2(p, backup)
p.write_text(s, encoding='utf-8')
print('V10.21 appliquee ; sauvegarde :', backup)
print('Compiler puis rechercher [ELP V10.21] PARENT / SIBLING / TRACE END.')
