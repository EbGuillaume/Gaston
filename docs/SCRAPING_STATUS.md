# Status des Scrapers de Métadonnées

## BDPhile.fr - ✅ FONCTIONNEL

**Dernière vérification:** 2025-11-05

**Status:** Opérationnel avec enrichissement complet des métadonnées

**Fonctionnalités implémentées:**

1. **Recherche de séries**
   - Recherche par nom de série sur `/search/series/`
   - Support des BD franco-belges (`/series/view/ID/`)
   - Support des Comics américains (mêmes URLs dans la recherche)
   - Matching intelligent avec normalisation de la ponctuation

2. **Enrichissement des métadonnées**
   - Récupération complète des détails d'album (auteurs, éditeur, ISBN, etc.)
   - Parsing du synopsis
   - Extraction des dates de publication
   - Préservation des numéros de tome

3. **Calcul de confiance amélioré**
   - Normalisation des noms (retire ponctuation, accents, etc.)
   - Score de 1.0 pour match exact après normalisation
   - Score de 0.95 pour inclusion
   - Seuil de validation automatique: ≥ 0.90

**Problèmes résolus:**

### Issue #1: Comics non trouvés (2025-11-05) ✅ RÉSOLU
- **Problème:** Les comics comme "Y le dernier homme" n'étaient pas validés automatiquement
- **Cause:** BDPhile utilise `/series/view/ID/` pour TOUS les types de séries dans la recherche
- **Impact:** La ponctuation (`"Y, le dernier homme"` vs `"Y le dernier homme"`) causait un score de 0.85 < 0.90
- **Solution:** Normalisation de la ponctuation dans `_calculate_confidence()`
- **Résultat:** Score passé de 0.85 → 1.00, validation automatique ✅

**Configuration:**
```yaml
scrapers:
  bdphile:
    enabled: true
    base_url: "https://www.bdphile.fr"
    rate_limit: 1.0  # 1 req/sec
    timeout: 10.0
```

**Tests effectués:**
```bash
# Test 1: Recherche "Astérix"
curl -s "https://www.bdphile.fr/search/series/?q=Asterix" | grep -o '/series/view/[0-9]*' | head -5
# Résultat: /series/view/124/ (trouvé)

# Test 2: Recherche "Y le dernier homme"
curl -s "https://www.bdphile.fr/search/series/?q=Y,%20le%20dernier%20homme" | grep "Y, le dernier homme"
# Résultat: /series/view/4315/ (trouvé) + /series/view/12132/ (Urban Comics)

# Test 3: Enrichissement complet
# Book: Astérix T41 → Score: 1.00, auto-validé
# Book: Y le dernier homme 01 → Score: 1.00, auto-validé
```

---

## Bedetheque.com - ⚠️ NON FONCTIONNEL

**Dernière vérification:** 2025-11-04

**Problèmes identifiés:**

1. **Protection anti-scraping active**
   - Les requêtes GET vers `/search/albums?RechSerie=X` retournent le formulaire vide (pas de résultats)
   - Les requêtes POST vers `/search/albums` sont bloquées (HTTP 403 Forbidden)
   - Probablement protection CSRF token + WAF

2. **Pas d'API publique**
   - Aucune API officielle documentée
   - Pas de JSON-LD ou microdata structurée
   - Base collaborative sans accès programmatique

3. **Limitations techniques**
   - 422,253+ albums dans la base
   - Nécessiterait un scraping respectueux avec rate limiting
   - Risque de blocage IP

**Solutions possibles:**

### Option 1: Contact direct (Recommandé pour usage légal)
Contacter Bedetheque pour:
- Demander l'accès à une API ou export de données
- Négocier un partenariat pour accès programmatique
- Obtenir une autorisation de scraping avec rate limits appropriés

### Option 2: Scraping avancé (Non implémenté)
Techniques possibles mais non recommandées sans autorisation:
- Utiliser Selenium/Playwright pour simuler un navigateur
- Implémenter gestion des cookies et CSRF tokens
- Rotation d'IP et rate limiting agressif
- **⚠️ Risque:** Violation des ToS, blocage IP, problèmes légaux

### Option 3: Sources alternatives (Recommandé pour MVP)

#### ComicVine API
- **URL:** https://comicvine.gamespot.com/api/
- **Avantage:** API officielle, bien documentée
- **Limitation:** Nécessite une clé API (gratuite)
- **Couverture:** Comics américains principalement
- **Status:** À implémenter

#### Open Library API
- **URL:** https://openlibrary.org/developers/api
- **Avantage:** API publique, pas de clé requise
- **Couverture:** Livres principalement, quelques BD
- **Status:** À implémenter

#### Google Books API
- **URL:** https://developers.google.com/books
- **Avantage:** Vaste couverture, API gratuite
- **Limitation:** Quota quotidien, pas spécialisé BD
- **Status:** À implémenter

#### Anilist API (Pour manga)
- **URL:** https://anilist.gitbook.io/anilist-apiv2-docs
- **Avantage:** API GraphQL, excellente pour manga/anime
- **Couverture:** Manga et light novels
- **Status:** À implémenter

### Option 4: Métadonnées manuelles (Implémenté)
- Interface pour saisie manuelle des métadonnées
- Import depuis fichiers CSV/JSON
- Édition des métadonnées existantes

## Recommandation pour le MVP

Pour la version MVP de Gaston, nous recommandons:

1. **Court terme:**
   - Désactiver Bedetheque par défaut
   - Implémenter saisie manuelle des métadonnées
   - Ajouter support d'import CSV

2. **Moyen terme:**
   - Implémenter ComicVine API pour les comics
   - Implémenter Anilist API pour les manga
   - Améliorer l'extraction des métadonnées depuis les fichiers CBZ/CBR (ComicInfo.xml)

3. **Long terme:**
   - Contacter Bedetheque pour partenariat/autorisation
   - Implémenter scraping respectueux si autorisation obtenue
   - Créer une base collaborative communautaire propre à Gaston

## Configuration actuelle

```yaml
scrapers:
  bedetheque:
    enabled: false  # Désactivé par défaut
    reason: "Anti-scraping protection active"
    rate_limit: 1.0  # 1 req/sec si réactivé
```

## Tests effectués

```bash
# Test 1: GET search
curl "https://www.bedetheque.com/search/albums?RechSerie=asterix"
# Résultat: Formulaire vide, 0 résultats

# Test 2: POST search
curl -X POST "https://www.bedetheque.com/search/albums" \
  -d "RechSerie=asterix"
# Résultat: HTTP 403 Forbidden

# Test 3: Direct series page
curl "https://www.bedetheque.com/serie-396-BD-Asterix.html"
# Résultat: Page fonctionnelle, mais nécessite connaître l'ID exact
```

## Prochaines étapes

1. ✅ Documenter le problème
2. ⏳ Désactiver Bedetheque dans la config par défaut
3. ⏳ Ajouter endpoints d'édition manuelle des métadonnées
4. 📋 Implémenter ComicVine API comme alternative
5. 📋 Ajouter extraction des métadonnées depuis ComicInfo.xml

---

**Date de mise à jour:** 2025-11-04
**Testé par:** Claude Code
**Version Gaston:** 0.1.0
