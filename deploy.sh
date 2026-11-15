#!/usr/bin/env bash
# Compile le plugin Engage et remplace son NRO dans la SD virtuelle de Ryujinx.
# Usage : bash deploy.sh
# Si plusieurs installations existent :
#   RYUJINX_NRO_PATH="/mnt/c/.../liblanguage_plugin.nro" bash deploy.sh
set -euo pipefail

cd "$(dirname "$(realpath "$0")")"
nro_name="liblanguage_plugin.nro"

if [[ -n "${RYUJINX_NRO_PATH:-}" ]]; then
    destination="$RYUJINX_NRO_PATH"
    if [[ ! -f "$destination" ]]; then
        echo "Erreur : le NRO cible n'existe pas : $destination" >&2
        exit 1
    fi
else
    # On recherche uniquement un NRO DEJA installé : pas de dossier supposé.
    candidates=()
    for engage_dir in /mnt/c/Users/*/AppData/Roaming/Ryujinx/sdcard/engage; do
        if [[ -d "$engage_dir" ]]; then
            while IFS= read -r -d '' file; do
                candidates+=("$file")
            done < <(find "$engage_dir" -type f -name "$nro_name" -print0)
        fi
    done

    if (( ${#candidates[@]} != 1 )); then
        echo "Erreur : ${#candidates[@]} installation(s) du NRO trouvée(s)." >&2
        printf '  %s\n' "${candidates[@]}" >&2
        echo "Indique le bon chemin : RYUJINX_NRO_PATH=/chemin/vers/$nro_name bash deploy.sh" >&2
        exit 1
    fi
    destination="${candidates[0]}"
fi

echo "Compilation Skyline..."
cargo skyline build --release

# La commande Cargo Skyline dépose normalement le NRO dans target/.
mapfile -d '' outputs < <(find target -type f -name "$nro_name" -print0)
if (( ${#outputs[@]} == 0 )); then
    echo "Erreur : $nro_name introuvable après compilation." >&2
    exit 1
fi
# Si plusieurs variantes existent, prendre la plus récemment modifiée.
built="${outputs[0]}"
for file in "${outputs[@]:1}"; do
    if [[ "$file" -nt "$built" ]]; then
        built="$file"
    fi
done

# Ne rien remplacer si la compilation a échoué ; conserver une sauvegarde.
cp -p -- "$destination" "${destination}.bak"
tmp="${destination}.tmp.$$"
trap 'rm -f -- "$tmp"' EXIT
cp -- "$built" "$tmp"
mv -f -- "$tmp" "$destination"
trap - EXIT

echo "NRO déployé : $destination"
echo "Ancienne version : ${destination}.bak"
echo "Relance Ryujinx pour tester."
