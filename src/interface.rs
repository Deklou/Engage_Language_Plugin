#[unity::from_offset("App", "Language", "GetLang")]
pub fn get_current_language() -> i32;

#[unity::from_offset("App", "Language", "SetLang")]
pub fn set_language(lang: i32);

#[unity::from_offset("App", "Language", "ReflectSetting")]
pub fn reflect_language_setting();

#[unity::from_offset("App", "Language", "GetVoice")]
pub fn get_current_voice() -> i32;

#[unity::from_offset("App", "Language", "SetVoice")]
pub fn set_voice(voice: i32);

#[unity::from_offset("App", "Language", "ReflectSetting")]
pub fn reflect_voice_setting();

#[unity::from_offset("App", "Mess", "Reload")]
pub fn reload_messages();

#[unity::from_offset("App", "Mess", "Get")]
pub fn get_message(label: &unity::prelude::Il2CppString) -> &'static unity::prelude::Il2CppString;