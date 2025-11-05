#!/bin/bash
# Script pour réinitialiser complètement la base de données

set -e

echo "=================================="
echo "  RÉINITIALISATION DE LA DATABASE"
echo "=================================="
echo

# Confirmation
read -p "⚠️  Voulez-vous vraiment réinitialiser la database ? (oui/non): " confirm
if [ "$confirm" != "oui" ]; then
    echo "❌ Annulé"
    exit 0
fi

echo

# Arrêter le serveur si actif
if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "⚠️  Serveur détecté, veuillez l'arrêter avant de continuer"
    read -p "Appuyez sur Entrée une fois le serveur arrêté..."
fi

# Backup de la DB actuelle
if [ -f gaston.db ]; then
    backup_file="gaston.db.backup.$(date +%Y%m%d_%H%M%S)"
    echo "📦 Backup de la DB actuelle vers: $backup_file"
    cp gaston.db "$backup_file"
    echo "   ✓ Backup créé"
fi

# Supprimer toutes les données
echo
echo "🗑️  Suppression de toutes les données..."

sqlite3 gaston.db 2>/dev/null << 'EOF'
-- Désactiver les foreign keys temporairement
PRAGMA foreign_keys = OFF;

-- Supprimer toutes les données
DELETE FROM metadata;
DELETE FROM duplicates;
DELETE FROM operations_history;
DELETE FROM tasks;
DELETE FROM books;
DELETE FROM series;

-- Réactiver les foreign keys
PRAGMA foreign_keys = ON;

-- Vacuum pour nettoyer
VACUUM;
EOF

echo "   ✓ Toutes les données supprimées"

# Supprimer les caches
echo
echo "🧹 Nettoyage des caches..."

# Cache scraper
if [ -f backend/.scraper_cache.sqlite ]; then
    rm -f backend/.scraper_cache.sqlite
    echo "   ✓ Cache scraper supprimé"
else
    echo "   ℹ  Pas de cache scraper"
fi

# Cache Python
find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
echo "   ✓ Cache Python nettoyé"

# Vérification
echo
echo "📊 État de la base de données:"
echo
sqlite3 gaston.db << 'EOF'
.mode column
.headers on
SELECT
    (SELECT COUNT(*) FROM books) as books,
    (SELECT COUNT(*) FROM series) as series,
    (SELECT COUNT(*) FROM metadata) as metadata,
    (SELECT COUNT(*) FROM duplicates) as duplicates;
EOF

echo
echo "=================================="
echo "✅ Réinitialisation terminée !"
echo "=================================="
echo
echo "Pour scanner vos BDs, lancez:"
echo "  ./scan_all.sh"
