#!/bin/bash
# Script pour organiser la bibliothèque selon les standards Komga

PORT=${1:-8080}
DRY_RUN=${2:-false}
API_URL="http://localhost:$PORT/api"

echo "=================================="
echo "  ORGANISATION KOMGA"
echo "=================================="
echo

# Vérifier le serveur
if ! curl -s "$API_URL/health" >/dev/null 2>&1; then
    echo "❌ Serveur non accessible. Lancez: ./start_gaston.sh"
    exit 1
fi

# Preview de l'organisation
echo "📋 Aperçu de l'organisation..."
curl -s -X POST "$API_URL/organize/preview" \
    -H "Content-Type: application/json" \
    -d '{}' | python3 << 'EOF'
import sys, json
data = json.load(sys.stdin)
print(f"\n📚 Livres à organiser: {data.get('total_books', 0)}\n")
for preview in data.get('previews', [])[:5]:
    print(f"  • {preview['filename']}")
    print(f"    → {preview['target_path']}")
    print()
EOF

echo
read -p "Organiser la bibliothèque ? (oui/non): " confirm
if [ "$confirm" != "oui" ]; then
    echo "❌ Annulé"
    exit 0
fi

# Organiser
echo
echo "🔄 Organisation en cours..."

BODY="{\"dry_run\": $DRY_RUN, \"copy_instead_of_move\": false, \"inject_comicinfo\": true}"

curl -s -X POST "$API_URL/organize/organize" \
    -H "Content-Type: application/json" \
    -d "$BODY" | python3 << 'EOF'
import sys, json
data = json.load(sys.stdin)
print(f"\n✅ Organisation terminée !")
print(f"   • Organisés: {data.get('organized', 0)}/{data.get('total_books', 0)}")
print(f"   • Échecs: {data.get('failed', 0)}")
print(f"   • Ignorés: {data.get('skipped', 0)}")
EOF

echo
echo "=================================="
echo "✅ Terminé !"
echo "=================================="
