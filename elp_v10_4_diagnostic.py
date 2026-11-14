from pathlib import Path

path = Path('src/language.rs')
source = path.read_text(encoding='utf-8')
start = source.find('fn refresh_config_menu(current_item: &mut ConfigBasicMenuItem) {')
if start == -1:
    raise SystemExit('ERREUR: fonction refresh_config_menu introuvable; aucun fichier modifié.')
brace = source.find('{', start)
depth = 0
end = None
for i in range(brace, len(source)):
    if source[i] == '{': depth += 1
    elif source[i] == '}':
        depth -= 1
        if depth == 0:
            end = i + 1
            break
if end is None:
    raise SystemExit('ERREUR: fin de fonction introuvable; aucun fichier modifié.')
current = source[start:end]
if '[ELP V10.4]' in current:
    raise SystemExit('V10.4 déjà appliquée; aucun fichier modifié.')
if 'get_virtual_method(method_name)' not in current or 'std::mem::transmute(method_ptr)' not in current:
    raise SystemExit('ERREUR: la fonction ne correspond pas à la V10.3 attendue; aucun fichier modifié.')
replacement = '''fn refresh_config_menu(current_item: &mut ConfigBasicMenuItem) {
    // V10.4: diagnostic non-invasif.
    // Ne pas appeler de pointeurs IL2CPP avec une signature supposée.
    update_texts(current_item);

    let current_ptr = current_item as *const ConfigBasicMenuItem;
    let mut inspected = 0usize;

    for entry in current_item.menu.full_menu_item_list.iter_mut() {
        let entry: &mut ConfigBasicMenuItem = &mut **entry;
        if std::ptr::eq(entry as *const ConfigBasicMenuItem, current_ptr) {
            continue;
        }

        let class_name = entry.get_class().get_name();
        skyline::println!(
            "[ELP V10.4] ITEM #{} class={}",
            inspected,
            class_name
        );
        inspected += 1;
    }

    skyline::println!("[ELP V10.4] INSPECTED={} (native calls disabled)", inspected);
}'''
backup = path.with_name('language.rs.bak_v10_3')
if not backup.exists():
    backup.write_text(source, encoding='utf-8')
path.write_text(source[:start] + replacement + source[end:], encoding='utf-8')
print('OK: src/language.rs modifié (V10.4 diagnostic).')
print('Sauvegarde: src/language.rs.bak_v10_3')
