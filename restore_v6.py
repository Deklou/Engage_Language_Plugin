from pathlib import Path
p=Path('src/language.rs')
b=p.with_name('language.rs.bak_before_v6')
if not b.exists(): raise SystemExit('Sauvegarde introuvable')
p.write_bytes(b.read_bytes())
print('Code restaure')
