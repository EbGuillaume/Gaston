#!/bin/bash
# Script pour afficher l'état de Gaston

echo "╔════════════════════════════════════════╗"
echo "║   GASTON - ÉTAT DU SYSTÈME             ║"
echo "╚════════════════════════════════════════╝"
echo

# Vérifier le serveur
echo "🌐 Serveur:"
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "   ✅ En ligne (http://localhost:8080)"
else
    echo "   ❌ Hors ligne"
    echo "   Pour démarrer: ./start_gaston.sh"
fi
echo

# Statistiques de la base
echo "📊 Base de données:"
sqlite3 gaston.db << 'EOF'
.mode column
.headers on
SELECT
    (SELECT COUNT(*) FROM books) as 'Livres',
    (SELECT COUNT(*) FROM books WHERE has_metadata = 1) as 'Enrichis',
    (SELECT COUNT(*) FROM books WHERE has_metadata = 0) as 'Sans métadonnées',
    (SELECT COUNT(*) FROM series) as 'Séries',
    (SELECT COUNT(DISTINCT source) FROM metadata) as 'Sources';
EOF
echo

# Taille de la base
DB_SIZE=$(du -h gaston.db | cut -f1)
echo "💾 Taille de la DB: $DB_SIZE"
echo

# Répartition par extension
echo "📋 Livres par extension:"
sqlite3 gaston.db << 'EOF'
SELECT extension, COUNT(*) as count
FROM books
GROUP BY extension
ORDER BY count DESC;
EOF
echo

# Derniers livres ajoutés
echo "📚 Derniers livres scannés:"
sqlite3 gaston.db << 'EOF'
.mode column
.width 3 50 10
SELECT
    id,
    CASE WHEN length(filename) > 50
         THEN substr(filename, 1, 47) || '...'
         ELSE filename END as filename,
    CASE WHEN has_metadata = 1 THEN '✅ Enrichi' ELSE '⏳ En attente' END as status
FROM books
ORDER BY id DESC
LIMIT 10;
EOF
echo

# Séries les plus représentées
echo "🏆 Séries les plus représentées:"
sqlite3 gaston.db << 'EOF'
SELECT
    m.series_name,
    COUNT(*) as volumes
FROM books b
JOIN metadata m ON b.id = m.book_id
GROUP BY m.series_name
HAVING COUNT(*) > 1
ORDER BY volumes DESC
LIMIT 5;
EOF
echo

echo "════════════════════════════════════════"
echo "Pour plus d'informations: cat README_SCRIPTS.md"
