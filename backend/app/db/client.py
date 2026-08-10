from supabase import create_client, Client

from app.config import SUPABASE_URL, SUPABASE_KEY

_client: Client | None = None


def get_supabase() -> Client:
    """Client Supabase en singleton — un seul par process, réutilisé
    entre les requêtes plutôt que recréé à chaque appel."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL / SUPABASE_KEY manquantes — vérifie ton .env")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client