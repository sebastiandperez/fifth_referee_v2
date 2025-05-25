from utils.utils import load_event_type_map
import unicodedata

def normalize_text(text):
    if not isinstance(text, str):
        return text
    return text.strip().lower()

def normalize_event_types(event_df):
    event_type_map = load_event_type_map('pipeline/config/event_map.json')
    normalized_map = {normalize_text(k): v for k, v in event_type_map.items()}
    event_df = event_df.dropna(subset=['match_id']).copy()
    event_df['match_id'] = event_df['match_id'].astype(float).astype('Int32')
    event_df['event_type'] = (
        event_df['event_type']
        .apply(normalize_text)
        .map(normalized_map)
    )
    unmapped = event_df[event_df['event_type'].isnull()]
    if not unmapped.empty:
        print("WARNING: THE FOLLOWING event_type AREN'T MAPPED:", unmapped['event_type'].unique())
    return event_df
