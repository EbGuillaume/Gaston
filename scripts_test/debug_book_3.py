#!/usr/bin/env python3
"""Debug enrichment for book #3"""
import sys
sys.path.insert(0, "backend")

import asyncio
from matching.name_matcher import NameMatcher

async def debug():
    # Test avec le même nom de fichier que book #3
    filename = "[Comics.fr] Y le dernier homme - 03 - un petit pas [Vaughan - Guerra].cbr"

    print(f"=== Debug enrichissement pour: {filename} ===\n")

    # Créer matcher SANS cache
    matcher = NameMatcher(use_cache=False)

    # Chercher les correspondances
    matches = await matcher.match(filename)

    print(f"Nombre de résultats: {len(matches)}\n")

    if matches:
        best = matches[0]
        print(f"Meilleur résultat:")
        print(f"  Source: {best.source}")
        print(f"  Confiance: {best.confidence}")
        print(f"  Série: {best.series_name}")
        print(f"  Volume: {best.volume_number}")
        print(f"  Titre: {best.title}")
        print(f"  Résumé: {best.summary[:100] if best.summary else None}...")
        print(f"  Auteurs: {best.writers}")
        print(f"  Dessinateurs: {best.pencillers}")
        print(f"  Éditeur: {best.publisher}")
        print(f"  Date: {best.publication_date}")
        print(f"  URL: {best.url}")

        # Afficher les raw_data
        if best.raw_data:
            print(f"\n  Raw data keys: {list(best.raw_data.keys())}")

    await matcher.close()

asyncio.run(debug())
