#!/usr/bin/env python3
"""ELP V10.25 — refresh native Reset Settings key-help text in both titlebar slots.

Apply from the Rust project's root after V10.24 (including the unsafe get_message
compile correction). Only edits src/config_hook.rs, with a backup.
"""
from pathlib import Path
import shutil

config = Path('src/config_hook.rs')
if not Path('Cargo.toml').is_file() or not config.is_file():
    raise SystemExit('Lancer depuis la racine du projet Rust (Cargo.toml).')
s = config.read_text(encoding='utf-8')
if '[ELP V10.25]' in s:
    raise SystemExit('V10.25 deja appliquee. Aucun changement.')

required = (
    'pub fn refresh_settings_titlebar() {',
    'let titlebar = elp_tmp_child(game_ui, "TitleBarRootCanvas");',
    'let content = elp_tmp_child(all, "ContentTitle");',
    'fn elp_tmp_set_text_2(',
    'fn elp_tmp_get_component_by_name(',
    'skyline::println!("[ELP V10.24] DONE written={}/4", written);',
)
for signature in required:
    n = s.count(signature)
    if n != 1:
        raise SystemExit(f'Source V10.24 inattendue, signature {signature!r} x{n}. Aucun changement.')

# Do not change the existing title/help code path. Insert immediately before its
# final status log, inside the same unsafe block where `content` is a Transform.
anchor = '        skyline::println!("[ELP V10.24] DONE written={}/4", written);'
addition = r'''        // V10.25: native titlebar X keyhelp (Reset Settings).
        // V10.22 confirmed the hierarchy for both animation slots:
        // ContentTitle{0,1}/KeyHelpTitleBar/X/Text.
        // The MSBT is re-resolved after Mess.Reload, just like Title/Help.
        let reset_key: &'static Il2CppString = "MID_KEYHELP_MENU_RESET".into();
        let reset = crate::interface::get_message(reset_key);
        let reset_value = reset.get_string().unwrap_or_default();
        if reset_value.is_empty() || reset_value == "MID_KEYHELP_MENU_RESET" {
            skyline::println!("[ELP V10.25] SKIP unresolved reset key value={:?}", reset_value);
        } else {
            let mut reset_written = 0usize;
            for slot in 0..2 {
                let part = elp_tmp_child(content,
                    if slot == 0 { "ContentTitle0" } else { "ContentTitle1" });
                let keyhelp = elp_tmp_child(part, "KeyHelpTitleBar");
                let x = elp_tmp_child(keyhelp, "X");
                let text_node = elp_tmp_child(x, "Text");
                if text_node.is_null() {
                    skyline::println!("[ELP V10.25] MISSING slot={} X/Text node", slot);
                    continue;
                }
                let go = elp_ui_get_game_object(text_node, core::ptr::null());
                if go.is_null() { continue; }
                let type_name: &'static Il2CppString = "TextMeshProUGUI".into();
                let component = elp_tmp_get_component_by_name(go,
                    type_name as *const Il2CppString, core::ptr::null());
                if component.is_null() {
                    skyline::println!("[ELP V10.25] MISSING slot={} X/Text TMP", slot);
                    continue;
                }
                elp_tmp_set_text_2(component, reset as *const Il2CppString,
                    false, core::ptr::null());
                reset_written += 1;
                skyline::println!("[ELP V10.25] RESET slot={} component={:p} value={:?}",
                    slot, component, reset_value);
            }
            skyline::println!("[ELP V10.25] DONE reset_written={}/2", reset_written);
        }
'''
patched = s.replace(anchor, addition + anchor, 1)
backup = Path('src/config_hook.rs.bak_v10_24')
if backup.exists():
    raise SystemExit(f'Sauvegarde {backup} existe deja. Aucun changement.')
shutil.copy2(config, backup)
config.write_text(patched, encoding='utf-8')
print('V10.25 appliquee : traduction native X/Reset Settings dans les deux slots.')
print(f'Sauvegarde : {backup}')
print('Compiler : cargo skyline build --release')
print('Logs attendus : [ELP V10.25] RESET slot=0/1 et DONE reset_written=2/2')
