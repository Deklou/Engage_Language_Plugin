from pathlib import Path
import sys
p=Path('src/language.rs')
if not p.exists(): sys.exit('Lance ce script a cote de Cargo.toml.')
s=p.read_text(encoding='utf-8')
a=s.find('fn refresh_config_menu(')
b=s.find('//update the preview text',a)
if a<0 or b<0: sys.exit('refresh_config_menu introuvable.')
if 'V6 diagnostic' in s: sys.exit('V6 deja installee.')
backup=p.with_name('language.rs.bak_before_v6')
if backup.exists(): sys.exit('Sauvegarde V6 deja presente : '+str(backup))
replacement='''// V6 diagnostic: direct non-virtual IL2CPP method lookup on derived setting class.
// V5 proved InitContent does not reset title or command for the existing item.
fn refresh_config_menu(current_item: &mut ConfigBasicMenuItem) {
    update_texts(current_item);
    let current_ptr = current_item as *const ConfigBasicMenuItem;
    let mut tested = false;
    for entry in current_item.menu.full_menu_item_list.iter_mut() {
        let entry: &mut ConfigBasicMenuItem = &mut **entry;
        if std::ptr::eq(entry as *const ConfigBasicMenuItem, current_ptr) || tested {
            continue;
        }
        tested = true;
        let probe: &'static Il2CppString = "V6 COMMAND PROBE".into();
        entry.command_text = probe;
        // SetCommandText is generally NOT a virtual method in the game dump.
        // Class-specific lookup is required instead of get_virtual_method.
        let method = entry.get_class().get_method_from_name("SetCommandText", 0);
        let state = if let Ok(info) = method {
            unsafe {
                let call: extern "C" fn(&mut ConfigBasicMenuItem, &MethodInfo) =
                    std::mem::transmute(info.method_ptr);
                call(entry, info);
            }
            if std::ptr::eq(entry.command_text, probe) { "V6 CMD UNCHANGED" }
            else { "V6 CMD REBUILT" }
        } else {
            "V6 CMD NO METHOD"
        };
        entry.title_text = "V6 DIRECT LOOKUP".into();
        entry.command_text = state.into();
        entry.update_text();
    }
    if !tested {
        current_item.title_text = "V6 NO OTHER ITEM".into();
        current_item.update_text();
    }
}

'''
backup.write_text(s,encoding='utf-8')
p.write_text(s[:a]+replacement+s[b:],encoding='utf-8')
print('V6 appliquee; sauvegarde:', backup)
