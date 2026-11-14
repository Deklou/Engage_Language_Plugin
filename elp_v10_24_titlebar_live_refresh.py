#!/usr/bin/env python3
"""ELP V10.24: refresh Settings Title/Help TextMeshPro after changing language.
Applies to V10.23 source. Engage v2.0.0. Backs up both edited files.
"""
from pathlib import Path
import shutil

root = Path('Cargo.toml')
config = Path('src/config_hook.rs')
language = Path('src/language.rs')
if not all(p.is_file() for p in (root, config, language)):
    raise SystemExit('Lancer depuis la racine du projet (Cargo.toml, src/config_hook.rs et src/language.rs).')
s = config.read_text(encoding='utf-8')
l = language.read_text(encoding='utf-8')
if '[ELP V10.24]' in s or 'refresh_settings_titlebar();' in l:
    raise SystemExit('V10.24 deja appliquee : aucun changement.')
required_s = [
    'fn elp_trace_titlebar_tmp_components(seq: *const c_void) {',
    '    elp_trace_titlebar_tmp_components(this);',
    'unsafe fn elp_tmp_child(parent: *const c_void, target: &str) -> *const c_void {',
    'fn elp_tmp_get_component_by_name(go: *const c_void, type_name: *const Il2CppString,',
    'pub fn refresh_native_settings() {',
    '[ELP V10.23] Installing focused TMP-component trace (keeps V10.17 refresh)',
]
for a in required_s:
    if s.count(a) != 1:
        raise SystemExit(f'Version config_hook.rs inattendue : {a!r} (occurrences={s.count(a)}). Aucun changement.')
anchor_language = '            crate::config_hook::refresh_native_settings();'
if l.count(anchor_language) != 1:
    raise SystemExit('Ancre du changement de langue absente ou dupliquee dans language.rs. Aucun changement.')
for path in (Path('src/config_hook.rs.bak_v10_23'), Path('src/language.rs.bak_v10_23')):
    if path.exists():
        raise SystemExit(f'Sauvegarde deja existante : {path}. Aucun changement.')

# A live ConfigSequence pointer is only used after the user confirms a language
# change while Settings is open. It is replaced on the next CreateConfigMenu.
# Guard the refresh with the native Settings item capture, which is only nonzero
# after the ConfigMenu exists. No permanent TMP component pointers are cached.
s = s.replace('static NATIVE_TITLE_KEYS: Mutex<Vec<Option<String>>> = Mutex::new(Vec::new());',
'''static NATIVE_TITLE_KEYS: Mutex<Vec<Option<String>>> = Mutex::new(Vec::new());
// V10.24: ConfigSequence of the current Settings screen; replaced at creation.
static SETTINGS_TITLEBAR_SEQUENCE: AtomicUsize = AtomicUsize::new(0);''', 1)

anchor = 'fn elp_trace_titlebar_tmp_components(seq: *const c_void) {'
helper = r'''// V10.24: TMPro.TMP_Text.SetText(string, bool), native (non-virtual) IL2CPP
// overload, offset confirmed in DivineDragonFanClub/engage-il2cpp for 2.0.0.
// Calling the public SetText overload instead of writing TMP_Text.m_text.
#[skyline::from_offset(0x2837690)]
fn elp_tmp_set_text_2(component: *const c_void, text: *const Il2CppString,
    sync_text_input_box: bool, mi: *const c_void);

pub fn refresh_settings_titlebar() {
    let seq = SETTINGS_TITLEBAR_SEQUENCE.load(Ordering::Relaxed) as *const c_void;
    if seq.is_null() {
        skyline::println!("[ELP V10.24] SKIP no Settings sequence");
        return;
    }
    // Resolve translations *after* Mess.Reload. These are the known MSBT keys.
    let title_key: &'static Il2CppString = "MID_MENU_CONFIG".into();
    let help_key: &'static Il2CppString = "MID_MENU_CONFIG_HELP".into();
    let title = crate::interface::get_message(title_key);
    let help = crate::interface::get_message(help_key);
    let title_value = title.get_string().unwrap_or_default();
    let help_value = help.get_string().unwrap_or_default();
    if title_value.is_empty() || help_value.is_empty()
        || title_value == "MID_MENU_CONFIG" || help_value == "MID_MENU_CONFIG_HELP" {
        skyline::println!("[ELP V10.24] SKIP unresolved MSBT title={:?} help={:?}",
            title_value, help_value);
        return;
    }
    unsafe {
        let config_go = ((seq as *const u8).add(0x70) as *const *const c_void).read();
        if config_go.is_null() { skyline::println!("[ELP V10.24] SKIP null ConfigRoot"); return; }
        let root = elp_ui_get_transform(config_go, core::ptr::null());
        if root.is_null() { return; }
        let game_ui = elp_ui_get_parent(root, core::ptr::null());
        let titlebar = elp_tmp_child(game_ui, "TitleBarRootCanvas");
        let content_root = elp_tmp_child(titlebar, "ContentTitleRoot(Clone)");
        let all = elp_tmp_child(content_root, "ContentsTitleAll");
        let content = elp_tmp_child(all, "ContentTitle");
        if content.is_null() {
            skyline::println!("[ELP V10.24] SKIP TitleBar path missing");
            return;
        }
        let type_name: &'static Il2CppString = "TextMeshProUGUI".into();
        let mut written = 0;
        // Update both animation slots to prevent an old English title returning.
        for slot in 0..2 {
            let part = elp_tmp_child(content,
                if slot == 0 { "ContentTitle0" } else { "ContentTitle1" });
            let title_help = elp_tmp_child(part, "TitleHelp");
            for (role, value) in [("Title", title), ("Help", help)].iter() {
                let node = elp_tmp_child(title_help, role);
                if node.is_null() { continue; }
                let go = elp_ui_get_game_object(node, core::ptr::null());
                if go.is_null() { continue; }
                let component = elp_tmp_get_component_by_name(go,
                    type_name as *const Il2CppString, core::ptr::null());
                if component.is_null() {
                    skyline::println!("[ELP V10.24] MISSING slot={} role={}", slot, role);
                    continue;
                }
                elp_tmp_set_text_2(component, *value as *const Il2CppString,
                    false, core::ptr::null());
                written += 1;
                skyline::println!("[ELP V10.24] SET slot={} role={} component={:p} value={:?}",
                    slot, role, component,
                    if *role == "Title" { &title_value } else { &help_value });
            }
        }
        skyline::println!("[ELP V10.24] DONE written={}/4", written);
    }
}

'''
s = s.replace(anchor, helper + anchor, 1)
# Store the sequence only when we know CreateConfigMenu completed and the probe
# was reached. This is the exact point already verified by V10.23.
s = s.replace('    elp_trace_titlebar_tmp_components(this);',
'''    SETTINGS_TITLEBAR_SEQUENCE.store(this as usize, Ordering::Relaxed);
    elp_trace_titlebar_tmp_components(this);''', 1)
s = s.replace('[ELP V10.23] Installing focused TMP-component trace (keeps V10.17 refresh)',
              '[ELP V10.24] Installing live Settings titlebar translation (keeps V10.17 refresh)', 1)
l = l.replace(anchor_language, anchor_language + '\n            crate::config_hook::refresh_settings_titlebar();', 1)
shutil.copy2(config, 'src/config_hook.rs.bak_v10_23')
shutil.copy2(language, 'src/language.rs.bak_v10_23')
config.write_text(s, encoding='utf-8')
language.write_text(l, encoding='utf-8')
print('V10.24 appliquee sur config_hook.rs et language.rs.')
print('Sauvegardes : src/config_hook.rs.bak_v10_23 et src/language.rs.bak_v10_23')
print('Apres build/deploiement: test anglais -> francais -> anglais sans quitter Settings.')
print('Logs attendus : [ELP V10.24] SET ... / DONE written=4/4')
