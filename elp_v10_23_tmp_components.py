#!/usr/bin/env python3
"""V10.23: targeted, read-only TMP component identification for the Settings titlebar.
Apply to V10.22 with the matches! Rust compile fix. Engage 2.0.0 only.
"""
from pathlib import Path
import shutil

p = Path('src/config_hook.rs')
if not Path('Cargo.toml').is_file() or not p.is_file():
    raise SystemExit('Lancer depuis la racine Rust (Cargo.toml / src/config_hook.rs).')
s = p.read_text(encoding='utf-8')
if '[ELP V10.23]' in s:
    raise SystemExit('V10.23 deja appliquee ; aucun changement.')
required = [
    'fn elp_trace_titlebar_from_config(seq: *const c_void) {',
    '    elp_trace_titlebar_from_config(this);',
    'fn elp_trace_settings_parent_siblings(seq: *const c_void) {',
    '    elp_trace_settings_parent_siblings(this);',
    '    elp_trace_settings_ui_tree(this);',
    '[ELP V10.22] Installing targeted TitleBar hierarchy trace (keeps V10.17 refresh)',
]
for marker in required:
    if s.count(marker) != 1:
        raise SystemExit(f'Signature V10.22 absente ou dupliquee: {marker!r}. Aucun changement.')
if 'get_string().as_deref() != Some("TitleBarRootCanvas")' in s:
    raise SystemExit('Appliquer d abord la correction matches! de compilation V10.22. Aucun changement.')

anchor = 'fn elp_trace_settings_ui_tree(seq: *const c_void) {'
if s.count(anchor) != 1:
    raise SystemExit('Ancre de diagnostic absente. Aucun changement.')
helper = r'''// V10.23: GameObject.GetComponentByName(Il2CppString) -- verified in
// DivineDragonFanClub/engage-il2cpp, UnityEngine.GameObject, Engage v2.0.0.
// No text reads/writes yet: first prove the component type and object identity.
#[skyline::from_offset(0x2c4dcf0)]
fn elp_tmp_get_component_by_name(go: *const c_void, type_name: *const Il2CppString,
    mi: *const c_void) -> *const c_void;

unsafe fn elp_tmp_child(parent: *const c_void, target: &str) -> *const c_void {
    if parent.is_null() { return core::ptr::null(); }
    let n = elp_ui_get_child_count(parent, core::ptr::null());
    if !(0..=100).contains(&n) { return core::ptr::null(); }
    for i in 0..n {
        let ch = elp_ui_get_child(parent, i, core::ptr::null());
        if ch.is_null() { continue; }
        let go = elp_ui_get_game_object(ch, core::ptr::null());
        if go.is_null() { continue; }
        let name = elp_ui_get_name(go, core::ptr::null());
        if !name.is_null() && matches!((&*name).get_string().as_deref(), Ok(x) if x == target) {
            return ch;
        }
    }
    core::ptr::null()
}

unsafe fn elp_tmp_probe(go: *const c_void, slot: i32, role: &str) {
    if go.is_null() { return; }
    // GameObject.GetComponentByName is a verified method; the exact class name
    // accepted by Unity is deliberately probed rather than assumed.
    let class_names = ["TextMeshProUGUI", "TMPro.TextMeshProUGUI", "TMP_Text"];
    for class_name in class_names.iter() {
        let il_name: &'static Il2CppString = (*class_name).into();
        let component = elp_tmp_get_component_by_name(go, il_name as *const Il2CppString,
            core::ptr::null());
        skyline::println!("[ELP V10.23] COMPONENT slot={} role={} go={:p} lookup={} ptr={:p}",
            slot, role, go, class_name, component);
        if !component.is_null() { break; }
    }
}

fn elp_trace_titlebar_tmp_components(seq: *const c_void) {
    if seq.is_null() { return; }
    unsafe {
        let go = ((seq as *const u8).add(0x70) as *const *const c_void).read();
        if go.is_null() { return; }
        let config_root = elp_ui_get_transform(go, core::ptr::null());
        if config_root.is_null() { return; }
        let game_ui = elp_ui_get_parent(config_root, core::ptr::null());
        let titlebar = elp_tmp_child(game_ui, "TitleBarRootCanvas");
        let content_root = elp_tmp_child(titlebar, "ContentTitleRoot(Clone)");
        let all = elp_tmp_child(content_root, "ContentsTitleAll");
        let content = elp_tmp_child(all, "ContentTitle");
        skyline::println!("[ELP V10.23] TMP BEGIN titlebar={:p} content={:p}", titlebar, content);
        if content.is_null() { return; }
        for slot in 0..2 {
            let slot_name = if slot == 0 { "ContentTitle0" } else { "ContentTitle1" };
            let part = elp_tmp_child(content, slot_name);
            let title_help = elp_tmp_child(part, "TitleHelp");
            for role in ["Title", "Help"].iter() {
                let child = elp_tmp_child(title_help, role);
                let part_go = if child.is_null() { core::ptr::null() }
                    else { elp_ui_get_game_object(child, core::ptr::null()) };
                skyline::println!("[ELP V10.23] TARGET slot={} role={} node={:p} go={:p}",
                    slot, role, child, part_go);
                elp_tmp_probe(part_go, slot, role);
            }
        }
        skyline::println!("[ELP V10.23] TMP END");
    }
}

'''
s = s.replace(anchor, helper + anchor, 1)
# Disable only the expensive old diagnostic calls; keep their functions intact
# for rollback and retain refresh/update operations unmodified.
for old in [
    '    elp_trace_settings_ui_tree(this);',
    '    elp_trace_settings_parent_siblings(this);',
    '    elp_trace_titlebar_from_config(this);',
]:
    s = s.replace(old, '    // V10.23: replaced broad probe: ' + old.strip(), 1)
old_line = '    // V10.23: replaced broad probe: elp_trace_titlebar_from_config(this);'
s = s.replace(old_line, old_line + '\n    elp_trace_titlebar_tmp_components(this);', 1)
s = s.replace('[ELP V10.22] Installing targeted TitleBar hierarchy trace (keeps V10.17 refresh)',
              '[ELP V10.23] Installing focused TMP-component trace (keeps V10.17 refresh)', 1)
backup = Path('src/config_hook.rs.bak_v10_22')
if backup.exists():
    raise SystemExit(f'Sauvegarde deja existante: {backup}. Aucun changement.')
shutil.copy2(p, backup)
p.write_text(s, encoding='utf-8')
print('V10.23 appliquee. Sauvegarde :', backup)
print('Logs attendus : [ELP V10.23] TMP BEGIN / TARGET / COMPONENT / TMP END')
print('Diagnostic en lecture seule : aucun changement des textes Unity.')
