use std::collections::HashMap;
use unity::prelude::*;
use std::cell::RefCell;
use engage::menu::{config::{ConfigBasicMenuItem, ConfigBasicMenuItemSwitchMethods}, BasicMenuResult};
use engage::dialog::yesno::{BasicDialogItemYes, YesNoDialog, TwoChoiceDialogMethods};
use crate::interface::{reload_messages, get_current_voice, set_voice, reflect_voice_setting};
use crate::language::CURRENT_LANG;

static mut PREVIEW_VOICE: i32 = 1;
static mut CURRENT_VOICE: i32 = 1;

//get the voice translations for each voice ID
fn get_voice_translations() -> HashMap<i32, Vec<&'static str>> {
    let mut translations = HashMap::new();
    translations.insert(0, vec!["日本語", "Japanese", "", "Japonés", "Japanese", "Japonais", "Japonés", "Japanisch", "Giapponese", "日本語", "日语", "일본어"]);
    translations.insert(1, vec!["英語", "English", "", "Inglés", "English", "Anglais", "Inglés", "Englisch", "Inglese", "韩语", "韩语", "한국어"]);
    translations
}

//get the name of a voice based on the selected voice ID and current language ID
fn get_voice_name(voice_id: i32, current_lang_id: i32) -> &'static str {
    let translations = get_voice_translations();
    translations.get(&voice_id).and_then(|names| names.get(current_lang_id as usize)).unwrap_or(&"Unknown")
}

//get the localized string for different keys
fn get_localized_string(key: &str, lang_id: i32) -> &'static str {
    match (key, lang_id) {
        ("change_voice_confirm", 0) => "音声を変えますか",
        ("change_voice_confirm", 1) => "Change Voice",
        ("change_voice_confirm", 3) => "Cambiar Voz",
        ("change_voice_confirm", 4) => "Change Voice",
        ("change_voice_confirm", 5) => "Changer de voix",
        ("change_voice_confirm", 6) => "Cambiar voz",
        ("change_voice_confirm", 7) => "Ändere deine Stimme",
        ("change_voice_confirm", 8) => "Cambia la tua voce",
        ("change_voice_confirm", 9) => "改變你的聲音",
        ("change_voice_confirm", 10) => "改变你的声音",
        ("change_voice_confirm", 11) => "목소리를 바꿔라",
        ("current_voice", 0) => "現在の声",
        ("current_voice", 1) => "Current Voice",
        ("current_voice", 3) => "Voz Actual",
        ("current_voice", 4) => "Current Voice",
        ("current_voice", 5) => "Voix actuelle",
        ("current_voice", 6) => "Voz Actual",
        ("current_voice", 7) => "Aktuelle Stimme",
        ("current_voice", 8) => "Voce Attuale",
        ("current_voice", 9) => "目前語音",
        ("current_voice", 10) => "当前语音",
        ("current_voice", 11) => "현재 음성",
        ("confirm_yes", 0) => "はい",
        ("confirm_yes", 1) => "Yes",
        ("confirm_yes", 3) => "Sí",
        ("confirm_yes", 4) => "Yes",
        ("confirm_yes", 5) => "Oui",
        ("confirm_yes", 6) => "Sí",
        ("confirm_yes", 7) => "Ja",
        ("confirm_yes", 8) => "SÌ",
        ("confirm_yes", 9) => "是的",
        ("confirm_yes", 10) => "是的",
        ("confirm_yes", 11) => "예",
        ("confirm_no", 0) => "いいえ",
        ("confirm_no", 1) => "No",
        ("confirm_no", 3) => "No",
        ("confirm_no", 4) => "No",
        ("confirm_no", 5) => "Non",
        ("confirm_no", 6) => "No",
        ("confirm_no", 7) => "Nein",
        ("confirm_no", 8) => "No",
        ("confirm_no", 9) => "不",
        ("confirm_no", 10) => "不",
        ("confirm_no", 11) => "아니요",
        _ => "Unspecified",
    }
}

pub struct VoiceSettings;

//implementing the trait for menu switch methods
impl ConfigBasicMenuItemSwitchMethods for VoiceSettings {
    //initialize the content of the menu
    fn init_content(this: &mut ConfigBasicMenuItem) {
        unsafe {
            CURRENT_VOICE = get_current_voice();
            PREVIEW_VOICE = CURRENT_VOICE;
            update_preview_text(this);
        }
    }

    //changing the voice preview
    extern "C" fn custom_call(this: &mut ConfigBasicMenuItem, _method_info: Option<&'static MethodInfo>) -> BasicMenuResult {
        unsafe {
            let new_voice = ConfigBasicMenuItem::change_key_value_i(PREVIEW_VOICE, 0, 1, 1);
            if PREVIEW_VOICE != new_voice {
                PREVIEW_VOICE = new_voice;
                update_preview_text(this);
                BasicMenuResult::se_cursor()
            } else {
                BasicMenuResult::new()
            }
        }
    }

    //set help text
    extern "C" fn set_help_text(this: &mut ConfigBasicMenuItem, _method_info: Option<&'static MethodInfo>) {
        unsafe {
            let help_text = get_localized_string("current_voice", CURRENT_LANG);
            let voice_name = get_voice_name(CURRENT_VOICE, CURRENT_LANG);
            this.help_text = format!("{}: {}", help_text, voice_name).into();
        }
    }

    //set command text
    extern "C" fn set_command_text(this: &mut ConfigBasicMenuItem, _method_info: Option<&'static MethodInfo>) {
        unsafe {
            let command_text = get_voice_name(CURRENT_VOICE, CURRENT_LANG);
            this.command_text = command_text.to_string().into();
        }
    }
}

thread_local! {
    static CURRENT_MENU_ITEM: RefCell<Option<*mut ConfigBasicMenuItem>> = RefCell::new(None);
}

struct VoiceConfirmation;

//confirm the voice change when the A button is pressed
extern "C" fn a_button_confirm(this: &mut ConfigBasicMenuItem, _method_info: Option<&'static MethodInfo>) -> BasicMenuResult {
    unsafe {
        CURRENT_MENU_ITEM.with(|item| {
            *item.borrow_mut() = Some(this as *mut _);
        });
        if PREVIEW_VOICE != CURRENT_VOICE {
            BasicMenuResult::se_cursor();
            YesNoDialog::bind::<VoiceConfirmation>(
            this.menu,  
            get_localized_string("change_voice_confirm", CURRENT_LANG),
            get_localized_string("confirm_yes", CURRENT_LANG),
            get_localized_string("confirm_no", CURRENT_LANG)
            );
        }
        BasicMenuResult::se_cursor()
    }
}

impl TwoChoiceDialogMethods for VoiceConfirmation {
    extern "C" fn on_first_choice(_this: &mut BasicDialogItemYes, _method_info: OptionalMethod) -> BasicMenuResult {
        unsafe {
            set_voice(PREVIEW_VOICE);
            CURRENT_VOICE = PREVIEW_VOICE;
            reflect_voice_setting();
            reload_messages();
            CURRENT_MENU_ITEM.with(|item| {
                if let Some(menu_item) = *item.borrow() {
                    update_texts(&mut *menu_item);
                }
            });
        }
        BasicMenuResult::new().with_close_this(true)
    }

}

//update the preview text based on the selected voice
fn update_preview_text(this: &mut ConfigBasicMenuItem) {
    unsafe {
        let voice_name = get_voice_name(PREVIEW_VOICE, CURRENT_LANG);
        this.command_text = voice_name.to_string().into();
        this.update_text();
    }
}

//update this plugin texts to reflect the current voice setting
fn update_texts(this: &mut ConfigBasicMenuItem) {
    unsafe {
        this.title_text = get_localized_string("change_voice_confirm", CURRENT_LANG).into();
        VoiceSettings::set_help_text(this, None);
        VoiceSettings::set_command_text(this, None);
        this.update_text();
    }
}

//callback function for voice selection
#[no_mangle]
extern "C" fn voice_callback() -> &'static mut ConfigBasicMenuItem {
    let switch = ConfigBasicMenuItem::new_switch::<VoiceSettings>("Change Voice");
    if let Some(method) = switch.get_class_mut().get_virtual_method_mut("ACall") {
        method.method_ptr = a_button_confirm as _;
    }
    
    update_texts(switch);
    switch
}

//function to install the voice setting in the game
pub fn voice_install() {
    cobapi::install_game_setting(voice_callback);
}
