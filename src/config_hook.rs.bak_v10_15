//! V10.15: refresh native setting values and help for rows 0..24.
use core::ffi::c_void;
use std::sync::atomic::{AtomicUsize, Ordering};
use unity::prelude::*;
use unity::system::List;
use engage::menu::{ConfigMenu, config::ConfigBasicMenuItem};

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
}

pub fn install() {
    skyline::println!("[ELP V10.15] Installing native refresh (rows 0..24)");
    skyline::install_hooks!(config_sequence_create_config_menu);
}
