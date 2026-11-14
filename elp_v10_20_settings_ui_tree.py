#!/usr/bin/env python3
"""ELP V10.20: enumerate the Settings GameObject hierarchy to locate header UI.

Input: exact V10.19 config_hook.rs. Diagnostic-only and preserves native refresh.
Known native IL2CPP offsets are for Fire Emblem Engage 2.0.0.
"""
from pathlib import Path
import shutil

p = Path('src/config_hook.rs')
if not Path('Cargo.toml').is_file() or not p.is_file():
    raise SystemExit('Lancer depuis la racine du projet Rust (Cargo.toml requis).')
s = p.read_text(encoding='utf-8')
if '[ELP V10.19]' not in s or 'fn config_sequence_create_config_menu(' not in s:
    raise SystemExit('La V10.19 est requise ; aucun fichier modifie.')
if '[ELP V10.20]' in s:
    raise SystemExit('La V10.20 est deja appliquee ; aucun fichier modifie.')

anchor = '#[skyline::hook(offset = 0x253a290)] // ConfigSequence.StartSequence, Engage 2.0.0'
if s.count(anchor) != 1:
    raise SystemExit('Hook StartSequence V10.19 non reconnu ; aucun fichier modifie.')

helper = r'''// V10.20: read-only inspection scoped to ConfigSequence.m_ConfigObject.
// All offsets from engage-il2cpp, Engage 2.0.0. No Unity object mutation.
#[skyline::from_offset(0x2c4e880)] // UnityEngine.GameObject.get_transform
fn elp_ui_get_transform(go: *const c_void, mi: *const c_void) -> *const c_void;
#[skyline::from_offset(0x37925a0)] // UnityEngine.Transform.get_childCount
fn elp_ui_get_child_count(transform: *const c_void, mi: *const c_void) -> i32;
#[skyline::from_offset(0x3792d40)] // UnityEngine.Transform.GetChild
fn elp_ui_get_child(transform: *const c_void, index: i32, mi: *const c_void) -> *const c_void;
#[skyline::from_offset(0x2c46490)] // UnityEngine.Component.get_gameObject
fn elp_ui_get_game_object(component: *const c_void, mi: *const c_void) -> *const c_void;
#[skyline::from_offset(0x32e8e90)] // UnityEngine.Object.get_name
fn elp_ui_get_name(obj: *const c_void, mi: *const c_void) -> *const Il2CppString;

unsafe fn elp_trace_ui_transform(node: *const c_void, depth: usize, nodes: &mut usize) {
    if node.is_null() || depth > 7 || *nodes >= 240 { return; }
    *nodes += 1;
    let go = elp_ui_get_game_object(node, core::ptr::null());
    if go.is_null() { return; }
    let name_ptr = elp_ui_get_name(go, core::ptr::null());
    let name = if name_ptr.is_null() { String::from("<null>") }
        else { (&*name_ptr).get_string().unwrap_or_default() };
    let raw_count = elp_ui_get_child_count(node, core::ptr::null());
    if raw_count < 0 || raw_count > 2000 {
        skyline::println!("[ELP V10.20] invalid child count depth={} name={:?} count={}", depth, name, raw_count);
        return;
    }
    skyline::println!("[ELP V10.20] UI depth={} node={:p} go={:p} children={} name={:?}", depth, node, go, raw_count, name);
    // Cap per parent and overall count; diagnostic intentionally incomplete on huge trees.
    for i in 0..raw_count.min(80) {
        if *nodes >= 240 { break; }
        let child = elp_ui_get_child(node, i, core::ptr::null());
        elp_trace_ui_transform(child, depth + 1, nodes);
    }
}

fn elp_trace_settings_ui_tree(seq: *const c_void) {
    if seq.is_null() { return; }
    unsafe {
        // ConfigSequence.m_ConfigObject is a GameObject at IL2CPP offset 0x70.
        let go = ((seq as *const u8).add(0x70) as *const *const c_void).read();
        if go.is_null() {
            skyline::println!("[ELP V10.20] ConfigSequence.m_ConfigObject=NULL");
            return;
        }
        let root = elp_ui_get_transform(go, core::ptr::null());
        if root.is_null() {
            skyline::println!("[ELP V10.20] ConfigSequence GameObject has no Transform");
            return;
        }
        skyline::println!("[ELP V10.20] SETTINGS UI TREE BEGIN game_object={:p}", go);
        let mut nodes = 0usize;
        elp_trace_ui_transform(root, 0, &mut nodes);
        skyline::println!("[ELP V10.20] SETTINGS UI TREE END nodes_logged={}", nodes);
    }
}

'''
s = s.replace(anchor, helper + anchor, 1)

# Insert read-only tree inspection immediately after original creation, while
# the sequence and GameObject have a known valid lifetime.
old = '''    MESS_CAPTURE_ACTIVE.store(false, Ordering::Relaxed);
    if this.is_null() { return; }'''
new = '''    MESS_CAPTURE_ACTIVE.store(false, Ordering::Relaxed);
    elp_trace_settings_ui_tree(this);
    if this.is_null() { return; }'''
if s.count(old) != 1:
    raise SystemExit('Fin du hook CreateConfigMenu V10.19 non reconnue ; aucun fichier modifie.')
s = s.replace(old, new, 1)

old_install = '[ELP V10.19] Installing StartSequence -> CreateConfigMenu MSBT trace (keeps V10.17 refresh)'
new_install = '[ELP V10.20] Installing Settings UI hierarchy trace (keeps V10.17 refresh)'
if s.count(old_install) != 1:
    raise SystemExit('Signature de version V10.19 absente ; aucun fichier modifie.')
s = s.replace(old_install, new_install, 1)

backup = Path('src/config_hook.rs.bak_v10_19')
if backup.exists():
    raise SystemExit(f'Sauvegarde deja presente : {backup}. Aucun fichier modifie.')
shutil.copy2(p, backup)
p.write_text(s, encoding='utf-8')
print('V10.20 appliquee ; sauvegarde :', backup)
print('Diagnostic en lecture seule ; conserver le meme .nro et les memes ressources hors plugin.')
print('Dans le log, chercher [ELP V10.20] SETTINGS UI TREE BEGIN / UI depth= / END.')
