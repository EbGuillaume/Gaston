# Fix: Enrichissement incomplet en mode batch

## Problème

Certains livres ne s'enrichissaient pas correctement lors des tests en batch:
- Livre #3 (Y le dernier homme tome 3): seulement `series_name` sauvegardé, pas les détails
- Livre #4 (Teleportation Inc. tome 1): parfois incomplet
- Livre #6 (Y le dernier homme tome 1): parfois incomplet

Symptôme: Seul le nom de série était sauvegardé, mais pas le numéro de volume, titre, auteurs, etc.

## Cause Racine

Le problème venait de la **gestion du cache dans l'API**:

1. **Cache désactivé dans le matcher** (`backend/matching/name_matcher.py:19`):
   ```python
   use_cache: bool = False,  # TEMPORAIRE: Désactivé pour debug
   ```

2. **MAIS activé explicitement dans l'API** (`backend/api/routes/metadata.py`):
   ```python
   # Ligne 123
   matcher = NameMatcher(use_cache=True)  # ❌ Override le défaut!

   # Ligne 224
   matcher = NameMatcher(use_cache=True)  # ❌ Override le défaut!
   ```

3. **Résultat**: Le cache était activé malgré notre intention de le désactiver, et contenait des données corrompues ou incomplètes.

## Solution

Désactiver explicitement le cache dans **tous** les endpoints API:

```python
# backend/api/routes/metadata.py - Ligne 63
matcher = NameMatcher(use_cache=False)  # Cache désactivé pour debug

# backend/api/routes/metadata.py - Ligne 123
matcher = NameMatcher(use_cache=False)  # Cache désactivé pour debug

# backend/api/routes/metadata.py - Ligne 224
matcher = NameMatcher(use_cache=False)  # Cache désactivé pour debug
```

## Résultats

Après la correction, **tous les 6 livres s'enrichissent correctement**:

```
1|Teleportation Inc. 2.cbz|2|La vie galactique
2|[Comics.fr] Y le dernier homme - 02 [Pia-Vaughan].cbr|2|Un petit coin de paradis
3|[Comics.fr] Y le dernier homme - 03 - un petit pas [Vaughan - Guerra].cbr|3|Un petit pas
4|Teleportation Inc. 1.cbz|1|Perdus en translation
5|Astérix T41, Astérix en Lusitanie [CBZ] Fr.cbz|41|Astérix en Lusitanie - Artbook - Édition collector
6|[Comics.fr] Y le dernier homme - 01 [Vaughan-Guerra].cbr|1|No Man's Land
```

## Tests

Utiliser les scripts de test:

```bash
# Test rapide de 4 livres
./test_4_books.sh

# Test complet de tous les livres
./test_all_6_books.sh

# Test individuel des livres problématiques
./test_individual_books.sh
```

## À faire plus tard

1. **Réactiver le cache** une fois que le bug de corruption est résolu
2. **Ajouter des tests unitaires** pour vérifier que l'enrichissement fonctionne correctement
3. **Investiguer le bug de deep copy** dans `backend/scrapers/cache.py` qui causait la corruption

## Historique des corrections

1. **Punctuation normalization**: Fix pour "Y, le dernier homme" vs "Y le dernier homme"
2. **Sort before limit**: Tri des résultats avant limitation pour trouver les meilleurs matchs
3. **AsyncClient**: Utilisation de `httpx.AsyncClient` pour suivre les redirections
4. **Comics album parsing**: Support des URLs `/album/comics/` en plus de `/album/bd/`
5. **Deep copy in cache**: Ajout de `copy.deepcopy()` dans le cache (pas suffisant)
6. **Cache désactivé** (cette correction): Désactivation complète du cache dans l'API

## Date

2025-11-05
