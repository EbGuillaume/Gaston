#!/bin/bash
# Script de démarrage de Gaston

set -e  # Arrêter en cas d'erreur

echo "=== Démarrage de Gaston ==="
echo

# 1. Activer l'environnement virtuel
echo "▶ Activation du venv..."
source venv/bin/activate

# 2. Installer/mettre à jour les dépendances si nécessaire
echo "▶ Vérification des dépendances..."
pip install -q -r requirements.txt

# 3. Copier le fichier de config si nécessaire
if [ ! -f config.yaml ]; then
    echo "⚠ Pas de config.yaml trouvé"
    echo "▶ Copie de config.example.yaml vers config.yaml..."
    cp config.example.yaml config.yaml
    echo "✓ Vous pouvez éditer config.yaml selon vos besoins"
fi

# 4. Initialiser la base de données si nécessaire
if [ ! -f gaston.db ]; then
    echo "▶ Initialisation de la base de données..."
    python -c "from backend.database.session import init_db; init_db()"
fi

# 5. Lancer le serveur
echo
echo "=== Démarrage du serveur FastAPI ==="
echo "URL: http://127.0.0.1:8080"
echo "Docs: http://127.0.0.1:8080/docs"
echo
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo

python backend/api/main.py dev
