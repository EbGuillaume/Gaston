# 📋 Cahier des Charges - Gaston v1.0

> *"From chaos to order - Your smart digital library organizer"*

**Date :** 4 novembre 2025  
**Version :** 1.0  
**Statut :** Validé

---

## 🎯 Vision du projet

**Gaston** est un outil d'organisation automatique de bibliothèques numériques (BD/Comics/Manga/Livres) avec interface web, optimisé pour Komga dans un premier temps.

### Objectifs principaux

1. **Scanner** et analyser des bibliothèques numériques
2. **Détecter et gérer** les doublons intelligemment
3. **Renommer et organiser** selon les standards Komga
4. **Enrichir** avec des métadonnées automatiques (scraping)
5. **Fournir** une interface web intuitive pour contrôler le tout

---

## 🏗️ Stack Technique

### Backend
- **Langage :** Python 3.10+
- **Framework API :** FastAPI
- **Base de données :** SQLite
- **Scraping :** httpx + BeautifulSoup4
- **OCR :** EasyOCR
- **Image matching :** API externe (imagehash en local pour cache)

### Frontend
- **Framework :** Vue.js 3
- **Build :** Vite
- **UI Library :** À définir (Vuetify, Element Plus, ou custom)
- **WebSocket :** Pour progression temps réel

### Déploiement
- **Environnements cibles :**
  - Exécution locale (Windows/Linux)
  - Conteneur LXC (Ubuntu/Debian)
- **Serveur web :** Uvicorn
- **Port par défaut :** 8080

### Langues & Interface
- **Langue V1 :** Français uniquement (préparation pour EN)
- **Interface :** Desktop/Server (pas de mobile-friendly pour V1)
- **Thème :** Clair par défaut (sombre en Phase 2)
- **Authentification :** Aucune pour V1
- **Multi-utilisateurs :** Non pour V1

---

## 📦 Formats Supportés

### Priorités égales
- `.cbz` (Comic Book ZIP)
- `.cbr` (Comic Book RAR)
- `.epub` (eBook)
- `.pdf` (Portable Document Format)

### Gestion des doublons
Ordre de préférence : **CBZ > CBR > EPUB > PDF**

### Limites
- **Taille maximale par fichier :** 1 GB
- **Limite RAM :** Configurable dans paramètres (auto-détection intelligente)
- **PDF multi-albums :** Non géré en V1
- **Conversions de format :** Aucune (fichiers conservés dans leur format d'origine)

### Fichiers problématiques
- **Corrompus :** Déplacés dans `/corrupted/`
- **Inclassables :** Déplacés dans `/_uncategorized/`

---

## 🎯 Pipeline de Matching Métadonnées

### Ordre de priorité

```
1. Matching par NOM de fichier
   ├─ Extraction : série, numéro, titre, année
   ├─ Fuzzy matching avec bases de données
   └─ Seuil confiance : 90%
   
   ↓ (si échec ou confiance < 90%)
   
2. OCR sur COUVERTURE
   ├─ Extraction texte avec EasyOCR
   ├─ Parsing : titre, auteur, éditeur, numéro
   └─ Recherche avec texte extrait
   
   ↓ (si échec)
   
3. Matching par IMAGE (couverture)
   ├─ Extraction couverture depuis archive
   ├─ API externe pour matching
   └─ Comparaison avec résultats de recherche
```

### Auto-validation
- **Confiance ≥ 90% :** Validation automatique sans intervention
- **Confiance < 90% :** Sélection du meilleur résultat, mais user peut consulter les autres options via l'interface
- **Multiples résultats similaires :** Choix automatique du score le plus élevé

### Sources de métadonnées

**Priorité 1 : Bedetheque.com**
- BD franco-belges
- Comics français
- Mangas français

**Priorité 2 : ComicVine**
- Comics US
- Si non trouvé dans Bedetheque

**Stratégie :** Si recherche échoue dans source primaire, essayer source secondaire

### Rate Limiting
- **Bedetheque :** Max 1 requête/seconde
- **ComicVine :** Selon limites API
- **Cache :** Indéfini par défaut (configurable via interface)

---

## 🗂️ Organisation des Fichiers

### Structure basée sur Komga

**Principe de base :** 1 dossier = 1 série | 1 fichier = 1 tome

### Pattern de nommage standard

```
[Nom Série]/[Nom Série] [Numéro] - [Titre].ext
```

**Exemples :**
```
Astérix/
├── Astérix 01 - Le Gaulois.cbz
├── Astérix 02 - La Serpe d'Or.cbz
└── Astérix 03 - Astérix et les Goths.cbz

Spider-Man/
├── Spider-Man 001.cbz
├── Spider-Man 002.cbz
└── Spider-Man 003.cbz
```

### Organisation hiérarchique

**Pas de sous-dossiers par éditeur**
```
✓ Comics/Spider-Man/
✗ Comics/Marvel/Spider-Man/
```

### Cas spéciaux

#### One-shots
```
_oneshots/
├── Blacksad - Quelque part entre les ombres.cbz
├── Maus.cbz
└── Persepolis.cbz
```

#### Intégrales & Omnibus
```
Astérix Intégrale/
├── Astérix - Intégrale 01.cbz
├── Astérix - Intégrale 02.cbz
└── Astérix - Intégrale 03.cbz
```

**Règle :** Toujours dans un dossier séparé avec suffixe "Intégrale"

#### Livres (non-BD)
- Même structure que BD/Comics
- Komga gère aussi les livres

#### Fichiers non identifiés
```
_uncategorized/
├── fichier_inconnu_01.cbz
└── scan_bizarre.pdf
```

### Éditions multiples
**Priorité automatique :** Intégrale > Edition spéciale > Edition originale

### Multi-bibliothèques
Support de plusieurs sources si Komga le permet (ex: BD, Comics, Manga séparés)

---

## 🔍 Détection des Doublons

### Méthodes de détection

1. **Hash exact (MD5/SHA256)**
   - Fichiers 100% identiques
   - Action : Garder selon priorité format

2. **Hash perceptuel (images)**
   - Couvertures similaires
   - Seuil : À définir lors des tests

3. **Fuzzy matching (noms)**
   - Noms de fichiers similaires
   - Seuil : 85% de similarité

### Gestion des doublons

```
/duplicates/
├── 2024-11-04_scan_001/
│   ├── duplicate_001.cbz
│   ├── duplicate_002.cbz
│   └── metadata.json      # Info sur origine et raison
└── 2024-11-05_scan_002/
    └── ...
```

**Métadonnées des doublons :**
- Chemin d'origine
- Fichier conservé (lequel)
- Raison du doublon (hash, nom, image)
- Date de détection

---

## 💾 Base de Données (SQLite)

### Schéma principal

```sql
-- Séries détectées
CREATE TABLE series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('BD', 'Comic', 'Manga', 'Book', 'Oneshot', 'Integrale')),
    language TEXT DEFAULT 'fr',
    folder_path TEXT,
    komga_ready BOOLEAN DEFAULT 0,
    total_books INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fichiers/Livres
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER,
    original_path TEXT NOT NULL,
    new_path TEXT,
    filename TEXT NOT NULL,
    file_hash TEXT,
    file_size INTEGER,
    number INTEGER,
    title TEXT,
    extension TEXT,
    status TEXT CHECK(status IN ('pending', 'processing', 'renamed', 'organized', 'error')),
    has_metadata BOOLEAN DEFAULT 0,
    is_duplicate BOOLEAN DEFAULT 0,
    is_corrupted BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
);

-- Index pour performance
CREATE INDEX idx_books_hash ON books(file_hash);
CREATE INDEX idx_books_series ON books(series_id);
CREATE INDEX idx_books_status ON books(status);

-- Métadonnées enrichies
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER UNIQUE,
    source TEXT CHECK(source IN ('bedetheque', 'comicvine', 'manual', 'embedded')),
    confidence_score REAL,
    
    -- Données bibliographiques
    series_name TEXT,
    volume_number INTEGER,
    title TEXT,
    summary TEXT,
    
    -- Créateurs
    writers TEXT,        -- JSON array
    pencillers TEXT,     -- JSON array
    inkers TEXT,         -- JSON array
    colorists TEXT,      -- JSON array
    letterers TEXT,      -- JSON array
    
    -- Publication
    publisher TEXT,
    publication_date TEXT,
    isbn TEXT,
    page_count INTEGER,
    
    -- Classification
    genres TEXT,         -- JSON array
    tags TEXT,          -- JSON array
    age_rating TEXT,
    
    -- Médias
    cover_url TEXT,
    cover_local_path TEXT,
    
    -- Données brutes
    raw_data JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
);

-- Doublons détectés
CREATE TABLE duplicates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id_1 INTEGER,
    book_id_2 INTEGER,
    similarity_score REAL,
    duplicate_type TEXT CHECK(duplicate_type IN ('hash_exact', 'hash_perceptual', 'name_fuzzy')),
    resolved BOOLEAN DEFAULT 0,
    kept_book_id INTEGER,
    action TEXT CHECK(action IN ('keep_both', 'keep_first', 'keep_second', 'pending')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (book_id_1) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (book_id_2) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (kept_book_id) REFERENCES books(id) ON DELETE SET NULL
);

-- Tâches/Jobs asynchrones
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT CHECK(task_type IN ('scan', 'rename', 'organize', 'scrape', 'dedupe', 'ocr')),
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    current_item TEXT,
    log_messages JSON,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configuration globale
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    value_type TEXT CHECK(value_type IN ('string', 'integer', 'boolean', 'json')),
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historique des opérations (pour futur rollback)
CREATE TABLE operations_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT CHECK(operation_type IN ('rename', 'move', 'delete', 'metadata_update')),
    book_id INTEGER,
    before_state JSON,
    after_state JSON,
    reversible BOOLEAN DEFAULT 1,
    rolled_back BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE SET NULL
);
```

---

## 🔧 Configuration (config.yaml)

```yaml
# Gaston Configuration v1.0

gaston:
  version: "1.0"
  
  # Chemins des bibliothèques sources
  library_paths:
    - /mnt/nas/BD
    - /mnt/nas/Comics
    - /mnt/nas/Manga
  
  # Dossier de sortie organisé
  output_path: /mnt/nas/Organized
  
  # Dossiers spéciaux
  special_folders:
    duplicates: /mnt/nas/duplicates
    corrupted: /mnt/nas/corrupted
    uncategorized: /mnt/nas/_uncategorized
  
  # Organisation
  organization:
    target_format: komga
    naming_pattern: "{series}/{series} {number:03d} - {title}"
    create_oneshots_folder: true
    create_integrales_folder: true
    separate_by_publisher: false
  
  # Métadonnées
  metadata:
    sources:
      - name: bedetheque
        enabled: true
        priority: 1
      - name: comicvine
        enabled: true
        priority: 2
    
    auto_fetch: true
    auto_validate_threshold: 0.90
    cache_duration: null  # null = indéfini
    store_covers_locally: true
    covers_path: /mnt/nas/.gaston/covers
  
  # Matching pipeline
  matching:
    order:
      - name
      - ocr
      - image
    
    confidence_thresholds:
      name: 0.85
      ocr: 0.80
      image: 0.75
    
    ocr:
      engine: easyocr
      languages: ['fr', 'en']
      preprocess: true
    
    image:
      use_api: true
      api_endpoint: null  # À définir
  
  # Déduplication
  deduplication:
    enabled: true
    methods:
      - hash_exact
      - name_fuzzy
      - image_perceptual
    
    format_priority:
      - cbz
      - cbr
      - epub
      - pdf
    
    similarity_threshold: 0.85
    auto_move_duplicates: true
  
  # Scanning
  scanning:
    max_file_size: 1073741824  # 1 GB en bytes
    scan_on_startup: false
    scheduled_scan:
      enabled: true
      frequency: daily
      time: "03:00"
    
    file_extensions:
      - .cbz
      - .cbr
      - .epub
      - .pdf
    
    ignore_hidden: true
    detect_corrupted: true
  
  # Performance
  performance:
    max_workers: null  # null = auto-detection CPU
    max_memory_mb: null  # null = auto-detection
    enable_cache: true
    cache_path: /mnt/nas/.gaston/cache
  
  # API & Web
  web:
    host: 0.0.0.0
    port: 8080
    enable_cors: false
    log_level: DEBUG
  
  # Rate limiting
  rate_limiting:
    bedetheque:
      requests_per_second: 1
      burst: 3
    comicvine:
      requests_per_minute: 60
  
  # Interface
  interface:
    language: fr
    theme: light
    items_per_page: 50
    enable_keyboard_shortcuts: true
```

---

## 🎨 Interface Web - Wireframes

### Architecture des pages

```
┌─────────────────────────────────────────────────┐
│  [LOGO] Gaston           [Notifications] [⚙️]   │
├─────────────────────────────────────────────────┤
│ [Tableau de bord] [Bibliothèque] [Doublons]    │
│ [Métadonnées] [Tâches] [Paramètres]            │
├──────────────┬──────────────────────────────────┤
│              │                                  │
│  SIDEBAR     │      CONTENU PRINCIPAL          │
│              │                                  │
│  📊 Stats    │                                  │
│  📁 Sources  │                                  │
│  🔄 Tâches   │                                  │
│  ⚙️ Config   │                                  │
│              │                                  │
└──────────────┴──────────────────────────────────┘
```

### Pages principales

#### 1. Tableau de bord (Dashboard)
**Contenu :**
- Statistiques globales
  - Nombre total de fichiers
  - Nombre de séries
  - Doublons détectés
  - Fichiers sans métadonnées
  - Espace disque utilisé
- Graphiques
  - Répartition par type (BD/Comic/Manga)
  - Répartition par format (CBZ/CBR/PDF/EPUB)
  - État de la bibliothèque (organisé/non-organisé)
- Dernières activités
- Raccourcis actions rapides

#### 2. Scanner
**Fonctionnalités :**
- Sélection dossier source (file picker)
- Bouton "Lancer le scan"
- Barre de progression en temps réel (WebSocket)
- Résultats :
  - Fichiers trouvés
  - Doublons détectés
  - Fichiers corrompus
  - Problèmes rencontrés
- Actions :
  - Voir les détails
  - Passer à l'organisation
  - Exporter rapport

#### 3. Bibliothèque
**Fonctionnalités :**
- Vue en grille ou liste
- Affichage des séries détectées
- Clic sur série → liste des tomes
- Filtres :
  - Type (BD/Comic/Manga/Livre)
  - Statut (Organisé/En attente/Erreur)
  - Langue
  - Avec/sans métadonnées
- Recherche globale
- Tri :
  - Date d'ajout (défaut)
  - Nom alphabétique
  - Nombre de tomes
  - Score de confiance
- Actions par série :
  - Éditer métadonnées
  - Réorganiser
  - Supprimer
  - Voir dans explorateur

#### 4. Doublons
**Fonctionnalités :**
- Liste des doublons détectés
- Vue comparaison côte à côte :
  - Couvertures
  - Métadonnées (taille, résolution, format)
  - Chemins
  - Score de similarité
- Actions :
  - Garder fichier A
  - Garder fichier B
  - Garder les deux
  - Prévisualiser avant décision
- Filtres :
  - Type de doublon (hash/nom/image)
  - Statut (résolu/en attente)
- Actions groupées

#### 5. Métadonnées
**Fonctionnalités :**
- Liste des fichiers/séries
- Indicateurs :
  - ✅ Métadonnées complètes
  - ⚠️ Métadonnées partielles
  - ❌ Aucune métadonnée
  - 🔄 En cours de scraping
- Détail par fichier :
  - Couverture actuelle
  - Métadonnées actuelles
  - Source (Bedetheque/ComicVine/Manuel)
  - Score de confiance
- Actions :
  - Rechercher automatiquement
  - Rechercher manuellement
  - Éditer manuellement
  - Choix parmi résultats multiples
- Actions groupées :
  - Scraper toute la bibliothèque
  - Scraper sélection

**Interface de matching :**
```
┌────────────────────────────────────────────┐
│  Fichier: Asterix 01.cbz                   │
│  ┌──────────┐                              │
│  │          │  Série détectée: Astérix     │
│  │ COVER    │  Numéro: 1                   │
│  │          │  Confiance: 95%              │
│  └──────────┘                              │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ Résultats Bedetheque (3 trouvés)     │ │
│  ├───────────────────────────────────────┤ │
│  │ ● Astérix - Tome 1 - Le Gaulois      │ │
│  │   Score: 98% | 1961 | Goscinny       │ │
│  │   [Détails] [Aperçu]                  │ │
│  ├───────────────────────────────────────┤ │
│  │ ○ Astérix - Intégrale 1              │ │
│  │   Score: 87% | 2005                   │ │
│  ├───────────────────────────────────────┤ │
│  │ ○ Astérix - Edition spéciale         │ │
│  │   Score: 75%                          │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  [✓ Valider] [Recherche manuelle] [Ignorer]│
└────────────────────────────────────────────┘
```

#### 6. Tâches (Jobs)
**Fonctionnalités :**
- Liste des tâches actives et historique
- Détail par tâche :
  - Type (scan/rename/organize/scrape)
  - Statut (en attente/en cours/terminé/erreur)
  - Progression (barre + pourcentage)
  - Fichier en cours
  - Temps écoulé / estimé
  - Logs détaillés
- Actions :
  - Annuler tâche
  - Voir logs complets
  - Réessayer si erreur
- Filtres par type et statut

#### 7. Paramètres
**Sections :**

**Général**
- Chemins des bibliothèques (ajout/suppression)
- Dossier de sortie
- Langue interface
- Thème (clair/sombre)

**Organisation**
- Pattern de nommage (éditable)
- Options Komga
- Gestion des one-shots
- Gestion des intégrales

**Métadonnées**
- Sources activées (Bedetheque/ComicVine)
- Seuil de confiance auto-validation
- Durée du cache
- Stockage local des couvertures

**Déduplication**
- Méthodes activées
- Seuil de similarité
- Priorité des formats
- Auto-déplacement

**Scanning**
- Taille max fichiers
- Scan planifié (activer/désactiver)
- Fréquence et heure
- Extensions à scanner

**Performance**
- Nombre de workers
- Limite mémoire
- Niveau de logs

**Avancé**
- Rate limiting API
- Chemins du cache
- Réinitialisation base de données
- Import/Export configuration

---

## 🚀 Workflow Utilisateur

### Scénario type : Premier scan

```
1. User ouvre http://localhost:8080

2. Page "Scanner"
   ├─ Sélectionne /mnt/nas/downloads/BD
   ├─ Clique "Lancer le scan"
   └─ Gaston scanne en arrière-plan

3. Pendant le scan (temps réel)
   ├─ Barre de progression
   ├─ Fichiers trouvés : 150
   ├─ Détection des types
   └─ Calcul des hash

4. Résultats du scan
   ├─ 120 BD détectées
   ├─ 20 Comics détectés
   ├─ 5 fichiers corrompus → /corrupted
   ├─ 5 fichiers inclassables → /_uncategorized
   └─ 8 doublons détectés

5. Page "Doublons"
   ├─ User review les 8 doublons
   ├─ Choix automatique du meilleur format (CBZ > CBR)
   └─ Validation → doublons vers /duplicates

6. Matching automatique (arrière-plan)
   ├─ Matching par nom : 100/140 (confiance > 90%)
   ├─ OCR : 25/40 restants
   ├─ Image matching : 10/15 restants
   └─ 5 fichiers nécessitent validation manuelle

7. Page "Métadonnées"
   ├─ 135/140 fichiers avec métadonnées auto
   ├─ 5 fichiers en attente
   ├─ User clique sur fichier en attente
   ├─ Interface propose 3 résultats
   ├─ User sélectionne le bon
   └─ Validation

8. Organisation automatique
   ├─ Application des renommages
   ├─ Création de l'arborescence
   ├─ Injection des métadonnées (ComicInfo.xml)
   ├─ Déplacement vers /Organized
   └─ Mise à jour base de données

9. Confirmation
   ├─ Rapport final affiché
   ├─ 140 fichiers organisés
   ├─ Structure Komga prête
   └─ User peut scanner dans Komga
```

### Mode d'exécution

**Par défaut :** Application directe
- Pas de dry-run obligatoire
- Modifications appliquées immédiatement
- Historique conservé en base pour futur rollback (Phase 2)

**Validation :**
- Automatique si confiance ≥ 90%
- Traitement continu (pas de batch manuel)

---

## 📊 Tâches Asynchrones

### Types de tâches

1. **Scan** - Scanner un dossier
2. **Dedupe** - Détection des doublons
3. **Scrape** - Récupération métadonnées
4. **OCR** - Analyse OCR sur couvertures
5. **Organize** - Renommage et organisation
6. **Cleanup** - Nettoyage fichiers temporaires

### Gestion
- Exécution en arrière-plan (asyncio/celery)
- WebSocket pour mise à jour temps réel UI
- Logs détaillés par tâche
- Annulation possible
- Retry automatique en cas d'erreur réseau

---

## 📦 Dépendances Python

```txt
# API & Web
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
python-multipart==0.0.6

# Base de données
sqlalchemy==2.0.23
alembic==1.12.1

# Archives
rarfile==4.1
py7zr==0.20.8
zipfile-deflate64==0.2.0

# Images
Pillow==10.1.0
imagehash==4.3.1
opencv-python==4.8.1.78

# OCR
easyocr==1.7.1

# Matching
rapidfuzz==3.5.2
python-Levenshtein==0.23.0

# Scraping
httpx==0.25.2
beautifulsoup4==4.12.2
lxml==4.9.3
playwright==1.40.0  # Pour JS-heavy sites si nécessaire

# Métadonnées
xmltodict==0.13.0
ebooklib==0.18

# Utils
pydantic==2.5.2
pyyaml==6.0.1
python-dotenv==1.0.0
rich==13.7.0
click==8.1.7

# Async & Workers
asyncio
aiofiles==23.2.1

# Monitoring
psutil==5.9.6  # Pour auto-détection CPU/RAM

# Logs
loguru==0.7.2
```

### Dépendances système (auto-install)

**Ubuntu/Debian :**
```bash
sudo apt-get update
sudo apt-get install -y \
    unrar \
    p7zip-full \
    python3-dev \
    libgl1-mesa-glx \
    libglib2.0-0
```

---

## 🏗️ Architecture du Code

```
gaston/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app
│   │   ├── dependencies.py          # Dependency injection
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py         # GET /api/dashboard
│   │   │   ├── library.py           # /api/library/*
│   │   │   ├── scanner.py           # /api/scan/*
│   │   │   ├── duplicates.py        # /api/duplicates/*
│   │   │   ├── metadata.py          # /api/metadata/*
│   │   │   ├── tasks.py             # /api/tasks/*
│   │   │   └── config.py            # /api/config/*
│   │   └── websocket.py             # WebSocket endpoints
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── scanner.py               # Scan filesystem
│   │   ├── deduplicator.py          # Duplicate detection
│   │   ├── organizer.py             # File organization (Komga)
│   │   ├── renamer.py               # Intelligent renaming
│   │   └── metadata_manager.py      # Metadata orchestration
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py                  # Abstract base class
│   │   ├── bedetheque.py            # Bedetheque scraper
│   │   ├── comicvine.py             # ComicVine scraper
│   │   └── cache.py                 # Scraping cache management
│   │
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── pipeline.py              # Matching pipeline orchestrator
│   │   ├── name_matcher.py          # Fuzzy name matching
│   │   ├── ocr_matcher.py           # OCR + matching
│   │   └── image_matcher.py         # Image matching via API
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── archive.py               # CBZ/CBR/EPUB manipulation
│   │   ├── image.py                 # Image processing
│   │   ├── ocr.py                   # EasyOCR wrapper
│   │   ├── fuzzy.py                 # Fuzzy string matching
│   │   ├── patterns.py              # Regex patterns extraction
│   │   ├── hash.py                  # File hashing utilities
│   │   └── filesystem.py            # FS operations
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                # SQLAlchemy models
│   │   ├── crud.py                  # CRUD operations
│   │   ├── session.py               # DB session management
│   │   └── migrations/              # Alembic migrations
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── worker.py                # Async task worker
│   │   ├── scan_task.py
│   │   ├── scrape_task.py
│   │   ├── organize_task.py
│   │   └── dedupe_task.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── book.py                  # Pydantic schemas
│   │   ├── series.py
│   │   ├── metadata.py
│   │   ├── task.py
│   │   └── config.py
│   │
│   └── config.py                    # Configuration loader
│
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   │
│   ├── src/
│   │   ├── assets/
│   │   │   ├── logo.png
│   │   │   └── styles/
│   │   │       └── main.css
│   │   │
│   │   ├── components/
│   │   │   ├── Dashboard.vue
│   │   │   ├── Scanner.vue
│   │   │   ├── Library.vue
│   │   │   ├── BookCard.vue
│   │   │   ├── SeriesCard.vue
│   │   │   ├── Duplicates.vue
│   │   │   ├── DuplicateComparison.vue
│   │   │   ├── Metadata.vue
│   │   │   ├── MetadataEditor.vue
│   │   │   ├── MatchingResults.vue
│   │   │   ├── Tasks.vue
│   │   │   ├── TaskItem.vue
│   │   │   ├── Settings.vue
│   │   │   └── ProgressBar.vue
│   │   │
│   │   ├── views/
│   │   │   ├── DashboardView.vue
│   │   │   ├── ScannerView.vue
│   │   │   ├── LibraryView.vue
│   │   │   ├── DuplicatesView.vue
│   │   │   ├── MetadataView.vue
│   │   │   ├── TasksView.vue
│   │   │   └── SettingsView.vue
│   │   │
│   │   ├── router/
│   │   │   └── index.js
│   │   │
│   │   ├── store/
│   │   │   ├── index.js
│   │   │   ├── modules/
│   │   │   │   ├── library.js
│   │   │   │   ├── scanner.js
│   │   │   │   ├── duplicates.js
│   │   │   │   ├── metadata.js
│   │   │   │   ├── tasks.js
│   │   │   │   └── config.js
│   │   │
│   │   ├── services/
│   │   │   ├── api.js              # API client
│   │   │   └── websocket.js        # WebSocket client
│   │   │
│   │   ├── App.vue
│   │   └── main.js
│   │
│   ├── package.json
│   ├── vite.config.js
│   └── .env.development
│
├── scripts/
│   ├── install.py                   # Installation script
│   ├── setup_lxc.py                 # LXC setup
│   └── dev.py                       # Development runner
│
├── tests/
│   ├── unit/
│   │   ├── test_scanner.py
│   │   ├── test_deduplicator.py
│   │   ├── test_renamer.py
│   │   ├── test_scrapers.py
│   │   └── test_matching.py
│   │
│   ├── integration/
│   │   ├── test_api.py
│   │   └── test_workflow.py
│   │
│   └── fixtures/
│       └── sample_files/
│
├── docs/
│   ├── installation.md
│   ├── configuration.md
│   ├── api.md
│   └── development.md
│
├── .github/
│   └── workflows/
│       ├── tests.yml
│       └── release.yml
│
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── setup.py
├── README.md
├── LICENSE
├── .gitignore
└── docker-compose.yml             # Bonus
```

---

## 🚀 Installation & Déploiement

### Prérequis
- Python 3.10+
- Node.js 18+ (pour le frontend)
- Git
- Ubuntu/Debian (pour LXC)

### Installation locale

```bash
# Clone du repository
git clone https://github.com/yourusername/gaston.git
cd gaston

# Installation du backend
pip install -e .

# Installation des dépendances système (auto)
python scripts/install.py

# Installation du frontend
cd frontend
npm install
npm run build
cd ..

# Initialisation de la base de données
gaston init

# Lancement
gaston start
# Ou mode dev avec hot-reload
gaston dev
```

### Installation LXC (Ubuntu/Debian)

```bash
# Sur l'hôte Proxmox
pct create 100 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname gaston \
  --memory 4096 \
  --cores 4 \
  --storage local-lvm \
  --rootfs local-lvm:32

# Démarrage du conteneur
pct start 100

# Connection
pct enter 100

# Dans le conteneur
apt update && apt install -y git python3-pip

# Clone et installation
git clone https://github.com/yourusername/gaston.git
cd gaston
python3 scripts/setup_lxc.py

# Service systemd auto-créé
systemctl status gaston
```

### Mise à jour

```bash
# Dans le dossier gaston
git pull origin main
pip install -e . --upgrade

# Si changements DB
gaston migrate

# Redémarrage
gaston restart
```

---

## 🎯 Roadmap de développement

### Phase 1 : MVP (Semaines 1-6)

**Semaine 1 : Setup & Core Backend**
- [x] Setup projet (structure, Git, pre-commit)
- [ ] Configuration FastAPI + SQLAlchemy
- [ ] Modèles de base de données
- [ ] Scanner de fichiers basique
- [ ] Extraction archives (CBZ/CBR)
- [ ] Tests unitaires core

**Semaine 2 : Déduplication & Hashing**
- [ ] Calcul hash MD5/SHA256
- [ ] Détection doublons par hash exact
- [ ] Fuzzy matching des noms
- [ ] Gestion dossier /duplicates
- [ ] API REST endpoints doublons

**Semaine 3 : Scraping & Matching (Nom)**
- [ ] Scraper Bedetheque (BeautifulSoup)
- [ ] Parsing métadonnées BD
- [ ] Matching par nom (rapidfuzz)
- [ ] Cache des résultats
- [ ] Rate limiting
- [ ] Tests scrapers

**Semaine 4 : OCR & Image Matching**
- [ ] Intégration EasyOCR
- [ ] Extraction couvertures depuis archives
- [ ] Prétraitement images (OpenCV)
- [ ] OCR + parsing texte
- [ ] API externe image matching
- [ ] Pipeline de matching complet

**Semaine 5 : Organisation & Renommage**
- [ ] Logique de renommage Komga
- [ ] Création arborescence dossiers
- [ ] Injection ComicInfo.xml
- [ ] Gestion one-shots
- [ ] Gestion intégrales
- [ ] Déplacement fichiers
- [ ] Tests organisation

**Semaine 6 : Interface Web MVP**
- [ ] Setup Vue.js + Vite
- [ ] Router + Store
- [ ] Dashboard (stats basiques)
- [ ] Page Scanner
- [ ] Page Bibliothèque (liste simple)
- [ ] Page Doublons (comparaison)
- [ ] Page Métadonnées (liste + édition)
- [ ] WebSocket progression
- [ ] Design responsive basique

### Phase 2 : Polish & Optimisations (Semaines 7-8)

**Semaine 7 : Tests & Stabilité**
- [ ] Tests d'intégration complets
- [ ] Tests de charge (1000+ fichiers)
- [ ] Correction bugs
- [ ] Optimisation performances
- [ ] Logs structurés
- [ ] Monitoring erreurs

**Semaine 8 : UX & Documentation**
- [ ] Amélioration UI/UX
- [ ] Raccourcis clavier
- [ ] Messages d'erreur clairs
- [ ] Documentation complète
- [ ] Vidéo démo
- [ ] README détaillé

### Phase 3 : Features Avancées (Post-MVP)

**À prioriser après retours utilisateurs :**
- [ ] Système de rollback complet
- [ ] Multi-bibliothèques avancé
- [ ] Scraper ComicVine complet
- [ ] Support Kavita
- [ ] Support Calibre
- [ ] Thème sombre
- [ ] Interface EN
- [ ] Patterns custom
- [ ] Plugins system
- [ ] Mode watch (surveillance dossier)
- [ ] Import/Export configuration
- [ ] API REST complète
- [ ] Docker image
- [ ] Application desktop (Electron)

---

## ✅ Critères de succès

### Performance
- Scan : < 1 seconde par fichier
- Matching : > 85% de précision
- Déduplication : > 95% de détection
- Interface : < 200ms temps de réponse

### Qualité
- Couverture tests : > 80%
- Zéro perte de données
- Logs détaillés pour debug
- Gestion erreurs robuste

### Expérience utilisateur
- Installation < 5 minutes
- Interface intuitive (pas de formation nécessaire)
- Résultats compréhensibles
- Feedback temps réel

---

## 🐛 Gestion des Erreurs

### Stratégie globale
- Logs structurés (Loguru)
- Try/catch exhaustifs
- Messages d'erreur clairs en français
- Retry automatique (réseau)
- Fallback gracieux

### Cas d'erreurs typiques

**Fichier corrompu**
→ Déplacer dans /corrupted + log détaillé

**Timeout scraping**
→ Retry 3x avec backoff + cache résultat partiel

**Disque plein**
→ Arrêt propre + alerte user + nettoyage possible

**Fichier verrouillé (en cours d'utilisation)**
→ Skip temporairement + retry ultérieur

**API rate limit dépassé**
→ Pause automatique + queue des requêtes

---

## 📝 Notes de développement

### Conventions de code
- **Python :** PEP 8 (Black formatter)
- **JavaScript :** ESLint + Prettier
- **Commits :** Conventional Commits
- **Branches :** GitFlow (main, develop, feature/*, hotfix/*)

### Tests
- **Framework :** pytest (backend) + Vitest (frontend)
- **Coverage :** pytest-cov
- **CI/CD :** GitHub Actions

### Documentation
- **Code :** Docstrings (Google style)
- **API :** OpenAPI (auto-générée par FastAPI)
- **User :** Markdown dans /docs

---

## 🔒 Sécurité

### V1 (Pas d'auth)
- Écoute sur localhost uniquement par défaut
- Pas d'exposition directe sur internet
- Validation des inputs (Pydantic)
- Sanitization des chemins fichiers

### Future (V2+)
- Authentification JWT
- Rôles utilisateurs
- Rate limiting global
- HTTPS recommandé

---

## 📞 Support & Contribution

### Issues GitHub
- Template pour bugs
- Template pour features
- Labels : bug, enhancement, question, documentation

### Contribution
- Fork + Pull Request
- Code review obligatoire
- Tests requis pour nouvelles features
- Documentation mise à jour

---

## 📄 Licence

**À définir** - Suggestions :
- MIT (très permissive)
- Apache 2.0 (avec protection brevets)
- GPL v3 (copyleft fort)

---

## 🎉 Remerciements

Inspirations et outils :
- [Komga](https://komga.org/) - Serveur média
- [beets](https://beets.io/) - Pour la musique
- [Sonarr/Radarr](https://sonarr.tv/) - Automation
- Bedetheque.com - Base de données BD

---

**Version du document :** 1.0  
**Dernière mise à jour :** 4 novembre 2025  
**Statut :** ✅ Validé et prêt pour développement