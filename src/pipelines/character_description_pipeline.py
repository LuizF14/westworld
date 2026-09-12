from dataclasses import dataclass, field
from web_scraper.base import Searcher, Fetcher, Extractor
from agents.base import CharacterAgent

@dataclass
class CharacterDescriptionResult:
    character_name: str
    descriptions: list[str] = field(default_factory=list)
    num_sources: int = 0

class CharacterDescriptionPipeline:
    def __init__(
        self,
        searcher: Searcher,
        fetcher: Fetcher,
        html_extractor: Extractor,
        description_agent: CharacterAgent,
        max_results_per_query: int = 5,
        num_variants: int = 3,
    ):
        self.searcher = searcher
        self.fetcher = fetcher
        self.html_extractor = html_extractor
        self.description_agent = description_agent
        self.max_results_per_query = max_results_per_query
        self.num_variants = num_variants

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

        if not documents:
            raise RuntimeError(f"No document extracted to '{character_name}'.")

        descriptions = []
        for i in range(self.num_variants):
            description = self.description_agent.generate_description(character_name, documents)
            print(f"\n--- Variant {i + 1} ---\n{description}\n")
            descriptions.append(description)

        result = CharacterDescriptionResult(
            character_name=character_name,
            descriptions=descriptions,
            num_sources=len(documents),
        )
        return result