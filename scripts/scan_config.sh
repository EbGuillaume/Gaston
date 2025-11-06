#!/bin/bash
# Script pour scanner tous les dossiers configurés dans config.yaml

PORT=${1:-8080}

echo "╔════════════════════════════════════════╗"
echo "║   SCAN DES BIBLIOTHÈQUES (config.yaml) ║"
echo "╚════════════════════════════════════════╝"
echo

# Vérifier que config.yaml existe
if [ ! -f config.yaml ]; then
    echo "❌ ERREUR: config.yaml introuvable"
    echo "Copiez config.example.yaml vers config.yaml et modifiez les chemins"
    exit 1
fi

# Extraire les chemins du config.yaml
echo "📂 Lecture de config.yaml..."
library_paths=$(python3 << 'PYEOF'
import yaml

try:
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
        paths = config.get('gaston', {}).get('library_paths', [])
        for path in paths:
            print(path)
except Exception as e:
    print(f"ERREUR: {e}", file=__import__('sys').stderr)
    exit(1)
PYEOF
)

if [ -z "$library_paths" ]; then
    echo "❌ ERREUR: Aucun chemin trouvé dans config.yaml"
    echo "Vérifiez la section 'library_paths'"
    exit 1
fi

# Afficher les chemins trouvés
echo "✓ Chemins configurés:"
echo "$library_paths" | while read -r path; do
    echo "  • $path"
done
echo

# Scanner chaque dossier
total_scanned=0
total_errors=0

echo "$library_paths" | while read -r path; do
    if [ -z "$path" ]; then
        continue
    fi

    echo "════════════════════════════════════════"
    echo "📚 Scan de: $path"
    echo "════════════════════════════════════════"
    echo

    if [ ! -d "$path" ]; then
        echo "⚠️  ATTENTION: Le dossier n'existe pas, ignoré"
        echo
        continue
    fi

    # Utiliser le script de scan existant
    ./scan_all.sh "$PORT" "$path"

    if [ $? -eq 0 ]; then
        echo "✅ Scan terminé pour $path"
    else
        echo "❌ Erreur lors du scan de $path"
    fi
    echo
done

echo "╔════════════════════════════════════════╗"
echo "║   ✅ SCAN TERMINÉ                       ║"
echo "╚════════════════════════════════════════╝"
echo
echo "Pour enrichir les métadonnées:"
echo "  ./enrich_all.sh"
