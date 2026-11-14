from pathlib import Path
p=Path('src/language.rs')
b=Path('src/language.rs.before_v8')
if not b.exists():
    raise SystemExit('Aucune sauvegarde V8 trouvee')
p.write_bytes(b.read_bytes())
print('Code precedent restaure')
