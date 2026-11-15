//! V10.17: exact Mess.Get return-pointer MSBT key capture on top of V10.16.
use core::ffi::c_void;
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::Mutex;
use std::collections::HashMap;
use unity::prelude::*;
use unity::system::List;
use engage::menu::{ConfigMenu, config::ConfigBasicMenuItem};

// Capture strictement limitee au CreateConfigMenu en cours :
// Mess.Get(label) => adresse Il2CppString retournee, sans modifier le texte.
static MESS_CAPTURE_ACTIVE: AtomicBool = AtomicBool::new(false);
static MESS_CAPTURE: Mutex<Option<HashMap<usize, Option<String>>>> = Mutex::new(None);
static NATIVE_TITLE_KEYS: Mutex<Vec<Option<String>>> = Mutex::new(Vec::new());
// V10.24: ConfigSequence of the current Settings screen; replaced at creation.
static SETTINGS_TITLEBAR_SEQUENCE: AtomicUsize = AtomicUsize::new(0);

// Trace the earlier sequence phase, without changing the game's call path.
// Capture stays active until CreateConfigMenu finishes, including any
// scheduled intermediate UI setup. The map is capped at 8192 entries.
// V10.20: read-only inspection scoped to ConfigSequence.m_ConfigObject.
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

// V10.21: traverse upwards from ConfigRoot, then inspect siblings in read-only mode.
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

// V10.22: isolated read-only walk through GameUI/TitleBarRootCanvas.
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
            if !matches!((&*p).get_string().as_deref(), Ok("TitleBarRootCanvas")) { continue; }
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

// V10.23: GameObject.GetComponentByName(Il2CppString) -- verified in
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

// V10.24: TMPro.TMP_Text.SetText(string, bool), native (non-virtual) IL2CPP
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
    let title = unsafe { crate::interface::get_message(title_key) };
    let help = unsafe { crate::interface::get_message(help_key) };
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
        // V10.25: native titlebar X keyhelp (Reset Settings).
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
        skyline::println!("[ELP V10.24] DONE written={}/4", written);
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
                    Entry::Vacant(v) => {
                        // During menu creation only, log the MSBT key and original
                        // visible string together. This is the first place where
                        // the result pointer is known to be valid. No UI writes.
                        let resolved = (&*result).get_string().unwrap_or_default();
                        if resolved.chars().count() <= 180 {
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
                            );
                        } else {
                            skyline::println!("[ELP V10.18] MSBT key={:?} value=<long>", key);
                        }
                        v.insert(Some(key));
                    }
                    Entry::Occupied(mut o) => {
                        if o.get().as_ref() != Some(&key) { o.insert(None); }
                    }
                }
            }
        }
    }
    result
}

static NATIVE_ITEMS: [AtomicUsize; 25] = [
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0),
    AtomicUsize::new(0)
];
#[skyline::from_offset(0x24690f0)]
fn native_cmd_0(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x24692b0)]
fn native_help_0(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x20addd0)]
fn native_cmd_1(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x20adf90)]
fn native_help_1(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x22e96a0)]
fn native_cmd_2(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x22e9810)]
fn native_help_2(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x250c220)]
fn native_cmd_3(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x250c390)]
fn native_help_3(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x193a6b0)]
fn native_cmd_4(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x193a7e0)]
fn native_help_4(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x202e110)]
fn native_cmd_5(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x202e240)]
fn native_help_5(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x202dcd0)]
fn native_cmd_6(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x202de00)]
fn native_help_6(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x1dcadf0)]
fn native_help_7(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x1de4b90)]
fn native_cmd_8(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x1de4df0)]
fn native_help_8(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x25e3db0)]
fn native_cmd_9(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x25e3f80)]
fn native_help_9(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x1d2e1f0)]
fn native_cmd_10(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x1d2e320)]
fn native_help_10(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x1e71ea0)]
fn native_cmd_11(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x1e71fb0)]
fn native_help_11(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x1e72380)]
fn native_cmd_12(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x1e72490)]
fn native_help_12(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x2d7ea40)]
fn native_cmd_13(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x2d7eb50)]
fn native_help_13(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x2d7ef20)]
fn native_cmd_14(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x2d7f030)]
fn native_help_14(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x2d7f560)]
fn native_help_15(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x27aa3e0)]
fn native_cmd_16(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x27aa4f0)]
fn native_help_16(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x21c3b70)]
fn native_help_17(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x21c3f20)]
fn native_help_18(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x21c42f0)]
fn native_help_19(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x20c4a80)]
fn native_cmd_20(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x20c4bb0)]
fn native_help_20(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x21218e0)]
fn native_cmd_21(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x2121970)]
fn native_help_21(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x21218e0)]
fn native_cmd_22(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x2121970)]
fn native_help_22(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x1a01fd0)]
fn native_cmd_23(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x1a02100)]
fn native_help_23(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x27a9d30)]
fn native_cmd_24(this: *mut c_void, method_info: *const c_void);
#[skyline::from_offset(0x27a9e40)]
fn native_help_24(this: *mut c_void, method_info: *const c_void);

const TARGET_CLASSES: [&str; 25] = [
    "BattleAnimeTypeMenuItem",
    "SupportAnimeTypeMenuItem",
    "EngageAnimeTypeMenuItem",
    "GameSpeedMenuItem",
    "AISkipMenuItem",
    "MapUnitOperationMenuItem",
    "MapUnitGaugeMenuItem",
    "MapGridAlphaMenuItem",
    "MapInfoUnitPageMenuItem",
    "MiniMapMenuItem",
    "AllInfoSwitchTypeMenuItem",
    "BattleCameraReverseHorizontalMenuItem",
    "BattleCameraReverseVerticalMenuItem",
    "HubCameraReverseHorizontalMenuItem",
    "HubCameraReverseVerticalMenuItem",
    "HubCameraRotateSpeedMenuItem",
    "IsMinimapRotateMenuItem",
    "VolumeBgmMenuItem",
    "VolumeSeMenuItem",
    "VolumeVoiceMenuItem",
    "TalkPlayModeMenuItem",
    "BGMChangeMenuItem",
    "BGMChangeMenuItem",
    "TutorialShowMenuItem",
    "IsEnableNetworkMenuItem",
];

#[skyline::hook(offset = 0x253a470)]
fn config_sequence_create_config_menu(this: *mut c_void, method_info: *const c_void) {
    for item in NATIVE_ITEMS.iter() { item.store(0, Ordering::Relaxed); }
    if let Ok(mut keys) = NATIVE_TITLE_KEYS.lock() { keys.clear(); keys.resize(25, None); }
    // StartSequence may have started the capture before CreateConfigMenu.
    // Preserve those earlier return-pointer/key associations.
    let early_count = if let Ok(mut captured) = MESS_CAPTURE.lock() {
        if captured.is_none() { *captured = Some(HashMap::new()); }
        captured.as_ref().map(|m| m.len()).unwrap_or(0)
    } else { 0 };
    skyline::println!("[ELP V10.19] CREATE ENTER: early Mess.Get pointers={}", early_count);
    MESS_CAPTURE_ACTIVE.store(true, Ordering::Relaxed);
    original!()(this, method_info);
    MESS_CAPTURE_ACTIVE.store(false, Ordering::Relaxed);
    // V10.23: replaced broad probe: elp_trace_settings_ui_tree(this);
    // V10.23: replaced broad probe: elp_trace_settings_parent_siblings(this);
    // V10.23: replaced broad probe: elp_trace_titlebar_from_config(this);
    SETTINGS_TITLEBAR_SEQUENCE.store(this as usize, Ordering::Relaxed);
    elp_trace_titlebar_tmp_components(this);
    if this.is_null() { return; }
    unsafe {
        let child = ((this as *const u8).add(0x38) as *const *const c_void).read();
        if child.is_null() { return; }
        let menu = &*(child as *const ConfigMenu<()>);
        let class_name = format!("{:?}", menu.get_class().get_name());
        if class_name != r#""ConfigMenu""# && class_name != r#"Some("ConfigMenu")"# { return; }
        let full = ((child as *const u8).add(0x80) as *const *const List<ConfigBasicMenuItem>).read();
        if full.is_null() { return; }
        let list = &*full;
        let size = list.len();
        if size < 25 || size > list.capacity() || size > 128 { return; }
        for (i, entry) in list.iter().take(25).enumerate() {
            let class = format!("{:?}", entry.get_class().get_name());
            let expected = TARGET_CLASSES[i];
            if class != format!("{:?}", expected) && class != format!("Some({:?})", expected) {
                skyline::println!("[ELP V10.15] capture skip #{} class={}", i, class);
                continue;
            }
            let ptr = *entry as *const ConfigBasicMenuItem;
            NATIVE_ITEMS[i].store(ptr as usize, Ordering::Relaxed);
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
            skyline::println!("[ELP V10.18] END Settings-build MSBT trace (unique pointers={})", n);
            *captured = None;
        }
        skyline::println!("[ELP V10.27b] captured 25 native rows, list size={}", size);
    }
}

pub fn refresh_native_settings() {
    for (i, target) in NATIVE_ITEMS.iter().enumerate() {
        let ptr = target.load(Ordering::Relaxed) as *mut ConfigBasicMenuItem;
        if ptr.is_null() { continue; }
        unsafe {
            let item = &mut *ptr;
            let class = format!("{:?}", item.get_class().get_name());
            let expected = TARGET_CLASSES[i];
            if class != format!("{:?}", expected) && class != format!("Some({:?})", expected) {
                target.store(0, Ordering::Relaxed);
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
            // If an exact MSBT key was captured for this title, recompute it.
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
                0 => { native_cmd_0(ptr.cast(), core::ptr::null()); native_help_0(ptr.cast(), core::ptr::null()); },
                1 => { native_cmd_1(ptr.cast(), core::ptr::null()); native_help_1(ptr.cast(), core::ptr::null()); },
                2 => { native_cmd_2(ptr.cast(), core::ptr::null()); native_help_2(ptr.cast(), core::ptr::null()); },
                3 => { native_cmd_3(ptr.cast(), core::ptr::null()); native_help_3(ptr.cast(), core::ptr::null()); },
                4 => { native_cmd_4(ptr.cast(), core::ptr::null()); native_help_4(ptr.cast(), core::ptr::null()); },
                5 => { native_cmd_5(ptr.cast(), core::ptr::null()); native_help_5(ptr.cast(), core::ptr::null()); },
                6 => { native_cmd_6(ptr.cast(), core::ptr::null()); native_help_6(ptr.cast(), core::ptr::null()); },
                7 => { native_help_7(ptr.cast(), core::ptr::null()); },
                8 => { native_cmd_8(ptr.cast(), core::ptr::null()); native_help_8(ptr.cast(), core::ptr::null()); },
                9 => { native_cmd_9(ptr.cast(), core::ptr::null()); native_help_9(ptr.cast(), core::ptr::null()); },
                10 => { native_cmd_10(ptr.cast(), core::ptr::null()); native_help_10(ptr.cast(), core::ptr::null()); },
                11 => { native_cmd_11(ptr.cast(), core::ptr::null()); native_help_11(ptr.cast(), core::ptr::null()); },
                12 => { native_cmd_12(ptr.cast(), core::ptr::null()); native_help_12(ptr.cast(), core::ptr::null()); },
                13 => { native_cmd_13(ptr.cast(), core::ptr::null()); native_help_13(ptr.cast(), core::ptr::null()); },
                14 => { native_cmd_14(ptr.cast(), core::ptr::null()); native_help_14(ptr.cast(), core::ptr::null()); },
                15 => { native_help_15(ptr.cast(), core::ptr::null()); },
                16 => { native_cmd_16(ptr.cast(), core::ptr::null()); native_help_16(ptr.cast(), core::ptr::null()); },
                17 => { native_help_17(ptr.cast(), core::ptr::null()); },
                18 => { native_help_18(ptr.cast(), core::ptr::null()); },
                19 => { native_help_19(ptr.cast(), core::ptr::null()); },
                20 => { native_cmd_20(ptr.cast(), core::ptr::null()); native_help_20(ptr.cast(), core::ptr::null()); },
                21 => { native_cmd_21(ptr.cast(), core::ptr::null()); native_help_21(ptr.cast(), core::ptr::null()); },
                22 => { native_cmd_22(ptr.cast(), core::ptr::null()); native_help_22(ptr.cast(), core::ptr::null()); },
                23 => { native_cmd_23(ptr.cast(), core::ptr::null()); native_help_23(ptr.cast(), core::ptr::null()); },
                24 => { native_cmd_24(ptr.cast(), core::ptr::null()); native_help_24(ptr.cast(), core::ptr::null()); },
                _ => continue,
            }
            item.update_text();
            skyline::println!("[ELP V10.15] updated #{} class={}", i, expected);
        }
    }

    // V10.27d: isolate diagnostic-induced crash. Count extra rows only.
    // V10.27c crashed even with plugin callbacks disabled, right after
    // GetClass/println on the final third-party entry. No reflection or
    // per-entry formatting in this diagnostic pass.
    let seq = SETTINGS_TITLEBAR_SEQUENCE.load(Ordering::Relaxed) as *const c_void;
    if seq.is_null() { return; }
    unsafe {
        let child = ((seq as *const u8).add(0x38) as *const *const c_void).read();
        if child.is_null() { return; }
        let menu = &*(child as *const ConfigMenu<()>);
        let menu_class = format!("{:?}", menu.get_class().get_name());
        if menu_class != r#""ConfigMenu""# && menu_class != r#"Some("ConfigMenu")"# {
            return;
        }
        let full = ((child as *const u8).add(0x80) as *const *const List<ConfigBasicMenuItem>).read();
        if full.is_null() { return; }
        let list = &*full;
        let size = list.len();
        if size < 25 || size > list.capacity() || size > 128 { return; }
        let mut extras = 0usize;
        for entry in list.iter().take(128) {
            let ptr = *entry as *const ConfigBasicMenuItem as usize;
            if ptr == 0 { continue; }
            if NATIVE_ITEMS.iter().any(|native| native.load(Ordering::Relaxed) == ptr) {
                continue;
            }
            extras += 1;
        }
        skyline::println!("[ELP V10.27d] COUNT DONE total={} extra={}", size, extras);
    }
}

pub fn install() {
    skyline::println!("[ELP V10.24] Installing live Settings titlebar translation (keeps V10.17 refresh)");
    skyline::install_hooks!(mess_get_capture, config_sequence_start_sequence, config_sequence_create_config_menu);
}
