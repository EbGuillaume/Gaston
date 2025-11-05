#!/bin/bash
# Test metadata enrichment for all books

echo "=== Testing metadata enrichment for all books ==="
echo

for i in {1..6}; do
    echo "=== Book $i ==="
    curl -s http://localhost:8081/api/metadata/book/$i | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['status'] == 'success' and data['metadata']:
    m = data['metadata']
    print(f\"Series: {m['series_name']}\")
    print(f\"Volume: {m['volume_number']}\")
    print(f\"Title: {m['title']}\")
    print(f\"Writers: {', '.join(m['writers']) if m['writers'] else 'N/A'}\")
    print(f\"Pencillers: {', '.join(m['pencillers']) if m['pencillers'] else 'N/A'}\")
    print(f\"Publisher: {m['publisher']}\")
    print(f\"Confidence: {m['confidence_score']}\")
else:
    print('No metadata')
"
    echo
done
