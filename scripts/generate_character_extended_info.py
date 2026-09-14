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
import web_scraper.searchers.duckduckgo
import web_scraper.fetchers.http_fetcher
import web_scraper.extractors.html_extractor
from agents.keyword_agent import KeywordAgent
from agents.summary_agent import SummaryAgent

from pipelines.character_extended_info_pipeline import CharacterExtendedInfoPipeline


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Searcher + fetcher + extractor + keyword + searcher.")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    cfg = load_config(args.config)

    base_searcher = searchers.build(cfg["base_searcher"]["name"], **cfg["base_searcher"].get("params", {}))
    keyword_searcher = searchers.build(cfg["keyword_searcher"]["name"], **cfg["keyword_searcher"].get("params", {}))
    fetcher = fetchers.build(cfg["fetcher"]["name"], **cfg["fetcher"].get("params", {}))
    extractor = extractors.build(cfg["extractor"]["name"], **cfg["extractor"].get("params", {}))

    keyword_agent = KeywordAgent(model=cfg["keyword_agent"]["model"], temperature=cfg["keyword_agent"]["temperature"])

    pipeline = CharacterExtendedInfoPipeline(base_searcher, keyword_searcher, fetcher, extractor, keyword_agent)

    extended_info = pipeline.run(cfg["query"])

    out_path = Path(cfg["output"]["path"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(asdict(extended_info), f, ensure_ascii=False, indent=2)
    
    print(f"\nDocuments saved in: {out_path}")

if __name__ == "__main__":
    main()