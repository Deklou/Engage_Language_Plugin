#!/usr/bin/env python3
"""V10.17: capture Mess.Get key -> exact string object while ConfigMenu is built.

Applies on top of V10.16 (and preserves all V10.15 native command/help refreshes).
Only refreshes native titles when an unambiguous exact pointer/key match exists.
"""
from pathlib import Path
import shutil

p = Path('src/config_hook.rs')
if not Path('Cargo.toml').is_file() or not p.is_file():
    raise SystemExit('Lancer depuis la racine du projet Rust (Cargo.toml + src/config_hook.rs).')
s = p.read_text(encoding='utf-8')
if '//! V10.16:' not in s or '[ELP V10.16]' not in s:
    raise SystemExit('Version attendue : V10.16. Aucun fichier modifie.')
if '[ELP V10.17]' in s:
    raise SystemExit('V10.17 deja appliquee. Aucun fichier modifie.')

# The actual address is from Fire Emblem Engage 2.0.0 generated IL2CPP bindings.
old_imports = 'use std::sync::atomic::{AtomicUsize, Ordering};'
new_imports = '''use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::Mutex;
use std::collections::HashMap;'''
if s.count(old_imports) != 1:
    raise SystemExit('Imports inattendus. Aucun fichier modifie.')
s = s.replace(old_imports, new_imports, 1)

needle_static = 'static NATIVE_ITEMS: [AtomicUsize; 25] = ['
if s.count(needle_static) != 1:
    raise SystemExit('Table NATIVE_ITEMS introuvable. Aucun fichier modifie.')
prefix = '''// Capture strictement limitee au CreateConfigMenu en cours :
// Mess.Get(label) => adresse Il2CppString retournee, sans modifier le texte.
static MESS_CAPTURE_ACTIVE: AtomicBool = AtomicBool::new(false);
static MESS_CAPTURE: Mutex<Option<HashMap<usize, Option<String>>>> = Mutex::new(None);
static NATIVE_TITLE_KEYS: Mutex<Vec<Option<String>>> = Mutex::new(Vec::new());

#[skyline::hook(offset = 0x25c9240)] // App.Mess.Get(Il2CppString), Engage 2.0.0
fn mess_get_capture(label: *const Il2CppString, method_info: *const c_void) -> *const Il2CppString {
    let result = original!()(label, method_info);
    if !MESS_CAPTURE_ACTIVE.load(Ordering::Relaxed) || label.is_null() || result.is_null() {
        return result;
    }
    unsafe {
        let key = (&*label).get_string().unwrap_or_default();
        if !key.starts_with("MID_") || key.len() > 180 { return result; }
        if let Ok(mut guard) = MESS_CAPTURE.lock() {
            if let Some(ref mut map) = *guard {
                if map.len() >= 8192 { return result; }
                use std::collections::hash_map::Entry;
                match map.entry(result as usize) {
                    Entry::Vacant(v) => { v.insert(Some(key)); }
                    Entry::Occupied(mut o) => {
                        if o.get().as_ref() != Some(&key) { o.insert(None); }
                    }
                }
            }
        }
    }
    result
}

'''
s = s.replace(needle_static, prefix + needle_static, 1)

needle_create = '''    for item in NATIVE_ITEMS.iter() { item.store(0, Ordering::Relaxed); }
    original!()(this, method_info);
    if this.is_null() { return; }'''
replacement_create = '''    for item in NATIVE_ITEMS.iter() { item.store(0, Ordering::Relaxed); }
    if let Ok(mut keys) = NATIVE_TITLE_KEYS.lock() { keys.clear(); keys.resize(25, None); }
    if let Ok(mut captured) = MESS_CAPTURE.lock() { *captured = Some(HashMap::new()); }
    MESS_CAPTURE_ACTIVE.store(true, Ordering::Relaxed);
    original!()(this, method_info);
    MESS_CAPTURE_ACTIVE.store(false, Ordering::Relaxed);
    if this.is_null() { return; }'''
if s.count(needle_create) != 1:
    raise SystemExit('Hook CreateConfigMenu inattendu. Aucun fichier modifie.')
s = s.replace(needle_create, replacement_create, 1)

needle_capture = '''            NATIVE_ITEMS[i].store(ptr as usize, Ordering::Relaxed);
        }
        skyline::println!("[ELP V10.15] captured up to 25 native rows, list size={}", size);'''
replacement_capture = '''            NATIVE_ITEMS[i].store(ptr as usize, Ordering::Relaxed);
            // Exact pointer matching, no guessing by translated text.
            // Title field is m_TitleText (offset 0x68), exposed by the wrapper.
            let title_ptr = (&*ptr).title_text as *const Il2CppString as usize;
            let key = if let Ok(map_guard) = MESS_CAPTURE.lock() {
                map_guard.as_ref().and_then(|map| map.get(&title_ptr).cloned()).flatten()
            } else { None };
            let before = (&*ptr).title_text.get_string().unwrap_or_default();
            if let Ok(mut keys) = NATIVE_TITLE_KEYS.lock() {
                if keys.len() == 25 { keys[i] = key.clone(); }
            }
            skyline::println!("[ELP V10.17] TITLE #{} class={} key={:?} current={:?}", i, expected, key, before);
        }
        if let Ok(mut captured) = MESS_CAPTURE.lock() {
            let n = captured.as_ref().map(|m| m.len()).unwrap_or(0);
            skyline::println!("[ELP V10.17] captured Mess.Get unique return pointers={}", n);
            *captured = None;
        }
        skyline::println!("[ELP V10.15] captured up to 25 native rows, list size={}", size);'''
if s.count(needle_capture) != 1:
    raise SystemExit('Boucle de capture inattendue. Aucun fichier modifie.')
s = s.replace(needle_capture, replacement_capture, 1)

# Keep V10.16's m_name test, which proved always null, untouched.
needle_refresh = '''            match i {
                0 => { native_cmd_0'''
replacement_refresh = '''            // If an exact MSBT key was captured for this title, recompute it.
            // Distinctly skip unknown mappings rather than fabricate one.
            let title_key = if let Ok(keys) = NATIVE_TITLE_KEYS.lock() {
                keys.get(i).cloned().flatten()
            } else { None };
            if let Some(key) = title_key {
                let label: &'static Il2CppString = key.as_str().into();
                let translated = crate::interface::get_message(label);
                let value = translated.get_string().unwrap_or_default();
                if !value.is_empty() && value != key {
                    item.title_text = translated;
                    skyline::println!("[ELP V10.17] REFRESH TITLE #{} key={} new={:?}", i, key, value);
                }
            }
            match i {
                0 => { native_cmd_0'''
if s.count(needle_refresh) != 1:
    raise SystemExit('Point de rafraichissement inattendu. Aucun fichier modifie.')
s = s.replace(needle_refresh, replacement_refresh, 1)

needle_install = '''    skyline::install_hooks!(config_sequence_create_config_menu);'''
if s.count(needle_install) != 1:
    raise SystemExit('Installation des hooks inattendue. Aucun fichier modifie.')
s = s.replace(needle_install, '    skyline::install_hooks!(mess_get_capture, config_sequence_create_config_menu);', 1)
s = s.replace('//! V10.16: generic MSBT-key title test on top of V10.15 native refresh.',
              '//! V10.17: exact Mess.Get return-pointer MSBT key capture on top of V10.16.', 1)
s = s.replace('skyline::println!("[ELP V10.15] Installing native refresh (rows 0..24)");',
              'skyline::println!("[ELP V10.17] Installing Mess.Get title-key capture + native refresh");', 1)

backup = Path('src/config_hook.rs.bak_v10_16')
if backup.exists():
    raise SystemExit(f'La sauvegarde existe deja : {backup}. Aucun fichier modifie.')
shutil.copy2(p, backup)
p.write_text(s, encoding='utf-8')
print('V10.17 appliquee ; sauvegarde :', backup)
print('Les lignes [ELP V10.17] indiqueront le nombre de titres associes sans ambiguite.')
