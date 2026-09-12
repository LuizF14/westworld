import argparse
import json
import sys
from pathlib import Path
from dataclasses import asdict

import yaml
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from registry import searchers, fetchers, extractors
import web_scraper.searchers.wikipedia
import web_scraper.fetchers.http_fetcher
import web_scraper.extractors.html_extractor
from agents.description_agent import DescriptionAgent

from pipelines.character_description_pipeline import CharacterDescriptionPipeline


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

    agent = DescriptionAgent(model=cfg["description_agent"]["model"], temperature=cfg["description_agent"]["temperature"])

    pipeline = CharacterDescriptionPipeline(searcher, fetcher, extractor, description_agent=agent)
    description = pipeline.run(cfg["query"])

    out_path = Path(cfg["output"]["path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(asdict(description), f, ensure_ascii=False, indent=2)

    print(f"\nDocuments saved in: {out_path}")


if __name__ == "__main__":
    main()