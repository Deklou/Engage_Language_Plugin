from pathlib import Path
p=Path('src/language.rs')
if not p.is_file(): raise SystemExit('Lancer depuis le dossier contenant src/language.rs')
s=p.read_text(encoding='utf-8')
if 'V9 PARENT CLASS' in s: raise SystemExit('V9 deja installee')
a=s.find('fn refresh_config_menu(');b=s.find('//update the preview text',a)
if min(a,b)<0: raise SystemExit('Fonction refresh_config_menu introuvable, aucune modification')
needle='''            set_language(PREVIEW_LANG);'''
if s.count(needle)!=1: raise SystemExit('Point de changement de langue introuvable, aucune modification')
backup=Path('src/language.rs.before_v9')
if not backup.exists(): backup.write_text(s,encoding='utf-8')
# Snapshot parent class before the language reload; never follow parent twice.
s=s.replace(needle,'''            // V9: inspect the direct parent before SetLanguage/ReloadMessages.
            CURRENT_MENU_ITEM.with(|item| {
                if let Some(menu_item) = *item.borrow() {
                    capture_v9_parent(&*menu_item);
                }
            });
            set_language(PREVIEW_LANG);''',1)
a=s.find('fn refresh_config_menu(');b=s.find('//update the preview text',a)
replacement='''thread_local! {
    static V9_PARENT_CLASS: RefCell<String> = RefCell::new(String::from("NOT READ"));
}

// This test reads exactly one parent before the language resources reload.
// Unlike V7, it does not walk the parent chain after reload_messages().
fn capture_v9_parent(current_item: &ConfigBasicMenuItem) {
    let info = match current_item.menu.proc.parent.as_ref() {
        None => "NONE".to_string(),
        Some(parent) => {
            // V9 risk boundary: dereferencing the direct parent to read its class.
            // If this crashes, parent inspection itself is unsafe on this runtime.
            parent.get_class().get_name()
        }
    };
    V9_PARENT_CLASS.with(|cell| *cell.borrow_mut() = info);
}

fn refresh_config_menu(current_item: &mut ConfigBasicMenuItem) {
    update_texts(current_item);
    let current_ptr = current_item as *const ConfigBasicMenuItem;
    let parent_name = V9_PARENT_CLASS.with(|cell| cell.borrow().clone());
    let mut marked = false;
    for entry in current_item.menu.full_menu_item_list.iter_mut() {
        let entry: &mut ConfigBasicMenuItem = &mut **entry;
        if marked || std::ptr::eq(entry as *const ConfigBasicMenuItem, current_ptr) {
            continue;
        }
        marked = true;
        entry.title_text = "V9 PARENT CLASS".into();
        entry.command_text = parent_name.as_str().into();
        entry.update_text();
    }
}

'''
s=s[:a]+replacement+s[b:]
p.write_text(s,encoding='utf-8')
print('V9 appliquee ; sauvegarde :',backup)
