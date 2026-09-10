import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from registry import searchers, fetchers, extractors
import web_scraper.searchers.wikipedia
import web_scraper.fetchers.http_fetcher
import web_scraper.extractors.html_extractor


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Test searcher + fetcher + extractor.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    cfg = load_config(args.config)

    searcher = searchers.build(cfg["searcher"]["name"], **cfg["searcher"].get("params", {}))
    fetcher = fetchers.build(cfg["fetcher"]["name"], **cfg["fetcher"].get("params", {}))
    extractor = extractors.build(cfg["extractor"]["name"], **cfg["extractor"].get("params", {}))

    results = searcher.search(cfg["query"], max_results=cfg.get("max_results", 5))
    print(f"\n{len(results)} results for '{cfg['query']}':\n")
    for r in results:
        print(f"- {r.title}\n  {r.url}")

    documents = []
    for r in results:
        page = fetcher.fetch(r.url)
        if page is None:
            print(f"[skip:fetch] {r.url}")
            continue

        doc = extractor.extract(page)
        if doc is None:
            print(f"[skip:extract] {r.url}")
            continue

        print(f"[ok] {r.url} -> {len(doc.text)} chars")
        documents.append({
            "url": doc.url,
            "title": doc.title,
            "text": doc.text,
            "extracted_at": doc.extracted_at.isoformat(),
        })

    out_path = Path(cfg["output"]["path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"\n{len(documents)}/{len(results)} documents saved in: {out_path}")


if __name__ == "__main__":
    main()