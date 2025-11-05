#!/bin/bash
# Script pour scanner tous les livres

PORT=${1:-8080}
SCAN_DIR="${2:-bd_sample}"

echo "=================================="
echo "  SCAN DES LIVRES"
echo "=================================="
echo "📂 Dossier: $SCAN_DIR"
echo

# Vérifier que le dossier existe
if [ ! -d "$SCAN_DIR" ]; then
    echo "❌ ERREUR: Le dossier '$SCAN_DIR' n'existe pas"
    exit 1
fi

# Vérifier que l'API est accessible
echo "🔍 Vérification du serveur..."
if ! curl -s "http://localhost:$PORT/health" >/dev/null 2>&1; then
    echo "❌ ERREUR: L'API n'est pas accessible"
    echo "Lancez d'abord le serveur avec: ./start_gaston.sh"
    exit 1
fi
echo "✓ Serveur accessible"
echo

# Obtenir le chemin absolu
SCAN_DIR_ABS=$(readlink -f "$SCAN_DIR")

# Scanner
echo "🔎 Scan en cours..."
TEMP_FILE=$(mktemp)
curl -s -X POST "http://localhost:$PORT/api/scan/directory" \
    -H "Content-Type: application/json" \
    -d "{\"path\": \"$SCAN_DIR_ABS\", \"calculate_hashes\": true, \"save_to_db\": true}" \
    > "$TEMP_FILE"

# Parser la réponse
python3 << EOF
import json, sys

with open("$TEMP_FILE") as f:
    try:
        data = json.load(f)
    except:
        print("❌ ERREUR: Réponse invalide de l'API")
        sys.exit(1)

if data.get('status') != 'success':
    print(f"❌ ERREUR: {data.get('message', 'Erreur inconnue')}")
    sys.exit(1)

print("✅ Scan terminé avec succès !")
print()
print("📊 Statistiques:")
print(f"   • Fichiers trouvés: {data.get('total_files', 0)}")
print(f"   • Sauvegardés en DB: {data.get('saved_to_db', 0)}")
print(f"   • Fichiers corrompus: {data.get('corrupted_count', 0)}")
print()

if data.get('by_extension'):
    print("📋 Par extension:")
    for ext, count in sorted(data.get('by_extension', {}).items()):
        print(f"   • {ext}: {count}")
    print()

size_mb = data.get('total_size_bytes', 0) / (1024 * 1024)
print(f"💾 Taille totale: {size_mb:.2f} MB")
EOF

if [ $? -ne 0 ]; then
    rm -f "$TEMP_FILE"
    exit 1
fi

rm -f "$TEMP_FILE"

echo
echo "=================================="
echo "📚 Liste des livres scannés:"
echo "=================================="
sqlite3 gaston.db << 'SQL'
SELECT printf('%3d | %-50s | %4s | %6.1f MB',
    id,
    CASE WHEN length(filename) > 50
         THEN substr(filename, 1, 47) || '...'
         ELSE filename END,
    extension,
    CAST(file_size AS REAL) / 1024 / 1024
) as info
FROM books
ORDER BY id;
SQL

echo
echo "=================================="
echo "✅ Scan terminé !"
echo "=================================="
echo
echo "Pour enrichir les métadonnées:"
echo "  ./enrich_all.sh"
