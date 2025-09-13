import json, os
from functools import lru_cache

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIELD_MAP_PATH = os.path.join(THIS_DIR, 'field_map.json')

@lru_cache(maxsize=1)
def _load_map() -> dict:
    if not os.path.exists(FIELD_MAP_PATH):
        return {}
    with open(FIELD_MAP_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def fmap(name: str) -> str:
    """Devuelve la clave real según field_map.json; si no existe, regresa name."""
    m = _load_map()
    return m.get(name, name)
