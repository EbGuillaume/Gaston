#!/bin/bash
# Script tout-en-un: reset + scan + enrich

set -e

echo "╔════════════════════════════════════════╗"
echo "║   GASTON - DÉMARRAGE COMPLET           ║"
echo "╚════════════════════════════════════════╝"
echo
echo "Ce script va:"
echo "  1. Réinitialiser la base de données"
echo "  2. Scanner tous les livres"
echo "  3. Enrichir les métadonnées"
echo
read -p "Continuer ? (oui/non): " confirm
if [ "$confirm" != "oui" ]; then
    echo "❌ Annulé"
    exit 0
fi

# Vérifier que le serveur tourne
if ! curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
    echo
    echo "⚠️  Le serveur n'est pas démarré"
    echo "Démarrage du serveur..."
    ./start_gaston.sh &
    SERVER_PID=$!
    sleep 3

    # Vérifier que le serveur est bien démarré
    if ! curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
        echo "❌ Impossible de démarrer le serveur"
        exit 1
    fi
    echo "✓ Serveur démarré (PID: $SERVER_PID)"
else
    echo "✓ Serveur déjà actif"
fi

echo
echo "════════════════════════════════════════"
echo "ÉTAPE 1/3 - Réinitialisation de la DB"
echo "════════════════════════════════════════"
echo

# Reset sans confirmation interactive
sqlite3 gaston.db 2>/dev/null << 'EOF' || true
PRAGMA foreign_keys = OFF;
DELETE FROM metadata;
DELETE FROM duplicates;
DELETE FROM operations_history;
DELETE FROM tasks;
DELETE FROM books;
DELETE FROM series;
PRAGMA foreign_keys = ON;
VACUUM;
EOF

rm -f backend/.scraper_cache.sqlite 2>/dev/null || true
find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

echo "✅ Base de données réinitialisée"

echo
echo "════════════════════════════════════════"
echo "ÉTAPE 2/3 - Scan des livres"
echo "════════════════════════════════════════"
echo

./scan_all.sh

echo
echo "════════════════════════════════════════"
echo "ÉTAPE 3/3 - Enrichissement"
echo "════════════════════════════════════════"
echo

./enrich_all.sh

echo
echo "╔════════════════════════════════════════╗"
echo "║   ✅ TERMINÉ !                          ║"
echo "╚════════════════════════════════════════╝"
echo
echo "Tous vos livres ont été scannés et enrichis."
echo
echo "Pour voir les résultats:"
echo "  sqlite3 gaston.db 'SELECT b.id, b.filename, m.volume_number, m.title FROM books b LEFT JOIN metadata m ON b.id = m.book_id ORDER BY b.id'"
