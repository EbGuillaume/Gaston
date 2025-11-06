#!/bin/bash

# Script pour enrichir tous les livres de la bibliothèque
# Usage: ./enrich_all_books.sh [PORT]

PORT=${1:-8080}
API_URL="http://localhost:$PORT"

echo "🔍 Récupération du nombre de livres..."

# Récupérer le nombre total de livres
TOTAL_BOOKS=$(curl -s "$API_URL/api/organize/stats" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_books'])")

echo "📚 Livres trouvés: $TOTAL_BOOKS"

if [ "$TOTAL_BOOKS" = "0" ]; then
    echo "❌ Aucun livre à enrichir. Scannez d'abord un dossier!"
    exit 1
fi

echo ""
echo "🚀 Enrichissement de $TOTAL_BOOKS livres..."
echo ""

SUCCESS=0
FAILED=0

for id in $(seq 1 $TOTAL_BOOKS); do
    echo -n "  📖 Livre $id/$TOTAL_BOOKS... "

    RESPONSE=$(curl -s -X POST "$API_URL/api/metadata/match/$id" -H "Content-Type: application/json")
    STATUS=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null || echo "error")

    if [ "$STATUS" = "success" ]; then
        echo "✅"
        ((SUCCESS++))
    else
        echo "❌"
        ((FAILED++))
    fi
done

echo ""
echo "✅ Enrichissement terminé!"
echo "   • Succès: $SUCCESS"
echo "   • Échecs: $FAILED"
echo ""
echo "📊 Stats finales:"
curl -s "$API_URL/api/organize/stats" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"   • Total: {d['total_books']}\")
print(f\"   • Avec métadonnées: {d['books_with_metadata']}\")
print(f\"   • Prêts à organiser: {d['books_ready_to_organize']}\")
"
