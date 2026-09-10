from typing import TypeVar, Generic

T = TypeVar("T")

class Registry(Generic[T]):
    def __init__(self, kind: str):
        self._kind = kind
        self._items: dict[str, type[T]] = {}

    def register(self, name: str):
        def decorator(cls: type[T]) -> type[T]:
            if name in self._items:
                raise ValueError(f"'{name}' already registered '{self._kind}'")
            self._items[name] = cls
            return cls
        return decorator

    def build(self, name: str, **kwargs) -> T:
        if name not in self._items:
            raise ValueError(
                f"{self._kind} '{name}' not found. Options: {list(self._items)}"
            )
        return self._items[name](**kwargs)

    def available(self) -> list[str]:
        return list(self._items)

searchers = Registry("searcher")
fetchers = Registry("fetcher")
extractors = Registry("extractor")
agents = Registry("agents")