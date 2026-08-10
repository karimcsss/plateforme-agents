from tavily import TavilyClient

from app.config import TAVILY_API_KEY

_client: TavilyClient | None = None


def get_tavily_client() -> TavilyClient:
    global _client
    if _client is None:
        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY manquante — vérifie ton .env")
        _client = TavilyClient(api_key=TAVILY_API_KEY)
    return _client


def web_search(query: str, max_results: int = 3) -> list[dict]:
    """Encapsulation de l'outil de recherche web.
    Retourne une liste de résultats simplifiés (titre, url, extrait) —
    jamais l'objet Tavily brut, pour garder une frontière claire entre
    l'outil externe et le reste du système (NF4 : outils encapsulés)."""
    client = get_tavily_client()
    response = client.search(query=query, max_results=max_results)
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", "")[:500],  # tronqué pour limiter les tokens envoyés au LLM ensuite
        }
        for r in response.get("results", [])
    ]