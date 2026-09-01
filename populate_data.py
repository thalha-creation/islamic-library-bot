"""
populate_data.py — pulls sample content from free, no-key APIs and loads it into the DB.

Run this once before starting the bot (needs internet on your machine):
    python populate_data.py

By default it loads a SMALL sample (a few well-known surahs) so you can test quickly.
Edit SURAHS_TO_LOAD below to load more/all 114 surahs — it will just take longer.

Sources used (all free, no API key needed):
- Quran Arabic + translations (incl. Tamil, Urdu, English): fawazahmed0/quran-api
- Tafsir (Arabic/English/Urdu):                              spa5k/tafsir_api
- Hadith (Arabic/English/Urdu):                               fawazahmed0/hadith-api

NOTE: Tamil Tafsir and Tamil Hadith Sharah are NOT available as free ready-made APIs.
Use the bot's /addtafsir and /addhadith admin commands to add Tamil sharah content yourself.
"""

import requests
from db import init_db, bulk_add

# ---- Config: which surahs to pull for the demo (edit as needed, 1-114) ----
SURAHS_TO_LOAD = [1, 2, 36, 55, 67, 112, 113, 114]

QURAN_API_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1"
TAFSIR_API_BASE = "https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main"
HADITH_API_BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1"

# Edition codes (see /editions.json on each API for the full list)
QURAN_EDITIONS = {
    "ar": "ara-quranarabic",
    "en": "eng-sahihinternational",
    "ur": "urd-mahmoodulhassan",
    "ta": "tam-tamilstandard",   # Tamil translation edition (verify exact code via editions.json)
}
TAFSIR_EDITIONS = {
    "en": "en-tafisr-ibn-kathir",
    "ar": "ar-tafsir-al-tabari",
    "ur": "ur-tafsir-bayan-ul-quran",
}
HADITH_EDITIONS = {
    "ar": "ara-bukhari",
    "en": "eng-bukhari",
    "ur": "urd-bukhari",
}


def fetch_json(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def load_quran_translations():
    rows = []
    for lang, edition in QURAN_EDITIONS.items():
        for surah in SURAHS_TO_LOAD:
            try:
                data = fetch_json(f"{QURAN_API_BASE}/editions/{edition}/{surah}.json")
            except Exception as e:
                print(f"  [skip] quran {lang} surah {surah}: {e}")
                continue
            for ayah in data["chapter"]:
                rows.append({
                    "entry_type": "quran_translation",
                    "language": lang,
                    "term": None,
                    "source": edition,
                    "reference": f"Surah {surah}:{ayah['verse']}",
                    "content": ayah["text"],
                    "added_by": "system",
                })
    bulk_add(rows)
    print(f"Loaded {len(rows)} Quran translation ayahs.")


def load_tafsir():
    rows = []
    for lang, edition in TAFSIR_EDITIONS.items():
        for surah in SURAHS_TO_LOAD:
            try:
                data = fetch_json(f"{TAFSIR_API_BASE}/tafsirs/{edition}/{surah}.json")
            except Exception as e:
                print(f"  [skip] tafsir {lang} surah {surah}: {e}")
                continue
            ayahs = data.get("ayahs", data if isinstance(data, list) else [])
            for ayah in ayahs:
                rows.append({
                    "entry_type": "tafsir",
                    "language": lang,
                    "term": None,
                    "source": edition,
                    "reference": f"Surah {surah}:{ayah.get('ayah', '?')}",
                    "content": ayah.get("text", ""),
                    "added_by": "system",
                })
    bulk_add(rows)
    print(f"Loaded {len(rows)} tafsir entries.")


def load_hadith():
    rows = []
    for lang, edition in HADITH_EDITIONS.items():
        try:
            data = fetch_json(f"{HADITH_API_BASE}/editions/{edition}.json")
        except Exception as e:
            print(f"  [skip] hadith {lang}: {e}")
            continue
        hadiths = data.get("hadiths", [])[:200]  # demo cap; remove slice to load all
        for h in hadiths:
            rows.append({
                "entry_type": "hadith",
                "language": lang,
                "term": None,
                "source": edition,
                "reference": f"{edition} #{h.get('hadithnumber')}",
                "content": h.get("text", ""),
                "added_by": "system",
            })
    bulk_add(rows)
    print(f"Loaded {len(rows)} hadith entries.")


if __name__ == "__main__":
    init_db()
    print("Fetching Quran translations...")
    load_quran_translations()
    print("Fetching Tafsir...")
    load_tafsir()
    print("Fetching Hadith...")
    load_hadith()
    print("\nDone. Tamil tafsir/hadith sharah is empty by design —")
    print("add it via the bot's /addtafsir or /addhadith admin commands.")
