from pathlib import Path

path = Path("src/language.rs")
if not path.exists():
    raise SystemExit("Erreur : lance ce script depuis le dossier contenant Cargo.toml")
src = path.read_text(encoding="utf-8")
start = src.find("fn refresh_config_menu(")
end = src.find("//update the preview text", start)
if start < 0 or end < 0:
    raise SystemExit("Impossible de localiser refresh_config_menu : aucun fichier modifie")
if "V8 PARENT PTR" in src:
    raise SystemExit("V8 deja appliquee")
backup = Path("src/language.rs.before_v8")
if not backup.exists():
    backup.write_text(src, encoding="utf-8")
replacement = r'''// V8: pointer-only diagnostic. NO DEREFERENCE OF PARENT PROCESSES.
// Can be installed directly over V7. No intermediate restore needed.
fn refresh_config_menu(current_item: &mut ConfigBasicMenuItem) {
    // Reading the pointer value is safe; V7 crashed while following its target.
    let parent_text = match current_item.menu.proc.parent.as_ref() {
        Some(parent) => format!("{:p}", *parent),
        None => "NONE".to_string(),
    };
    update_texts(current_item);
    let current_ptr = current_item as *const ConfigBasicMenuItem;
    let mut displayed = false;
    for entry in current_item.menu.full_menu_item_list.iter_mut() {
        let entry: &mut ConfigBasicMenuItem = &mut **entry;
        if std::ptr::eq(entry as *const ConfigBasicMenuItem, current_ptr) || displayed {
            continue;
        }
        displayed = true;
        entry.title_text = "V8 PARENT PTR".into();
        entry.command_text = parent_text.clone().into();
        entry.update_text();
    }
}

'''
path.write_text(src[:start] + replacement + src[end:], encoding="utf-8")
print("V8 installee directement sur la version actuelle.")
print("Sauvegarde :", backup)
