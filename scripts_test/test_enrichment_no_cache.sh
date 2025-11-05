#!/bin/bash
# Test de l'enrichissement livre par livre SANS cache
# Pour éviter les problèmes de cache entre les livres de la même série

PORT=${1:-8080}
API_URL="http://localhost:$PORT/api"

echo "=== Test d'enrichissement SANS cache (livre par livre) ==="
echo "API URL: $API_URL"
echo

# Vérifier que l'API est accessible
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo "❌ ERREUR: L'API n'est pas accessible sur $API_URL"
    exit 1
fi

echo "✓ API accessible"
echo

# Récupérer le nombre total de livres
TOTAL_BOOKS=$(sqlite3 gaston.db "SELECT COUNT(*) FROM books" 2>/dev/null || echo "0")

if [ "$TOTAL_BOOKS" -eq 0 ]; then
    echo "❌ Aucun livre trouvé dans la base de données"
    exit 1
fi

echo "📚 Nombre de livres dans la DB: $TOTAL_BOOKS"
echo

# Compteurs
SUCCESS=0
MANUAL=0
FAILED=0

# Enrichir chaque livre individuellement
for book_id in $(sqlite3 gaston.db "SELECT id FROM books ORDER BY id"); do
    echo "=== Livre #$book_id ==="

    # Récupérer le nom du fichier
    filename=$(sqlite3 gaston.db "SELECT filename FROM books WHERE id=$book_id" 2>/dev/null)
    echo "📖 Fichier: $filename"

    # VIDER LE CACHE avant chaque livre
    curl -s -X POST "$API_URL/metadata/cache/clear" > /dev/null 2>&1

    # Enrichir
    echo "🔍 Enrichissement en cours..."
    response=$(curl -s -X POST "$API_URL/metadata/match/$book_id")
    status=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'error'))" 2>/dev/null)

    if [ "$status" = "auto_validated" ]; then
        echo "✓ VALIDATION AUTOMATIQUE"
        SUCCESS=$((SUCCESS + 1))

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
    elif [ "$status" = "requires_validation" ]; then
        echo "⚠ VALIDATION MANUELLE REQUISE"
        MANUAL=$((MANUAL + 1))
    else
        echo "❌ ERREUR"
        FAILED=$((FAILED + 1))
    fi
    echo
done

echo "=== Résumé ==="
echo "Total: $TOTAL_BOOKS livres"
echo "  ✓ Validés automatiquement: $SUCCESS"
echo "  ⚠ Validation manuelle: $MANUAL"
echo "  ❌ Erreurs: $FAILED"
