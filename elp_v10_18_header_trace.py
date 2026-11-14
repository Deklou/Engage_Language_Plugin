#!/usr/bin/env python3
"""ELP V10.18 — trace MSBT strings requested while Settings is built.

Diagnostic only: preserves the V10.17 visual refresh and native commands.
Does not install hooks or modify Unity UI objects.
"""
from pathlib import Path
import shutil

p = Path('src/config_hook.rs')
if not Path('Cargo.toml').is_file() or not p.is_file():
    raise SystemExit('Execute depuis la racine du projet Rust.')
s = p.read_text(encoding='utf-8')
if '[ELP V10.17]' not in s or 'fn mess_get_capture(' not in s:
    raise SystemExit('La V10.17 est requise. Aucun fichier modifie.')
if '[ELP V10.18]' in s:
    raise SystemExit('La V10.18 semble deja appliquee. Aucun fichier modifie.')

old = '''                match map.entry(result as usize) {
                    Entry::Vacant(v) => { v.insert(Some(key)); }
                    Entry::Occupied(mut o) => {
                        if o.get().as_ref() != Some(&key) { o.insert(None); }
                    }
                }'''
new = '''                match map.entry(result as usize) {
                    Entry::Vacant(v) => {
                        // During menu creation only, log the MSBT key and original
                        // visible string together. This is the first place where
                        // the result pointer is known to be valid. No UI writes.
                        let resolved = (&*result).get_string().unwrap_or_default();
                        if resolved.chars().count() <= 180 {
                            skyline::println!(
                                "[ELP V10.18] MSBT key={:?} value={:?}",
                                key, resolved
                            );
                        } else {
                            skyline::println!("[ELP V10.18] MSBT key={:?} value=<long>", key);
                        }
                        v.insert(Some(key));
                    }
                    Entry::Occupied(mut o) => {
                        if o.get().as_ref() != Some(&key) { o.insert(None); }
                    }
                }'''
if s.count(old) != 1:
    raise SystemExit('Le bloc de capture de la V10.17 ne correspond pas. Aucun fichier modifie.')
s = s.replace(old, new, 1)

old = '''            skyline::println!("[ELP V10.17] captured Mess.Get unique return pointers={}", n);'''
new = '''            skyline::println!("[ELP V10.17] captured Mess.Get unique return pointers={}", n);
            skyline::println!("[ELP V10.18] END Settings-build MSBT trace (unique pointers={})", n);'''
if s.count(old) != 1:
    raise SystemExit('Le bilan de capture V10.17 est introuvable. Aucun fichier modifie.')
s = s.replace(old, new, 1)
old = '''skyline::println!("[ELP V10.17] Installing Mess.Get title-key capture + native refresh");'''
new = '''skyline::println!("[ELP V10.18] Installing scoped Settings-header MSBT trace (keeps V10.17 refresh)");'''
if s.count(old) != 1:
    raise SystemExit('Le message d\'installation V10.17 est introuvable. Aucun fichier modifie.')
s = s.replace(old, new, 1)

backup = Path('src/config_hook.rs.bak_v10_17')
if backup.exists():
    raise SystemExit(f'Sauvegarde existante : {backup}. Aucun fichier modifie.')
shutil.copy2(p, backup)
p.write_text(s, encoding='utf-8')
print(f'V10.18 appliquee ; sauvegarde : {backup}')
print('Test : ouvrir Settings en anglais, changer en francais sans quitter le menu.')
print('Le log [ELP V10.18] capture les cles et les textes MSBT lus pendant la creation de Settings.')
