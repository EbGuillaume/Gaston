# Gaston - Guide de Démarrage Rapide

## 🧹 Nettoyage complet (pour tests)

Pour repartir de zéro (comme un premier lancement) :
```bash
./clear_all_cache.sh
```

Ce script supprime :
- ✓ Toutes les métadonnées de la DB
- ✓ Le cache du scraper
- ✓ Le cache Python
- ✓ Le cache API (si serveur actif)
- ✓ Les fichiers de test temporaires

---

## 🚀 Lancer Gaston

### Méthode 1: Script automatique (recommandé)
```bash
./start_gaston.sh
```

Ce script va :
- ✓ Activer le venv
- ✓ Installer les dépendances
- ✓ Créer config.yaml si nécessaire
- ✓ Initialiser la DB si nécessaire
- ✓ Lancer le serveur sur http://127.0.0.1:8080

### Méthode 2: Commandes manuelles
```bash
# 1. Activer l'environnement virtuel
source venv/bin/activate

# 2. Installer les dépendances (première fois uniquement)
pip install -r requirements.txt

# 3. Copier la config (première fois uniquement)
cp config.example.yaml config.yaml

# 4. Lancer le serveur
python backend/api/main.py dev
```

Le serveur démarre sur **http://127.0.0.1:8080**
- API Docs: http://127.0.0.1:8080/docs
- Health check: http://127.0.0.1:8080/api/health

---

## 🧪 Workflow de test complet

Pour faire un test complet de A à Z :

```bash
# 1. Nettoyer tout
./clear_all_cache.sh

# 2. Lancer le serveur
./start_gaston.sh
# (Attendre que le serveur démarre)

# 3. Dans un autre terminal, tester l'enrichissement
./test_enrichment.sh
```

**Note :** Si vous retestez un livre déjà enrichi, vous aurez une erreur. Utilisez `./clear_all_cache.sh` pour repartir de zéro.

---

## 📚 Tester l'enrichissement des métadonnées

### Option 1: Script de test complet (recommandé)
```bash
# Tester TOUS les livres (12 livres)
./test_enrichment.sh

# Tester UN livre spécifique (ID = 2)
./test_enrichment.sh 8080 2

# Si le serveur tourne sur un autre port (ex: 8081)
./test_enrichment.sh 8081
```

### Option 2: Commandes curl manuelles

#### Scanner les livres dans un dossier
```bash
curl -X POST "http://localhost:8080/api/scanner/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/home/guillaume/work/Gaston/bd_sample",
    "recursive": true
  }'
```

#### Enrichir UN livre spécifique
```bash
# Livre #2 (Y le dernier homme - 02)
curl -s -X POST "http://localhost:8080/api/metadata/match/2" | python3 -m json.tool
```

#### Enrichir TOUS les livres (boucle)
```bash
# Obtenir tous les IDs de livres
book_ids=$(sqlite3 gaston.db "SELECT id FROM books ORDER BY id")

# Tester chaque livre
for book_id in $book_ids; do
    echo "=== Livre #$book_id ==="
    curl -s -X POST "http://localhost:8080/api/metadata/match/$book_id" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['status'] == 'success' and data.get('metadata'):
    m = data['metadata']
    print(f\"✓ {m['series_name']} #{m['volume_number']}\")
    print(f\"  Confiance: {m['confidence_score']}\")
    print(f\"  Status: {data['validation_status']}\")
else:
    print('❌ Échec')
"
    echo
done
```

#### Valider automatiquement un livre
```bash
# Si le livre a un score >= 0.90, le valider automatiquement
curl -X POST "http://localhost:8080/api/metadata/validate/2" \
  -H "Content-Type: application/json" \
  -d '{"book_id": 2, "accept": true}'
```

---

## 🔍 Commandes utiles

### Vérifier l'état de l'API
```bash
curl http://localhost:8080/api/health
```

### Lister tous les livres dans la DB
```bash
sqlite3 gaston.db "SELECT id, filename, has_metadata FROM books"
```

### Voir les métadonnées d'un livre
```bash
sqlite3 gaston.db "
SELECT
    b.id,
    b.filename,
    m.series_name,
    m.volume_number,
    m.confidence_score,
    m.source
FROM books b
LEFT JOIN metadata m ON b.id = m.book_id
WHERE b.id = 2
"
```

### Compter les livres avec/sans métadonnées
```bash
sqlite3 gaston.db "
SELECT
    CASE WHEN has_metadata THEN 'Avec métadonnées' ELSE 'Sans métadonnées' END,
    COUNT(*)
FROM books
GROUP BY has_metadata
"
```

---

## 🐛 Dépannage

### Le serveur ne démarre pas
```bash
# Vérifier que le port 8080 est libre
lsof -i :8080

# Tuer le processus si nécessaire
kill -9 $(lsof -t -i :8080)
```

### Erreur "Module not found"
```bash
# Réinstaller les dépendances
source venv/bin/activate
pip install -r requirements.txt
```

### Réinitialiser la base de données
```bash
rm gaston.db
python -c "from backend.database.session import init_db; init_db()"
```

---

## 📊 Tests effectués

Les livres suivants ont été testés avec succès :

- ✅ Astérix T41 → Score 1.00 (auto-validé)
- ✅ Teleportation Inc. T2 → Score 0.99 (auto-validé)
- ✅ Y le dernier homme #1, #2, #3 → Score 1.00 (auto-validé) ← **FIX RÉCENT**

Le fix du calcul de confiance (normalisation de la ponctuation) permet maintenant de valider automatiquement les comics avec ponctuation dans le titre.
