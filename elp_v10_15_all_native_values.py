#!/usr/bin/env python3
"""V10.15: update commands/help on all original native setting items (0..24).
Apply only to a V10.14 project; does not translate native titles or UI header.
"""
from pathlib import Path
import shutil

hook = Path('src/config_hook.rs')
lang = Path('src/language.rs')
if not Path('Cargo.toml').is_file() or not hook.is_file() or not lang.is_file():
    raise SystemExit('Execute from the Rust project root')
h = hook.read_text(encoding='utf-8')
l = lang.read_text(encoding='utf-8')
if '[ELP V10.14]' not in h or 'refresh_native_settings();' not in l:
    raise SystemExit('Expected V10.14 source; no files changed.')
backup_h = Path('src/config_hook.rs.bak_v10_14')
if backup_h.exists():
    raise SystemExit('V10.14 backup exists; no files changed.')
# Verified offsets in DivineDragonFanClub/engage-il2cpp for Engage 2.0.0.
# (class name, direct SetCommandText offset or None, direct SetHelpText offset or None)
rows = [
    ('BattleAnimeTypeMenuItem', 0x24690f0, 0x24692b0),
    ('SupportAnimeTypeMenuItem', 0x20addd0, 0x20adf90),
    ('EngageAnimeTypeMenuItem', 0x22e96a0, 0x22e9810),
    ('GameSpeedMenuItem', 0x250c220, 0x250c390),
    ('AISkipMenuItem', 0x193a6b0, 0x193a7e0),
    ('MapUnitOperationMenuItem', 0x202e110, 0x202e240),
    ('MapUnitGaugeMenuItem', 0x202dcd0, 0x202de00),
    ('MapGridAlphaMenuItem', None, 0x1dcadf0),
    ('MapInfoUnitPageMenuItem', 0x1de4b90, 0x1de4df0),
    ('MiniMapMenuItem', 0x25e3db0, 0x25e3f80),
    ('AllInfoSwitchTypeMenuItem', 0x1d2e1f0, 0x1d2e320),
    ('BattleCameraReverseHorizontalMenuItem', 0x1e71ea0, 0x1e71fb0),
    ('BattleCameraReverseVerticalMenuItem', 0x1e72380, 0x1e72490),
    ('HubCameraReverseHorizontalMenuItem', 0x2d7ea40, 0x2d7eb50),
    ('HubCameraReverseVerticalMenuItem', 0x2d7ef20, 0x2d7f030),
    ('HubCameraRotateSpeedMenuItem', None, 0x2d7f560),
    ('IsMinimapRotateMenuItem', 0x27aa3e0, 0x27aa4f0),
    ('VolumeBgmMenuItem', None, 0x21c3b70),
    ('VolumeSeMenuItem', None, 0x21c3f20),
    ('VolumeVoiceMenuItem', None, 0x21c42f0),
    ('TalkPlayModeMenuItem', 0x20c4a80, 0x20c4bb0),
    ('BGMChangeMenuItem', 0x21218e0, 0x2121970),
    ('BGMChangeMenuItem', 0x21218e0, 0x2121970),
    ('TutorialShowMenuItem', 0x1a01fd0, 0x1a02100),
    ('IsEnableNetworkMenuItem', 0x27a9d30, 0x27a9e40),
]
parts = ['''//! V10.15: refresh native setting values and help for rows 0..24.
use core::ffi::c_void;
use std::sync::atomic::{AtomicUsize, Ordering};
use unity::prelude::*;
use unity::system::List;
use engage::menu::{ConfigMenu, config::ConfigBasicMenuItem};

static NATIVE_ITEMS: [AtomicUsize; 25] = [AtomicUsize::new(0); 25];
''']
# AtomicUsize does not implement Copy; construct explicit elements instead.
parts[0] = parts[0].replace('[AtomicUsize::new(0); 25]', '[\n' + ',\n'.join('    AtomicUsize::new(0)' for _ in rows) + '\n]')
for i, (_, cmd, help_offset) in enumerate(rows):
    if cmd is not None:
        parts.append(f'#[skyline::from_offset(0x{cmd:x})]\nfn native_cmd_{i}(this: *mut c_void, method_info: *const c_void);\n')
    if help_offset is not None:
        parts.append(f'#[skyline::from_offset(0x{help_offset:x})]\nfn native_help_{i}(this: *mut c_void, method_info: *const c_void);\n')
parts.append('''
const TARGET_CLASSES: [&str; 25] = [
''')
for name, _, _ in rows:
    parts.append(f'    "{name}",\n')
parts.append('''];

#[skyline::hook(offset = 0x253a470)]
fn config_sequence_create_config_menu(this: *mut c_void, method_info: *const c_void) {
    for item in NATIVE_ITEMS.iter() { item.store(0, Ordering::Relaxed); }
    original!()(this, method_info);
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
        }
        skyline::println!("[ELP V10.15] captured up to 25 native rows, list size={}", size);
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
            match i {
''')
for i, (_, cmd, help_offset) in enumerate(rows):
    calls = []
    if cmd is not None: calls.append(f'native_cmd_{i}(ptr.cast(), core::ptr::null());')
    if help_offset is not None: calls.append(f'native_help_{i}(ptr.cast(), core::ptr::null());')
    parts.append(f'                {i} => {{ ' + ' '.join(calls) + ' },\n')
parts.append('''                _ => continue,
            }
            item.update_text();
            skyline::println!("[ELP V10.15] updated #{} class={}", i, expected);
        }
    }
}

pub fn install() {
    skyline::println!("[ELP V10.15] Installing native refresh (rows 0..24)");
    skyline::install_hooks!(config_sequence_create_config_menu);
}
''')
new_h = ''.join(parts)
assert 'refresh_native_settings();' in l
shutil.copy2(hook, backup_h)
hook.write_text(new_h, encoding='utf-8')
print('V10.15 applied. Previous source backed up as src/config_hook.rs.bak_v10_14')
