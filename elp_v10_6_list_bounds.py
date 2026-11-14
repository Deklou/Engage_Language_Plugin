from pathlib import Path

path = Path('src/language.rs')
if not path.is_file() or not Path('Cargo.toml').is_file():
    raise SystemExit('ERREUR : lancer depuis la racine du projet (avec Cargo.toml).')

source = path.read_text(encoding='utf-8')
start_token = 'fn refresh_config_menu(current_item: &mut ConfigBasicMenuItem) {'
start = source.find(start_token)
if start == -1:
    raise SystemExit('ERREUR : refresh_config_menu introuvable.')
brace = source.find('{', start)
depth = 0
end = None
for i in range(brace, len(source)):
    if source[i] == '{':
        depth += 1
    elif source[i] == '}':
        depth -= 1
        if depth == 0:
            end = i + 1
            break
if end is None:
    raise SystemExit('ERREUR : délimitation de fonction impossible.')
old = source[start:end]
if '[ELP V10.6]' in old:
    raise SystemExit('V10.6 déjà appliquée.')
if '[ELP V10.5]' not in old:
    raise SystemExit('ERREUR : V10.5 attendue, fichier inchangé.')

replacement = '''fn refresh_config_menu(current_item: &mut ConfigBasicMenuItem) {
    update_texts(current_item);

    // V10.6 : le Deref de List<T> couvre la CAPACITE du tableau.
    // Ne jamais visiter les emplacements apres list.len() (nombre d'elements reels).
    // Diagnostic de pointeurs uniquement : aucun get_class(), appel virtuel ou update_text() natif.
    let list = &current_item.menu.full_menu_item_list;
    let size = list.len();
    let capacity = list.capacity();
    skyline::println!(
        "[ELP V10.6] list size={} capacity={}", size, capacity
    );
    if size > capacity {
        skyline::println!("[ELP V10.6] INVALID list size > capacity; abort");
        return;
    }
    for (i, entry) in list.iter().take(size).enumerate() {
        let ptr = *entry as *const ConfigBasicMenuItem;
        skyline::println!("[ELP V10.6] entry #{} ptr={:p}", i, ptr);
    }
    skyline::println!("[ELP V10.6] completed {} entries", size);
}'''

backup = path.with_name('language.rs.bak_v10_5')
if backup.exists():
    raise SystemExit(f'ERREUR : sauvegarde deja presente : {backup}')
backup.write_text(source, encoding='utf-8')
path.write_text(source[:start] + replacement + source[end:], encoding='utf-8')
print('OK : V10.6 appliquee ; sauvegarde :', backup)
print('Diagnostic : bornage a size, adresses uniquement, aucune methode native.')
