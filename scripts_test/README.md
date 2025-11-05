# Scripts de Test - Gaston

Ce dossier contient les scripts de test et de debug utilisés pendant le développement.

## 📋 Scripts de test disponibles

### Tests d'enrichissement

#### `test_enrichment.sh`
Test complet de l'enrichissement pour tous les livres de la base.

```bash
./test_enrichment.sh [PORT]
```

**Utilisation:**
```bash
cd scripts_test
./test_enrichment.sh 8080
```

**Ce que fait le script:**
- Vérifie que le serveur est accessible
- Enrichit tous les livres de la base
- Affiche les détails de chaque livre enrichi
- Donne les statistiques finales

---

#### `test_enrichment_no_cache.sh`
Identique à `test_enrichment.sh` mais vide le cache entre chaque livre.

```bash
./test_enrichment_no_cache.sh [PORT]
```

**Utilité:** Debug des problèmes de cache

---

#### `test_individual_books.sh`
Test l'enrichissement des livres problématiques individuellement (livres #3, #4, #6).

```bash
./test_individual_books.sh
```

**Ce que fait le script:**
- Nettoie les métadonnées du livre
- Vide le cache
- Enrichit le livre
- Affiche les résultats

**Utilité:** Vérifier que l'enrichissement fonctionne quand on traite les livres un par un

---

### Tests par lot

#### `test_4_books.sh`
Test rapide sur 4 livres spécifiques (1, 2, 4, 6).

```bash
./test_4_books.sh
```

**Ce que fait le script:**
- Nettoie la base et le cache
- Enrichit 4 livres représentatifs
- Affiche les résultats avec détails

**Utilité:** Test rapide pour vérifier que tout fonctionne

---

#### `test_all_6_books.sh`
Test complet sur tous les 6 livres de référence.

```bash
./test_all_6_books.sh
```

**Ce que fait le script:**
- Nettoie la base et le cache
- Enrichit les 6 livres
- Affiche les résultats détaillés
- Vérifie l'état final de la base

---

#### `test_books_3_5.sh`
Test uniquement les livres #3 et #5.

```bash
./test_books_3_5.sh
```

**Utilité:** Test de livres spécifiques qui posaient problème

---

#### `test_all_books.sh`
Test sur tous les livres présents dans la base.

```bash
./test_all_books.sh
```

---

### Tests de scan

#### `test_scan.sh`
Test basique du scan avec affichage de la réponse brute.

```bash
./test_scan.sh
```

**Ce que fait le script:**
- Scanne le dossier bd_sample
- Affiche la réponse JSON brute
- Parse et affiche les résultats

**Utilité:** Debug des problèmes de scan

---

### Scripts de debug Python

#### `debug_book_3.py`
Debug l'enrichissement du livre #3 (Y le dernier homme tome 3).

```bash
source ../venv/bin/activate
python debug_book_3.py
```

**Ce que fait le script:**
- Extrait le nom de série et volume du filename
- Recherche sur BDPhile
- Affiche tous les résultats avec scores
- Affiche les détails du meilleur match

**Utilité:** Comprendre pourquoi un livre n'est pas enrichi correctement

---

#### `debug_teleportation.py`
Debug l'enrichissement de Teleportation Inc.

```bash
source ../venv/bin/activate
python debug_teleportation.py
```

**Utilité:** Test spécifique pour la série Teleportation Inc.

---

## 🎯 Cas d'usage

### Vérifier que l'enrichissement fonctionne

```bash
# Test rapide
./test_4_books.sh

# Test complet
./test_all_6_books.sh
```

### Debug d'un livre qui ne s'enrichit pas

```bash
# 1. Identifier le problème avec le script Python
source ../venv/bin/activate
python debug_book_3.py

# 2. Tester l'enrichissement individuel
./test_individual_books.sh
```

### Debug de problèmes de cache

```bash
# Tester sans cache
./test_enrichment_no_cache.sh
```

### Vérifier le scan

```bash
./test_scan.sh
```

## 📊 Interprétation des résultats

### Enrichissement réussi
```
=== Livre #1 ===
📖 Teleportation Inc. 2.cbz
✓ VALIDATION AUTOMATIQUE
  Série: Teleportation Inc.
  Volume: 2
  Titre: La vie galactique
  Confiance: 1.0
```

**Signification:**
- ✅ Métadonnées trouvées
- ✅ Confiance ≥ 0.90 (validation automatique)
- ✅ Toutes les informations présentes

---

### Enrichissement avec validation manuelle
```
=== Livre #5 ===
📖 Super Comics Unknown.cbr
⚠️  VALIDATION MANUELLE REQUISE
  Confiance: 0.75
```

**Signification:**
- ⚠️ Métadonnées trouvées mais confiance < 0.90
- ⚠️ Nécessite validation manuelle

---

### Aucune correspondance
```
=== Livre #7 ===
📖 Unknown_Series.pdf
❌ AUCUNE CORRESPONDANCE
```

**Signification:**
- ❌ Aucun résultat trouvé sur BDPhile
- Cause possible: nom de fichier mal formaté ou série inconnue

---

### Erreur
```
=== Livre #8 ===
📖 Test.cbz
❌ ERREUR
```

**Signification:**
- ❌ Erreur lors de l'enrichissement (timeout, erreur réseau, etc.)

---

## 🔧 Personnalisation

### Tester sur vos propres livres

Modifiez les scripts pour pointer vers vos book IDs:

```bash
# Éditer test_4_books.sh
nano test_4_books.sh

# Changer la ligne:
for id in 1 2 4 6; do
# En:
for id in 10 11 12 13; do  # Vos IDs
```

### Créer un nouveau script de test

```bash
#!/bin/bash
# Votre script de test personnalisé

API_URL="http://localhost:8080/api"

# Vos tests ici
curl -s "$API_URL/metadata/match/1"
```

## 📝 Notes importantes

1. **Serveur requis:** Tous les scripts nécessitent que le serveur Gaston soit démarré
2. **Cache:** Les scripts utilisent le cache par défaut sauf `test_enrichment_no_cache.sh`
3. **Base de données:** Certains scripts nettoient la base, soyez prudents !
4. **Python:** Les scripts `.py` nécessitent l'activation du venv

## 🐛 Dépannage

### "API not accessible"

Le serveur n'est pas démarré:
```bash
cd ..
./start_gaston.sh
```

### "No such file or directory"

Vous devez être dans le dossier scripts_test:
```bash
cd scripts_test
./test_4_books.sh
```

### Scripts Python ne fonctionnent pas

Activez le venv:
```bash
source ../venv/bin/activate
python debug_book_3.py
```

## 🎓 Historique

Ces scripts ont été créés pendant le développement pour résoudre les problèmes suivants:

1. **Problème de ponctuation** - "Y, le dernier homme" vs "Y le dernier homme"
2. **Limitation des résultats** - Les résultats étaient limités avant le tri
3. **Redirections HTTP** - AsyncClient nécessaire pour suivre les redirects
4. **Parsing des albums Comics** - Support de `/album/comics/` en plus de `/album/bd/`
5. **Corruption du cache** - Problèmes de références d'objets dans le cache
6. **Enrichissement en batch** - Certains livres ne s'enrichissaient pas en lot

Chaque script a servi à identifier et résoudre un problème spécifique.

## 📚 Documentation

Pour la documentation complète des scripts principaux, voir:
- `../README_SCRIPTS.md` - Scripts de production
- `../CHEMINS.md` - Configuration des chemins
- `../QUICKSTART.md` - Guide de démarrage rapide
