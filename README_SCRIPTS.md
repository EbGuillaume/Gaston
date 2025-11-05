# Scripts Gaston - Guide d'utilisation

Ce document explique comment utiliser les scripts de gestion de la base de données.

## 🚀 Démarrage rapide

Pour réinitialiser et scanner toute votre bibliothèque en une seule commande:

```bash
./fresh_start.sh
```

Ce script va:
1. Réinitialiser la base de données
2. Démarrer le serveur si nécessaire
3. Scanner tous les livres du dossier `bd_sample`
4. Enrichir automatiquement les métadonnées

## 📜 Scripts disponibles

### 1. `start_gaston.sh` - Démarrer le serveur

Démarre le serveur Gaston en mode développement.

```bash
./start_gaston.sh
```

Le serveur sera accessible sur `http://localhost:8080`

### 2. `reset_database.sh` - Réinitialiser la base

Supprime toutes les données de la base de données (avec confirmation interactive).

```bash
./reset_database.sh
```

**⚠️ Attention**: Cette opération:
- Supprime tous les livres, métadonnées, séries
- Crée un backup automatique: `gaston.db.backup.YYYYMMDD_HHMMSS`
- Vide tous les caches

### 3. `scan_all.sh` - Scanner les livres

Scanne un dossier et ajoute tous les livres à la base de données.

```bash
./scan_all.sh [PORT] [DOSSIER]
```

**Paramètres**:
- `PORT` (optionnel, défaut: 8080): Port du serveur
- `DOSSIER` (optionnel, défaut: bd_sample): Dossier à scanner

**Exemples**:
```bash
./scan_all.sh                      # Scanne bd_sample sur port 8080
./scan_all.sh 8080 /path/to/bds    # Scanne un autre dossier
```

**Résultat**:
- Fichiers trouvés par extension (.cbz, .cbr, .pdf, .epub)
- Taille totale
- Liste complète des livres scannés

### 4. `enrich_all.sh` - Enrichir les métadonnées

Enrichit automatiquement les métadonnées de tous les livres de la base.

```bash
./enrich_all.sh [PORT]
```

**Paramètres**:
- `PORT` (optionnel, défaut: 8080): Port du serveur

**Résultat**:
- ✅ Auto-validés: Métadonnées trouvées avec confiance ≥ 0.90
- ⚠️ Validation manuelle: Confiance < 0.90
- ❌ Aucune correspondance: Pas de résultats trouvés

### 5. `fresh_start.sh` - Recommencer à zéro

Script tout-en-un qui combine reset + scan + enrich.

```bash
./fresh_start.sh
```

**Ce script va**:
1. Demander confirmation
2. Réinitialiser la DB
3. Démarrer le serveur (si nécessaire)
4. Scanner tous les livres
5. Enrichir les métadonnées

## 🔧 Scripts utilitaires

### `clear_all_cache.sh` - Nettoyer les caches

Vide tous les caches (DB, scraper, Python, API).

```bash
./clear_all_cache.sh
```

### `test_all_6_books.sh` - Tester l'enrichissement

Teste l'enrichissement sur les 6 premiers livres (pour debug).

```bash
./test_all_6_books.sh
```

## 📊 Vérifier l'état de la base

### Compter les livres

```bash
sqlite3 gaston.db "SELECT COUNT(*) FROM books"
```

### Voir les livres avec métadonnées

```bash
sqlite3 gaston.db "
SELECT b.id, b.filename, m.volume_number, m.title
FROM books b
LEFT JOIN metadata m ON b.id = m.book_id
ORDER BY b.id
"
```

### Statistiques

```bash
sqlite3 gaston.db "
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN has_metadata = 1 THEN 1 ELSE 0 END) as with_metadata,
    SUM(CASE WHEN has_metadata = 0 THEN 1 ELSE 0 END) as without_metadata
FROM books
"
```

## 🐛 Dépannage

### Le serveur ne démarre pas

```bash
# Vérifier si un processus écoute sur le port 8080
lsof -i :8080

# Tuer le processus si nécessaire
kill <PID>

# Redémarrer
./start_gaston.sh
```

### Erreur "API not accessible"

```bash
# Vérifier que le serveur tourne
curl http://localhost:8080/health

# Si le serveur ne répond pas, le démarrer
./start_gaston.sh
```

### Les métadonnées ne s'enrichissent pas

```bash
# Vider le cache
./clear_all_cache.sh

# Relancer l'enrichissement
./enrich_all.sh
```

### Duplicatas dans la base

```bash
# Réinitialiser complètement
./reset_database.sh

# Rescanner
./scan_all.sh
```

## 📂 Structure des fichiers

```
Gaston/
├── backend/               # Code source
├── bd_sample/            # Dossier de test avec vos BDs
├── gaston.db             # Base de données SQLite
├── config.yaml           # Configuration
├── start_gaston.sh       # Démarrer le serveur
├── reset_database.sh     # Réinitialiser la DB
├── scan_all.sh           # Scanner les livres
├── enrich_all.sh         # Enrichir les métadonnées
├── fresh_start.sh        # Tout-en-un
└── clear_all_cache.sh    # Nettoyer les caches
```

## ⚙️ Configuration

Le fichier `config.yaml` contient la configuration de Gaston:

```yaml
gaston:
  library_paths:
    - /mnt/nas/BD
    - /mnt/nas/Comics
    - /mnt/nas/Manga

  metadata:
    sources:
      - name: bdphile
        enabled: true
        priority: 1

    auto_validate_threshold: 0.90
```

Pour scanner vos vraies bibliothèques, modifiez `library_paths` dans le config.

## 📈 Workflow recommandé

### Premier lancement

```bash
# 1. Configurer
cp config.example.yaml config.yaml
nano config.yaml  # Ajuster les chemins

# 2. Démarrage complet
./fresh_start.sh
```

### Ajout de nouveaux livres

```bash
# 1. Scanner uniquement les nouveaux
./scan_all.sh 8080 /path/to/new/books

# 2. Enrichir
./enrich_all.sh
```

### Nettoyage / Reset

```bash
# Reset complet
./reset_database.sh

# Rescanner
./scan_all.sh
```

## 🎯 Résultats attendus

Avec le dossier `bd_sample` par défaut (8 livres):

```
📊 Scan:
   • Fichiers trouvés: 8
   • Extensions: .cbz (3), .cbr (3), .pdf (2)
   • Taille: ~584 MB

📊 Enrichissement:
   • Auto-validés: 8/8
   • Toutes les séries trouvées avec confiance 1.00
```

## 🔄 Sources de métadonnées

Actuellement actif:
- **BDPhile**: 43k séries (BD, Comics, Manga)
- Recherche directe, pas de blocage

À venir:
- Bedetheque (nécessite contournement anti-scraping)
- ComicVine (nécessite clé API)

## 📝 Notes

- Le cache est actuellement désactivé pour debug
- Les métadonnées sont auto-validées si confiance ≥ 0.90
- Les PDFs sont supportés mais peuvent avoir moins de métadonnées
