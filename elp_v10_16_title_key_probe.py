#!/usr/bin/env python3
"""V10.16: test whether inherited BasicMenuItem.m_name stores a MSBT key.
Keeps V10.15 values/help; only updates native titles when m_name is MID_*.
"""
from pathlib import Path
import shutil

p = Path('src/config_hook.rs')
lang = Path('src/language.rs')
if not Path('Cargo.toml').is_file() or not p.is_file() or not lang.is_file():
    raise SystemExit('Run from the Rust project root')
s = p.read_text(encoding='utf8')
if '//! V10.15:' not in s or 'pub fn refresh_native_settings()' not in s:
    raise SystemExit('Expected pushed V10.15 config_hook.rs; no changes made')
if '[ELP V10.16]' in s:
    raise SystemExit('V10.16 already applied')
needle = '''                target.store(0, Ordering::Relaxed);
                continue;
            }
            match i {'''
if s.count(needle) != 1:
    raise SystemExit('Expected refresh insertion point not found uniquely; no changes')
insertion = '''                target.store(0, Ordering::Relaxed);
                continue;
            }
            // BasicMenuItem.m_name, offset 0x20 on Engage 2.0.0.
            // Different from ConfigBasicMenuItem.m_TitleText (0x68).
            // This is a guarded experiment: only MID_* keys can rewrite a title.
            let name_ptr = ((ptr as *const u8).add(0x20)
                as *const *const Il2CppString).read();
            if !name_ptr.is_null() {
                let name = (&*name_ptr).get_string().unwrap_or_default();
                skyline::println!("[ELP V10.16] item #{} m_name={:?}", i, name);
                if name.starts_with("MID_") {
                    let key: &'static Il2CppString = name.as_str().into();
                    let translated = crate::interface::get_message(key);
                    let title = translated.get_string().unwrap_or_default();
                    if !title.is_empty() && title != name {
                        item.title_text = translated;
                        skyline::println!("[ELP V10.16] title #{} => {:?}", i, title);
                    }
                }
            } else {
                skyline::println!("[ELP V10.16] item #{} m_name=NULL", i);
            }
            match i {'''
new = s.replace(needle, insertion).replace('//! V10.15: refresh native setting values and help for rows 0..24.', '//! V10.16: generic MSBT-key title test on top of V10.15 native refresh.')
backup = Path('src/config_hook.rs.bak_v10_15')
if backup.exists():
    raise SystemExit(f'{backup} already exists; no changes made')
shutil.copy2(p, backup)
p.write_text(new, encoding='utf8')
print('V10.16 applied. Backup:', backup)
print('m_name will be logged. Titles only change if m_name starts with MID_.')
