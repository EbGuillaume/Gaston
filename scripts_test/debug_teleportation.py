#!/usr/bin/env python3
import sys
sys.path.insert(0, "backend")

import asyncio
from scrapers.bdphile import BDPhileScraper

async def test():
    scraper = BDPhileScraper()

    # Recherche Teleportation Inc
    print("=== Recherche Teleportation Inc ===")
    results = await scraper.search("teleportation inc", limit=5)

    for i, r in enumerate(results, 1):
        print(f"{i}. {r.series_name} (ID: {r.raw_data.get('series_id')})")

    best = results[0]
    series_id = best.raw_data.get('series_id')

    # Récupérer les détails de la série
    print(f"\n=== Détails série {series_id} ===")
    details = await scraper.get_series_details(series_id)

    if details and details.get('albums'):
        print(f"Albums trouvés: {len(details['albums'])}")
        for album in details['albums']:
            print(f"  - Volume {album.get('volume_number')}: {album.get('title')} (ID: {album.get('id')})")
    else:
        print("❌ Aucun album trouvé")

    # Tester enrichissement tome 1
    print("\n=== Enrichissement tome 1 ===")
    enriched1 = await scraper.enrich_with_album_details(best, volume_number=1)
    print(f"Volume: {enriched1.volume_number}")
    print(f"Titre: {enriched1.title}")
    print(f"Auteurs: {enriched1.writers}")

    # Tester enrichissement tome 2
    print("\n=== Enrichissement tome 2 ===")
    enriched2 = await scraper.enrich_with_album_details(best, volume_number=2)
    print(f"Volume: {enriched2.volume_number}")
    print(f"Titre: {enriched2.title}")
    print(f"Auteurs: {enriched2.writers}")

asyncio.run(test())
