#!/bin/bash
response=$(curl -s -X POST "http://localhost:8080/api/scan/directory" \
    -H "Content-Type: application/json" \
    -d '{"path": "/home/guillaume/work/Gaston/bd_sample", "calculate_hashes": true, "save_to_db": true}')

echo "===== RAW RESPONSE ====="
echo "$response"
echo

echo "===== PARSED ====="
echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print('Status:', d.get('status')); print('Files:', d.get('total_files'))"
