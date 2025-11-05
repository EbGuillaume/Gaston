#!/bin/bash
# Test tous les 6 livres

./clear_all_cache.sh > /dev/null 2>&1

echo "=== Test de tous les livres ==="
echo

for id in 1 2 3 4 5 6; do
    echo "=== Livre #$id ==="
    filename=$(sqlite3 gaston.db "SELECT filename FROM books WHERE id=$id")
    echo "📖 $filename"

    response=$(curl -s -X POST "http://localhost:8080/api/metadata/match/$id")
    status=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('status', 'error'))" 2>/dev/null)

    if [ "$status" = "auto_validated" ]; then
        curl -s "http://localhost:8080/api/metadata/book/$id" | python3 -c "
import sys, json
d = json.load(sys.stdin)
m = d.get('metadata', {})
print(f\"  ✓ Volume: {m.get('volume_number')}, Titre: {m.get('title')}\")
if m.get('writers'):
    print(f\"  Auteurs: {', '.join(m.get('writers', []))}\")
" 2>/dev/null
    else
        echo "  ❌ Status: $status"
    fi
    echo
done

echo "=== Vérification finale ==="
echo
sqlite3 gaston.db "SELECT b.id, m.volume_number, m.title FROM books b LEFT JOIN metadata m ON b.id = m.book_id ORDER BY b.id"
