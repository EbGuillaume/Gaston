#!/bin/bash
# Test de l'enrichissement des métadonnées pour tous les livres

PORT=${1:-8080}  # Port par défaut 8080, modifiable en argument
API_URL="http://localhost:$PORT/api"

echo "=== Test d'enrichissement des métadonnées ==="
echo "API URL: $API_URL"
echo

# Vérifier que l'API est accessible
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo "❌ ERREUR: L'API n'est pas accessible sur $API_URL"
    echo "Assurez-vous que le serveur est démarré avec: ./start_gaston.sh"
    exit 1
fi

echo "✓ API accessible"
echo

# Récupérer le nombre total de livres
TOTAL_BOOKS=$(sqlite3 gaston.db "SELECT COUNT(*) FROM books" 2>/dev/null || echo "0")

if [ "$TOTAL_BOOKS" -eq 0 ]; then
    echo "❌ Aucun livre trouvé dans la base de données"
    echo "Lancez d'abord un scan avec: curl -X POST $API_URL/scanner/scan"
    exit 1
fi

echo "📚 Nombre de livres dans la DB: $TOTAL_BOOKS"
echo

# Fonction pour afficher les métadonnées
show_metadata() {
    local book_id=$1

    echo "=== Livre #$book_id ==="

    # Récupérer le nom du fichier
    local filename=$(sqlite3 gaston.db "SELECT filename FROM books WHERE id=$book_id" 2>/dev/null)
    echo "📖 Fichier: $filename"

    # Tester l'enrichissement (POST request)
    echo "🔍 Enrichissement en cours..."
    local response=$(curl -s -X POST "$API_URL/metadata/match/$book_id")

    # Parser et afficher les résultats
    local status=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'error'))")

    if [ "$status" = "auto_validated" ]; then
        echo "✓ VALIDATION AUTOMATIQUE"

        # Récupérer les métadonnées complètes
        local metadata=$(curl -s "$API_URL/metadata/book/$book_id")

        echo "$metadata" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('status') == 'success':
        m = data.get('metadata', {})
        print(f\"  Série: {m.get('series_name', 'N/A')}\")
        print(f\"  Volume: {m.get('volume_number', 'N/A')}\")
        print(f\"  Titre: {m.get('title', 'N/A')}\")
        writers = m.get('writers', [])
        print(f\"  Auteurs: {', '.join(writers) if writers else 'N/A'}\")
        pencillers = m.get('pencillers', [])
        print(f\"  Dessinateurs: {', '.join(pencillers) if pencillers else 'N/A'}\")
        print(f\"  Éditeur: {m.get('publisher', 'N/A')}\")
        print(f\"  Date: {m.get('publication_date', 'N/A')}\")
        print(f\"  ISBN: {m.get('isbn', 'N/A')}\")
        print(f\"  Confiance: {m.get('confidence_score', 'N/A')}\")
        print(f\"  Source: {m.get('source', 'N/A')}\")
except Exception as e:
    print(f'Erreur: {e}')
"
    elif [ "$status" = "requires_validation" ]; then
        echo "⚠ VALIDATION MANUELLE REQUISE"
        echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
matches = data.get('matches', [])
print(f\"  {len(matches)} correspondance(s) trouvée(s)\")
for i, m in enumerate(matches[:3], 1):
    print(f\"  {i}. {m.get('series_name')} #{m.get('volume_number')} (conf: {m.get('confidence'):.2f})\")
"
    elif [ "$status" = "no_match" ]; then
        echo "❌ AUCUNE CORRESPONDANCE"
    else:
        echo "❌ ERREUR"
        echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"  {data.get('message', 'Unknown error')}\")" 2>/dev/null || echo "  Erreur inconnue"
    fi
    echo
}

# Option 1: Tester un livre spécifique
if [ -n "$2" ]; then
    show_metadata "$2"
    exit 0
fi

# Option 2: Tester tous les livres
for book_id in $(sqlite3 gaston.db "SELECT id FROM books ORDER BY id"); do
    show_metadata "$book_id"
done

echo "=== Résumé ==="
echo "Total de livres testés: $TOTAL_BOOKS"
echo

# Afficher les statistiques de métadonnées
echo "Statistiques:"
sqlite3 gaston.db << EOF
SELECT
    CASE WHEN has_metadata THEN 'Avec métadonnées' ELSE 'Sans métadonnées' END as status,
    COUNT(*) as count
FROM books
GROUP BY has_metadata;
EOF
