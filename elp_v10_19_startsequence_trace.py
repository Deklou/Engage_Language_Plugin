#!/usr/bin/env python3
"""ELP V10.19: extend Mess.Get capture from ConfigSequence.StartSequence to CreateConfigMenu.

Target: existing V10.18 src/config_hook.rs. Diagnostic: no UI modifications beyond V10.17.
"""
from pathlib import Path
import shutil

p = Path('src/config_hook.rs')
if not Path('Cargo.toml').is_file() or not p.is_file():
    raise SystemExit('Lancer depuis la racine du projet Rust.')
s = p.read_text(encoding='utf-8')
if '[ELP V10.18]' not in s or 'fn mess_get_capture(' not in s or 'fn config_sequence_create_config_menu(' not in s:
    raise SystemExit('La V10.18 est requise. Aucun fichier modifie.')
if '[ELP V10.19]' in s:
    raise SystemExit('V10.19 deja appliquee. Aucun fichier modifie.')

needle = '''    if let Ok(mut captured) = MESS_CAPTURE.lock() { *captured = Some(HashMap::new()); }
    MESS_CAPTURE_ACTIVE.store(true, Ordering::Relaxed);
    original!()(this, method_info);
    MESS_CAPTURE_ACTIVE.store(false, Ordering::Relaxed);'''
replacement = '''    // StartSequence may have started the capture before CreateConfigMenu.
    // Preserve those earlier return-pointer/key associations.
    let early_count = if let Ok(mut captured) = MESS_CAPTURE.lock() {
        if captured.is_none() { *captured = Some(HashMap::new()); }
        captured.as_ref().map(|m| m.len()).unwrap_or(0)
    } else { 0 };
    skyline::println!("[ELP V10.19] CREATE ENTER: early Mess.Get pointers={}", early_count);
    MESS_CAPTURE_ACTIVE.store(true, Ordering::Relaxed);
    original!()(this, method_info);
    MESS_CAPTURE_ACTIVE.store(false, Ordering::Relaxed);'''
if s.count(needle) != 1:
    raise SystemExit('Bloc de capture CreateConfigMenu non conforme a la V10.18.')
s = s.replace(needle, replacement, 1)

needle = '#[skyline::hook(offset = 0x25c9240)] // App.Mess.Get(Il2CppString), Engage 2.0.0'
insert = '''// Trace the earlier sequence phase, without changing the game's call path.
// Capture stays active until CreateConfigMenu finishes, including any
// scheduled intermediate UI setup. The map is capped at 8192 entries.
#[skyline::hook(offset = 0x253a290)] // ConfigSequence.StartSequence, Engage 2.0.0
fn config_sequence_start_sequence(this: *mut c_void, method_info: *const c_void) {
    if let Ok(mut captured) = MESS_CAPTURE.lock() { *captured = Some(HashMap::new()); }
    MESS_CAPTURE_ACTIVE.store(true, Ordering::Relaxed);
    skyline::println!("[ELP V10.19] START StartSequence capture");
    original!()(this, method_info);
    let count = MESS_CAPTURE.lock().ok()
        .and_then(|guard| guard.as_ref().map(|m| m.len())).unwrap_or(0);
    skyline::println!("[ELP V10.19] END StartSequence function; capture continues until CreateConfigMenu (pointers={})", count);
}

'''
if s.count(needle) != 1:
    raise SystemExit('Point d insertion avant Mess.Get introuvable.')
s = s.replace(needle, insert + needle, 1)

needle = '''    skyline::install_hooks!(mess_get_capture, config_sequence_create_config_menu);'''
replacement = '''    skyline::install_hooks!(mess_get_capture, config_sequence_start_sequence, config_sequence_create_config_menu);'''
if s.count(needle) != 1:
    raise SystemExit('Installation des hooks V10.18 inattendue.')
s = s.replace(needle, replacement, 1)

needle = '''skyline::println!("[ELP V10.18] Installing scoped Settings-header MSBT trace (keeps V10.17 refresh)");'''
replacement = '''skyline::println!("[ELP V10.19] Installing StartSequence -> CreateConfigMenu MSBT trace (keeps V10.17 refresh)");'''
if s.count(needle) != 1:
    raise SystemExit('Message d installation V10.18 introuvable.')
s = s.replace(needle, replacement, 1)

# Early keys may be present before CreateConfigMenu. Log them with their
# resolved English string, but only for the requested header candidates.
needle = '''                        if resolved.chars().count() <= 180 {
                            skyline::println!(
                                "[ELP V10.18] MSBT key={:?} value={:?}",
                                key, resolved
                            );'''
replacement = '''                        if resolved.chars().count() <= 180 {
                            if resolved.contains("Settings")
                                || resolved.contains("settings")
                                || resolved.contains("Reset")
                                || resolved.contains("Adjust")
                                || key.contains("HEADER")
                                || key.contains("RESET") {
                                skyline::println!("[ELP V10.19] HEADER CANDIDATE key={:?} value={:?}", key, resolved);
                            }
                            skyline::println!(
                                "[ELP V10.18] MSBT key={:?} value={:?}",
                                key, resolved
                            );'''
if s.count(needle) != 1:
    raise SystemExit('Capture V10.18 inattendue.')
s = s.replace(needle, replacement, 1)

backup = Path('src/config_hook.rs.bak_v10_18')
if backup.exists():
    raise SystemExit(f'Sauvegarde deja presente : {backup}. Aucun fichier modifie.')
shutil.copy2(p, backup)
p.write_text(s, encoding='utf-8')
print(f'V10.19 appliquee ; sauvegarde : {backup}')
print('Ouvrir Settings en anglais, puis changer la langue vers le francais sans le fermer.')
print('Rechercher [ELP V10.19] START, CREATE ENTER et HEADER CANDIDATE dans le log.')
