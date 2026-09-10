import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from registry import searchers, fetchers
import web_scraper.searchers.wikipedia
import web_scraper.fetchers.http_fetcher


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Test searcher + fetcher.")
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    args = parser.parse_args()

    cfg = load_config(args.config)

    searcher_cfg = cfg["searcher"]
    fetcher_cfg = cfg["fetcher"]
    searcher = searchers.build(searcher_cfg["name"], **searcher_cfg.get("params", {}))
    fetcher = fetchers.build(fetcher_cfg["name"], **fetcher_cfg.get("params", {}))

    results = searcher.search(cfg["query"], max_results=cfg.get("max_results", 5))
    print(f"\n{len(results)} results for '{cfg['query']}':\n")
    for r in results:
        print(f"- {r.title}\n  {r.url}")

    fetched = []
    for r in results:
        page = fetcher.fetch(r.url)
        if page is None:
            print(f"[skip] failed to fetch: {r.url}")
            continue

        print(f"[ok] {r.url} -> {len(page.content)} chars, status={page.status_code}")
        fetched.append({
            "url": page.url,
            "title": r.title,
            "content_type": page.content_type,
            "status_code": page.status_code,
            "fetched_at": page.fetched_at.isoformat(),
            "content": page.content,
        })

    out_path = Path(cfg["output"]["path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fetched, f, ensure_ascii=False, indent=2)

    print(f"\n{len(fetched)}/{len(results)} pages saved in: {out_path}")


if __name__ == "__main__":
    main()