import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from registry import searchers
import data_collection.searchers.wikipedia

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Test only the searcher.")
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    args = parser.parse_args()

    cfg = load_config(args.config)

    searcher_cfg = cfg["searcher"]
    searcher = searchers.build(searcher_cfg["name"], **searcher_cfg.get("params", {}))

    results = searcher.search(cfg["query"], max_results=cfg.get("max_results", 5))

    print(f"\n{len(results)} results for '{cfg['query']}':\n")
    for r in results:
        print(f"- {r.title}\n  {r.url}")

    out_path = Path(cfg["output"]["path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([r.__dict__ for r in results], f, ensure_ascii=False, indent=2)

    print(f"\nSaved in: {out_path}")


if __name__ == "__main__":
    main()