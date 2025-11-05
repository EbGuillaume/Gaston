#!/bin/bash
for id in 3 5; do
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
print(f\"  Auteurs: {', '.join(m.get('writers', []))}\" )
" 2>/dev/null
    else
        echo "  ❌ Status: $status"
    fi
    echo
done
