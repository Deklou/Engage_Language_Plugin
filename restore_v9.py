from pathlib import Path
p=Path('src/language.rs'); backup=Path('src/language.rs.before_v9')
if not backup.exists(): raise SystemExit('Sauvegarde before_v9 absente, aucune modification')
p.write_bytes(backup.read_bytes())
print('src/language.rs restaure avant la V9')
