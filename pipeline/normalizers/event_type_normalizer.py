from utils.utils import load_event_type_map
import unicodedata

def normalize_text(text):
    if not isinstance(text, str):
        return text
    return text.strip().lower()

def normalize_event_types(event_df):
    event_type_map = load_event_type_map('pipeline/config/event_type.json')
    # Normaliza el mapping (todas las claves y valores en minúsculas)
    normalized_map = {normalize_text(k): v for k, v in event_type_map.items()}
    # Aplica el mapping sobre los valores normalizados
    event_df['event_type'] = (
        event_df['event_type']
        .apply(normalize_text)
        .map(normalized_map)
    )
    # Log de no mapeados
    unmapped = event_df[event_df['event_type'].isnull()]
    if not unmapped.empty:
        print("ATENCIÓN: Estos event_type NO están mapeados:", unmapped['event_type'].unique())
    # Ahora, si quieres forzar a que todo lo que no se mapee sea "Unknown" o similar:
    # event_df['event_type'] = event_df['event_type'].fillna("Unknown")
    return event_df
