#!/bin/bash
# Script pour enrichir tous les livres de la base de données

set -e

PORT=${1:-8080}
API_URL="http://localhost:$PORT/api"

echo "=================================="
echo "  ENRICHISSEMENT DES MÉTADONNÉES"
echo "=================================="
echo

# Vérifier que l'API est accessible
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo "❌ ERREUR: L'API n'est pas accessible sur $API_URL"
    exit 1
fi
echo "✓ Serveur accessible"
echo

# Compter les livres
total=$(sqlite3 gaston.db "SELECT COUNT(*) FROM books")
if [ "$total" -eq 0 ]; then
    echo "❌ Aucun livre dans la base de données"
    echo
    echo "Lancez d'abord:"
    echo "  ./scan_all.sh"
    exit 1
fi

echo "📚 Livres à enrichir: $total"
echo

# Vider le cache avant de commencer
echo "🧹 Vidage du cache..."
curl -s -X POST "$API_URL/metadata/cache/clear" > /dev/null
echo "   ✓ Cache vidé"
echo

# Compteurs
SUCCESS=0
MANUAL=0
FAILED=0
NO_MATCH=0

# Enrichir chaque livre
for book_id in $(sqlite3 gaston.db "SELECT id FROM books ORDER BY id"); do
    filename=$(sqlite3 gaston.db "SELECT filename FROM books WHERE id=$book_id")
    echo "=== Livre #$book_id ==="
    echo "📖 $filename"

    # Enrichir
    response=$(curl -s -X POST "$API_URL/metadata/match/$book_id")
    status=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('status', 'error'))" 2>/dev/null)

    case "$status" in
        "auto_validated")
            echo "   ✅ AUTO-VALIDÉ"
            SUCCESS=$((SUCCESS + 1))
            # Afficher les détails
            curl -s "$API_URL/metadata/book/$book_id" | python3 -c "
import sys, json
d = json.load(sys.stdin)
m = d.get('metadata', {})
if m:
    print(f\"      Série: {m.get('series_name')}\")
    print(f\"      Volume: {m.get('volume_number')}\")
    print(f\"      Titre: {m.get('title')}\")
    conf = m.get('confidence_score')
    if conf:
        print(f\"      Confiance: {conf:.2f}\")
" 2>/dev/null
            ;;
        "requires_validation")
            echo "   ⚠️  VALIDATION MANUELLE REQUISE"
            MANUAL=$((MANUAL + 1))
            ;;
        "no_match")
            echo "   ❌ AUCUNE CORRESPONDANCE"
            NO_MATCH=$((NO_MATCH + 1))
            ;;
        *)
            echo "   ❌ ERREUR"
            FAILED=$((FAILED + 1))
            ;;
    esac
    echo

    # Petit délai pour éviter de surcharger le serveur
    sleep 0.5
done

echo "=================================="
echo "📊 RÉSULTATS"
echo "=================================="
echo
echo "✅ Auto-validés: $SUCCESS"
echo "⚠️  Validation manuelle: $MANUAL"
echo "❌ Aucune correspondance: $NO_MATCH"
echo "❌ Erreurs: $FAILED"
echo "📚 Total: $total"
echo

# Statistiques finales
echo "=================================="
echo "📊 STATISTIQUES FINALES"
echo "=================================="
echo
sqlite3 gaston.db << 'EOF'
.mode column
.headers on
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN has_metadata = 1 THEN 1 ELSE 0 END) as with_metadata,
    SUM(CASE WHEN has_metadata = 0 THEN 1 ELSE 0 END) as without_metadata
FROM books;
EOF

echo
echo "=================================="
echo "✅ Enrichissement terminé !"
echo "=================================="
