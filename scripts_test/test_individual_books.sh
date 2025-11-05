#!/bin/bash
# Test des livres problématiques individuellement

PORT=${1:-8080}
API_URL="http://localhost:$PORT/api"

echo "=== Test individuel des livres #3, #4, #6 ==="
echo

for book_id in 3 4 6; do
    echo "=== Test livre #$book_id ==="

    # Récupérer le nom du fichier
    filename=$(sqlite3 gaston.db "SELECT filename FROM books WHERE id=$book_id" 2>/dev/null)
    echo "📖 Fichier: $filename"

    # Nettoyer les métadonnées de ce livre
    sqlite3 gaston.db "DELETE FROM metadata WHERE book_id = $book_id; UPDATE books SET has_metadata = 0 WHERE id = $book_id;" 2>/dev/null

    # Vider le cache
    curl -s -X POST "$API_URL/metadata/cache/clear" > /dev/null 2>&1

    # Enrichir
    echo "🔍 Enrichissement..."
    response=$(curl -s -X POST "$API_URL/metadata/match/$book_id")
    status=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'error'))" 2>/dev/null)

    if [ "$status" = "auto_validated" ]; then
        echo "✓ VALIDATION AUTOMATIQUE"

        # Récupérer les métadonnées
        metadata=$(curl -s "$API_URL/metadata/book/$book_id")
        echo "$metadata" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('status') == 'success':
    m = data.get('metadata', {})
    print(f\"  Série: {m.get('series_name')}\")
    print(f\"  Volume: {m.get('volume_number')}\")
    print(f\"  Titre: {m.get('title')}\")
    print(f\"  Confiance: {m.get('confidence_score')}\")
" 2>/dev/null
    else
        echo "❌ ERREUR: status=$status"
        echo "$response" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null
    fi

    echo
    sleep 2
done
