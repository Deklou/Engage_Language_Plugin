from pathlib import Path

path = Path('src/language.rs')
if not path.is_file():
    raise SystemExit('ERREUR : lancer depuis le dossier contenant Cargo.toml.')
source = path.read_text(encoding='utf-8')
start = source.find('fn refresh_config_menu(current_item: &mut ConfigBasicMenuItem) {')
if start < 0:
    raise SystemExit('ERREUR : fonction introuvable.')
brace = source.find('{', start)
depth = 0
end = None
for pos in range(brace, len(source)):
    if source[pos] == '{':
        depth += 1
    elif source[pos] == '}':
        depth -= 1
        if depth == 0:
            end = pos + 1
            break
if end is None:
    raise SystemExit('ERREUR : fin de fonction introuvable.')
current = source[start:end]
if '[ELP V10.5]' in current:
    raise SystemExit('V10.5 déjà appliquée.')
if '[ELP V10.4]' not in current:
    raise SystemExit('ERREUR : fonction V10.4 attendue ; rien modifié.')
backup = path.with_name('language.rs.bak_v10_4')
if backup.exists():
    raise SystemExit('ERREUR : sauvegarde V10.4 déjà présente ; rien modifié.')
replacement = '''fn refresh_config_menu(current_item: &mut ConfigBasicMenuItem) {
    // V10.5 : aucun parcours des autres objets du menu.
    // Ne toucher qu'a l'element dont le type est connu.
    update_texts(current_item);
    skyline::println!(
        "[ELP V10.5] Custom language item updated; native menu untouched"
    );
}'''
backup.write_text(source, encoding='utf-8')
path.write_text(source[:start] + replacement + source[end:], encoding='utf-8')
print('OK : V10.5 appliquee. Sauvegarde :', backup)
print('Ne corrige PAS encore le rafraichissement des options natives.')
