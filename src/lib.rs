#![feature(lazy_cell, ptr_sub_ptr)]

mod language;
mod interface;
mod voice;
mod config_hook;

#[skyline::main(name = "language_plugin")]
pub fn main() {
    // Keep the V9 panic handler and both existing settings unchanged.
    std::panic::set_hook(Box::new(|info| {
        let location = info.location().unwrap();
        let msg = match info.payload().downcast_ref::<&'static str>() {
            Some(s) => *s,
            None => match info.payload().downcast_ref::<String>() {
                Some(s) => &s[..],
                None => "Box<Any>",
            },
        };
        let err_msg = format!(
            "Language plugin has panicked at '{}' with the following message:\n{}\0",
            location, msg
        );
        skyline::error::show_error(
            420,
            "Language plugin has panicked! Please open the details and send a screenshot to the developer, then close the game.\n\0",
            err_msg.as_str(),
        );
    }));

    config_hook::install();
    language::language_install();
    voice::voice_install();
}
