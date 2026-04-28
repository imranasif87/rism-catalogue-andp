#!/usr/bin/env python3
"""
enrich_index.py

Runs after `bundle exec jekyll load-data` to extend index/index.json
with source metadata fetched from the RISM Online API.

Each work gains a `sources` key containing:
  - count        : total number of sources
  - items        : list of source summaries
      - id             : RISM Online URL for the source record
      - label          : English human-readable label
      - sourceType     : e.g. "Autograph manuscript"
      - contentType    : e.g. "Notated music"
      - hasDigitization: bool
      - hasIncipits    : bool
      - digitizationUrl: URL to digitized image (if available)
      - rismOnlineUrl  : direct link to the source on rism.online
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path

INDEX_PATH   = Path("index/index.json")
HEADERS      = {"Accept": "application/ld+json"}
DELAY        = 0.5   # seconds between API calls — be polite to rism.online
MAX_RETRIES  = 3


def fetch_json(url: str) -> dict | None:
    """Fetch JSON-LD from a URL with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code} for {url} (attempt {attempt + 1})")
            if e.code == 404:
                return None           # no sources — not an error
            time.sleep(2 ** attempt)  # exponential back-off
        except Exception as e:
            print(f"  Error fetching {url}: {e} (attempt {attempt + 1})")
            time.sleep(2 ** attempt)
    return None


def extract_source_summary(item: dict) -> dict:
    """
    Extract the fields we care about from a single source item.
    Mirrors the structure of the JSON-LD you shared.
    """
    summary = item.get("summary", {})
    flags   = item.get("flags", {})

    # --- label (English) ---
    label = (
        item.get("label", {}).get("en", [None])[0]
        or item.get("label", {}).get("none", [None])[0]
        or item.get("id", "")
    )

    # --- source type e.g. "Autograph manuscript" ---
    source_type = (
        summary.get("materialSourceTypes", {})
               .get("value", {})
               .get("en", [None])[0]
    )

    # --- content type e.g. "Notated music" ---
    content_type = (
        summary.get("materialContentTypes", {})
               .get("value", {})
               .get("en", [None])[0]
    )

    # --- digitization URL ---
    # Lives on the parent collection record under partOf.items[].relatedTo.externalResources
    digitization_url = None
    part_of_items = item.get("partOf", {}).get("items", [])
    for part in part_of_items:
        related = part.get("relatedTo", {})
        for resource in related.get("externalResources", []):
            resource_type = resource.get("resourceType", "")
            if resource_type in ("rism:DigitizationLink", "rism:IIIFManifest"):
                digitization_url = resource.get("url")
                break
        if digitization_url:
            break

    # --- holding institution: parse from label (e.g. "GB-Lbl") ---
    # The siglum always appears after the last semicolon in the label
    holding = None
    if label and ";" in label:
        parts = [p.strip() for p in label.split(";")]
        # Last segment is "GB-Lbl R.M.20.h.8." — take everything before the space
        last = parts[-1]
        if last:
            holding = last.split(" ")[0].rstrip(".")

    return {
        "id":              item.get("id"),
        "label":           label,
        "sourceType":      source_type,
        "contentType":     content_type,
        "hasDigitization": flags.get("hasDigitization", False),
        "hasIncipits":     flags.get("hasIncipits", False),
        "digitizationUrl": digitization_url,
        "holdingInstitution": holding,
        "rismOnlineUrl":   item.get("id", "").replace(
                               "https://rism.online/",
                               "https://rism.online/"
                           ),
    }


def enrich_work(work: dict) -> dict:
    """
    Fetch sources for one work and add a `sources` key to it.
    The sources URL is always {work_id}/sources.
    """
    work_id     = work.get("id", "")
    sources_url = f"{work_id}/sources"

    print(f"  Fetching sources for {work_id.split('/')[-1]} ...", end=" ")

    data = fetch_json(sources_url)
    if data is None:
        print("no data")
        return work

    total = data.get("totalItems", 0)
    items = data.get("items", [])

    print(f"{total} source(s)")

    work["sourcesCount"] = total
    work["sourcesUrl"]   = sources_url

    if items:
        work["sources"] = [extract_source_summary(item) for item in items]
    else:
        work["sources"] = []

    time.sleep(DELAY)
    return work


def main():
    if not INDEX_PATH.exists():
        print(f"ERROR: {INDEX_PATH} not found — run `bundle exec jekyll load-data` first.")
        raise SystemExit(1)

    print(f"Loading {INDEX_PATH} ...")
    with INDEX_PATH.open(encoding="utf-8") as f:
        works = json.load(f)

    print(f"Enriching {len(works)} works with source data from rism.online ...\n")

    enriched = []
    for i, work in enumerate(works, 1):
        print(f"[{i}/{len(works)}]", end=" ")
        enriched.append(enrich_work(work))

    print(f"\nWriting enriched index to {INDEX_PATH} ...")
    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, separators=(",", ":"))

    print("Done.")


if __name__ == "__main__":
    main()