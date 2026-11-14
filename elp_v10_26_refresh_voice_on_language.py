#!/usr/bin/env python3
"""V10.26 - Refresh the plugin's Voice setting after changing UI language.

Apply at the root of Deklou/Engage_Language_Plugin after V10.25.
Only src/language.rs and src/voice.rs are modified. All changes are
validated before any file is written and original backups are created.
"""
from pathlib import Path
import sys

root = Path.cwd()
lang_path = root / 'src/language.rs'
voice_path = root / 'src/voice.rs'
if not lang_path.is_file() or not voice_path.is_file():
    sys.exit('Lancer ce script a la racine du projet (src/language.rs et src/voice.rs attendus).')
lang = lang_path.read_text(encoding='utf-8')
voice = voice_path.read_text(encoding='utf-8')
marker = '[ELP V10.26]'
if marker in lang or marker in voice:
    sys.exit('V10.26 deja presente. Aucun changement.')

# We cannot safely keep a blind raw pointer to a Unity/IL2CPP object across menus.
# A pointer registered by voice_callback() is only dereferenced if it also appears
# in the current language-setting menu's *live* full_menu_item_list.
old_import = 'use std::cell::RefCell;'
new_import = old_import + '\nuse std::sync::atomic::{AtomicUsize, Ordering};'
old_static = 'static mut CURRENT_VOICE: i32 = 1;'
new_static = old_static + '''

// V10.26: the last allocated plugin voice row; NEVER dereference this pointer
// unless it is also found in the currently active language settings menu.
static VOICE_ITEM_PTR: AtomicUsize = AtomicUsize::new(0);'''
old_callback = '    update_texts(switch);\n    switch\n}'
new_callback = '''    update_texts(switch);
    VOICE_ITEM_PTR.store(switch as *mut ConfigBasicMenuItem as usize, Ordering::Relaxed);
    switch
}'''
voice_new = voice
for old,new,tag in [
    (old_import,new_import,'voice import'),
    (old_static,new_static,'voice static'),
    (old_callback,new_callback,'voice callback'),
]:
    if voice_new.count(old) != 1:
        sys.exit(f'Signature inattendue ({tag}): {voice_new.count(old)} occurrence(s). Aucun changement.')
    voice_new = voice_new.replace(old,new,1)

# refresh called after reload_messages(), on the same IL2CPP thread, before
# closing the confirmation dialog. The slice is bounded by len and capacity.
helper = '''
// V10.26: refresh the plugin's existing Change Voice row when the language
// changes. Only touch the voice item if it belongs to this same live menu.
pub fn refresh_voice_after_language_change(language_item: &mut ConfigBasicMenuItem) {
    let voice_ptr = VOICE_ITEM_PTR.load(Ordering::Relaxed) as *mut ConfigBasicMenuItem;
    if voice_ptr.is_null() {
        skyline::println!("[ELP V10.26] VOICE SKIP no registered voice item");
        return;
    }
    let list = &language_item.menu.full_menu_item_list;
    let len = list.len();
    if len < 2 || len > 16 || len > list.capacity() {
        skyline::println!("[ELP V10.26] VOICE SKIP unexpected menu len={}", len);
        return;
    }
    let found = list.iter().take(len).any(|entry| {
        (*entry as *const ConfigBasicMenuItem) == (voice_ptr as *const ConfigBasicMenuItem)
    });
    if !found {
        skyline::println!("[ELP V10.26] VOICE SKIP item not in active menu");
        return;
    }
    unsafe {
        let item = &mut *voice_ptr;
        update_texts(item);
        skyline::println!("[ELP V10.26] VOICE REFRESH title={:?} command={:?}",
            item.title_text.get_string().unwrap_or_default(),
            item.command_text.get_string().unwrap_or_default());
    }
}

'''
anchor = '//callback function for voice selection\n'
if voice_new.count(anchor) != 1:
    sys.exit('Signature inattendue (voice callback anchor). Aucun changement.')
voice_new = voice_new.replace(anchor,helper+anchor,1)

# Add only one call to voice refresh after the existing language setting
# has repainted its own row. No native UI code and no titlebar changes.
old_call = '''                    refresh_config_menu(&mut *menu_item);'''
new_call = old_call + '''
                    crate::voice::refresh_voice_after_language_change(&mut *menu_item);'''
if lang.count(old_call) != 1:
    sys.exit(f'Signature inattendue (language refresh call): {lang.count(old_call)} occurrence(s). Aucun changement.')
if 'crate::config_hook::refresh_settings_titlebar();' not in lang:
    sys.exit('V10.24/25 non detectee dans language.rs. Aucun changement.')
lang_new = lang.replace(old_call,new_call,1)

# Save only after all assertions succeed, avoiding partially applied versions.
for path in (lang_path,voice_path):
    backup = path.with_name(path.name+'.bak_v10_25')
    if backup.exists():
        sys.exit(f'Sauvegarde deja presente: {backup}. Aucun changement (renommer la sauvegarde avant de relancer).')
lang_backup = lang_path.with_name(lang_path.name+'.bak_v10_25')
voice_backup = voice_path.with_name(voice_path.name+'.bak_v10_25')
lang_backup.write_text(lang,encoding='utf-8')
voice_backup.write_text(voice,encoding='utf-8')
lang_path.write_text(lang_new,encoding='utf-8')
voice_path.write_text(voice_new,encoding='utf-8')
print('V10.26 appliquee : rafraichissement cible de Change Voice lors du changement de langue.')
print('Sauvegardes : src/language.rs.bak_v10_25 et src/voice.rs.bak_v10_25')
print('Compiler : cargo skyline build --release')
