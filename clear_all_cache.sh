#!/bin/bash
# Script de nettoyage complet de Gaston
# Supprime tous les caches et métadonnées pour repartir de zéro

set -e

echo "=== Nettoyage complet de Gaston ==="
echo

# 1. Supprimer toutes les métadonnées de la base de données
if [ -f gaston.db ]; then
    echo "▶ Suppression des métadonnées dans la DB..."
    sqlite3 gaston.db << EOF
DELETE FROM metadata;
UPDATE books SET has_metadata = 0;
VACUUM;
EOF
    echo "  ✓ Métadonnées supprimées"
else
    echo "  ⚠ gaston.db n'existe pas"
fi

# 2. Supprimer le fichier de cache du scraper
if [ -f backend/.scraper_cache.sqlite ]; then
    echo "▶ Suppression du cache scraper..."
    rm -f backend/.scraper_cache.sqlite
    echo "  ✓ Cache scraper supprimé"
else
    echo "  ℹ Pas de cache scraper trouvé"
fi

# 3. Nettoyer le cache Python
echo "▶ Nettoyage du cache Python..."
find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find backend -name "*.pyc" -delete 2>/dev/null || true
echo "  ✓ Cache Python nettoyé"

# 4. Vider le cache API si le serveur tourne
echo "▶ Vérification du serveur API..."
if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "  ℹ Serveur détecté, vidage du cache API..."
    curl -s -X POST "http://localhost:8080/api/metadata/cache/clear" > /dev/null 2>&1 && \
        echo "  ✓ Cache API vidé" || \
        echo "  ⚠ Impossible de vider le cache API"
else
    echo "  ℹ Serveur non détecté (pas besoin de vider le cache API)"
fi

# 5. Supprimer les fichiers de test temporaires
echo "▶ Nettoyage des fichiers de test..."
rm -f test_*.py 2>/dev/null || true
echo "  ✓ Fichiers de test nettoyés"

echo
echo "==================================="
echo "✓ Nettoyage complet terminé !"
echo "==================================="
echo
echo "Vous pouvez maintenant lancer Gaston avec:"
echo "  ./start_gaston.sh"
echo
echo "Puis tester l'enrichissement avec:"
echo "  ./test_enrichment.sh"
echo
