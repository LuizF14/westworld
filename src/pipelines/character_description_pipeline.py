from dataclasses import dataclass
from web_scraper.base import Searcher, Fetcher, Extractor

@dataclass
class CharacterDescriptionResult:
    character_name: str
    description: str

class CharacterDescriptionPipeline:
    def __init__(
        self,
        searcher: Searcher,
        fetcher: Fetcher,
        html_extractor: Extractor,
        max_results_per_query: int = 5,
    ):
        self.searcher = searcher
        self.fetcher = fetcher
        self.html_extractor = html_extractor
        self.max_results_per_query = max_results_per_query

    def run(self, character_name: str) -> CharacterDescriptionResult:
        search_results = self.searcher.search(character_name, self.max_results_per_query)
        
        print(f"\n{len(search_results)} results for '{character_name}':\n")
        for r in search_results:
            print(f"- {r.title}\n  {r.url}")

        documents = []
        for r in search_results:
            page = self.fetcher.fetch(r.url)
            if page is None:
                print(f"[skip:fetch] {r.url}")
                continue
    
            doc = self.html_extractor.extract(page)
            if doc is None:
                print(f"[skip:extract] {r.url}")
                continue
    
            print(f"[ok] {r.url} -> {len(doc.text)} chars")
            documents.append(doc.text)

        description = ' '.join(documents)
        result = CharacterDescriptionResult(character_name=character_name, description=description)
        return result