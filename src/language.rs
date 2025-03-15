use std::collections::HashMap;
use unity::prelude::*;
use std::cell::RefCell;
use engage::menu::{config::{ConfigBasicMenuItem, ConfigBasicMenuItemSwitchMethods}, BasicMenuResult};
use engage::dialog::yesno::{BasicDialogItemYes, YesNoDialog, TwoChoiceDialogMethods};
use crate::interface::{get_current_language, set_language, reflect_language_setting, reload_messages};

pub static mut PREVIEW_LANG: i32 = 1;
pub static mut CURRENT_LANG: i32 = 1;

//get the language translations for each language ID
fn get_language_translations() -> HashMap<i32, Vec<&'static str>> {
    let mut translations = HashMap::new();
    translations.insert(0, vec!["日本語", "Japanese","" , "Japonés", "Japanese", "Japonais", "Japonés", "Japanisch", "Giapponese", "日本語", "日语", "일본어"]);
    translations.insert(1, vec!["日本語で", "English (North America)","" , "Inglés (Nortoamérica)", "English (North America)","Anglais (Amérique du Nord)", "English (North America)", "Englisch (Nordamerika)", "Inglese (Nord America)", "英语", "英语", "영어"]);
    translations.insert(3, vec!["スペイン語", "Spanish (Latin America)","" , "Español (Latinoamérica)", "Spanish (Latin America)", "Espagnol (Amérique Latine)", "Español (Latinoamérica)", "Spanisch (Lateinamerika)", "Spagnolo (America Latina)", "西班牙语", "西班牙语", "스페인어"]);
    translations.insert(4, vec!["英語で", "English (Europe)","" , "Inglés (Europa)", "English (Europe)", "Anglais (Europe)", "Inglés (Europa)", "Englisch (Europa)", "Inglese (Europa)", "英文", "英文", "영어"]);
    translations.insert(5, vec!["フランス語", "French (Europe)","" , "Francés (Europa)", "French (Europe)", "Français (Europe)", "Francés (Europa)", "Französisch (Europa)", "Francese (Europa)", "法语", "法语", "프랑스어"]);
    translations.insert(6, vec!["スペイン語", "Spanish (Europe)","" , "Español (Europa)", "Spanish (Europe)", "Espagnol (Europe)", "Español (Europa)", "Spanisch (Europa)", "Spagnolo (Europa)", "西班牙语", "西班牙语", "스페인어"]);
    translations.insert(7, vec!["ドイツ語", "German","" , "Alemán", "German", "Allemand", "Alemán", "Deutsch", "Tedesco", "德语", "德语", "독일어"]);
    translations.insert(8, vec!["イタリア語", "Italian","" , "Italiano", "Italian", "Italien", "Italiano", "Italienisch", "Italiano", "意大利语", "意大利语", "이탈리아어"]);
    translations.insert(9, vec!["中国語 (繁体)", "Traditional Chinese","" , "Chino Tradicional", "Traditional Chinese", "Chinois traditionnel", "Chino Tradicional", "Chinesisch (Langzeichen)", "Cinese tradizionale", "传统中文", "传统中文", "중국어 (번체)"]);
    translations.insert(10, vec!["中国語 (簡体)", "Simplified Chinese","" , "Chino Simplificado", "Simplified Chinese", "Chinois simplifié", "Chino Simplificado", "Chinesisch (Kurzzeichen)", "Cinese semplificato", "简体中文", "简体中文", "중국어 (간체)"]);
    translations.insert(10, vec!["韓国語", "Korean","" , "Coreano", "Korean", "Coréen", "Coreano", "Koreanisch", "Coreano", "韩语", "韩语", "한국어"]);
    translations
}

//get the name of a language based on the selected language ID and current language ID
fn get_language_name(lang_id: i32, current_lang_id: i32) -> &'static str {
    let translations = get_language_translations();
    translations.get(&lang_id).and_then(|names| names.get(current_lang_id as usize)).unwrap_or(&"Unknown")
}

//get the localized string for different keys
fn get_localized_string(key: &str, lang_id: i32) -> &'static str {
    match (key, lang_id) {
        ("change_language_confirm", 0) => "言語を変えてください ？",
        ("change_language_confirm", 1) => "Change Language ?",
        ("change_language_confirm", 3) => "¿Chambiar Idioma?",
        ("change_language_confirm", 4) => "Change Language ?",
        ("change_language_confirm", 5) => "Changer de langue ?",
        ("change_language_confirm", 6) => "¿Chambiar Idioma?",
        ("change_language_confirm", 7) => "Sprache ändern?",
        ("change_language_confirm", 8) => "Vuoi cambiare la lingua ?",
        ("change_language_confirm", 9) => "改變語言 ？",
        ("change_language_confirm", 10) => "改变语言 ？",
        ("change_language_confirm", 11) => "언어를 바꾸시겠어요?",
        ("change_language", 0) => "言語を変更",
        ("change_language", 1) => "Change Language",
        ("change_language", 3) => "Cambiar Idioma",
        ("change_language", 4) => "Change Language",
        ("change_language", 5) => "Changer de langue",
        ("change_language", 6) => "Cambiar Idioma",
        ("change_language", 7) => "Sprache ändern",
        ("change_language", 8) => "Cambia Lingua",
        ("change_language", 9) => "更改语言",
        ("change_language", 10) => "更改语言",
        ("change_language", 11) => "언어 변경",
        ("current_language", 0) => "現在の言語",
        ("current_language", 1) => "Current Language",
        ("current_language", 3) => "Idioma Actual",
        ("current_language", 4) => "Current Language",
        ("current_language", 5) => "Langue Actuelle",
        ("current_language", 6) => "Idioma Actual",
        ("current_language", 7) => "Aktuelle Sprache",
        ("current_language", 8) => "Lingua Corrente",
        ("current_language", 9) => "当前语言",
        ("current_language", 10) => "当前语言",
        ("current_language", 11) => "현재 언어",
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

#[allow(dead_code)]
pub fn get_current_lang() -> i32 {
    unsafe { CURRENT_LANG }
}

pub struct LanguageSettings;

//implementing the trait for menu switch methods
impl ConfigBasicMenuItemSwitchMethods for LanguageSettings {
    //initialize the content of the menu
    fn init_content(this: &mut ConfigBasicMenuItem) {
        unsafe {
            CURRENT_LANG = get_current_language();
            PREVIEW_LANG = CURRENT_LANG;
            update_preview_text(this);
        }
    }

    //changing the language preview
    extern "C" fn custom_call(this: &mut ConfigBasicMenuItem, _method_info: Option<&'static MethodInfo>) -> BasicMenuResult {
        unsafe {
            let new_lang = ConfigBasicMenuItem::change_key_value_i(PREVIEW_LANG, 0, 11, 1);
            if PREVIEW_LANG != new_lang {
                PREVIEW_LANG = new_lang;
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
            let help_text = get_localized_string("current_language", CURRENT_LANG);
            let lang_name = get_language_name(CURRENT_LANG, CURRENT_LANG);
            this.help_text = format!("{}: {}", help_text, lang_name).into();
        }
    }

    //set command text
    extern "C" fn set_command_text(this: &mut ConfigBasicMenuItem, _method_info: Option<&'static MethodInfo>) {
        unsafe {
            let command_text = get_language_name(CURRENT_LANG, CURRENT_LANG);
            this.command_text = command_text.to_string().into();
        }
    }
}

thread_local! {
    static CURRENT_MENU_ITEM: RefCell<Option<*mut ConfigBasicMenuItem>> = RefCell::new(None);
}


struct LanguageConfirmation;

//confirm the language change when the A button is pressed
extern "C" fn a_button_confirm(this: &mut ConfigBasicMenuItem, _method_info: Option<&'static MethodInfo>) -> BasicMenuResult {
    unsafe {
        CURRENT_MENU_ITEM.with(|item| {
            *item.borrow_mut() = Some(this as *mut _);
        });
        if PREVIEW_LANG != CURRENT_LANG {
            BasicMenuResult::se_cursor();
            YesNoDialog::bind::<LanguageConfirmation>(
            this.menu,  
            get_localized_string("change_language_confirm", CURRENT_LANG),
            get_localized_string("confirm_yes", CURRENT_LANG),
            get_localized_string("confirm_no", CURRENT_LANG)
            );
        }
    BasicMenuResult::se_cursor()
    }  
}

impl TwoChoiceDialogMethods for LanguageConfirmation {
    extern "C" fn on_first_choice(_this: &mut BasicDialogItemYes, _method_info: OptionalMethod) -> BasicMenuResult {
        unsafe {
            set_language(PREVIEW_LANG);
            CURRENT_LANG = PREVIEW_LANG;
            reflect_language_setting();
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


//update the preview text based on the selected language
fn update_preview_text(this: &mut ConfigBasicMenuItem) {
    unsafe {
        let lang_name = get_language_name(PREVIEW_LANG, CURRENT_LANG);
        this.command_text = lang_name.to_string().into();
        this.update_text();
    }
}

//update this plugin texts to reflect the current language
fn update_texts(this: &mut ConfigBasicMenuItem) {
    unsafe {
        this.title_text = get_localized_string("change_language", CURRENT_LANG).into();
        LanguageSettings::set_help_text(this, None);
        LanguageSettings::set_command_text(this, None);
        this.update_text();
    }
}

//callback function for language selection
#[no_mangle]
extern "C" fn language_callback() -> &'static mut ConfigBasicMenuItem {
    let switch = ConfigBasicMenuItem::new_switch::<LanguageSettings>("Change Language");
    if let Some(method) = switch.get_class_mut().get_virtual_method_mut("ACall") {
        method.method_ptr = a_button_confirm as _;
    }
    
    update_texts(switch);
    switch
}

//function to install the language setting in the game
pub fn language_install() {
    cobapi::install_game_setting(language_callback);
}