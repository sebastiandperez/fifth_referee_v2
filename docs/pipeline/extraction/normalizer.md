### normalizer.py

**Purpose:**  
`normalizer.py` is responsible for converting the raw, heterogeneous match data objects into a **clean, consistent, and well-defined JSON structure**. This process is crucial for ensuring that all downstream analysis or data loading routines work with uniform, predictable data.

**Key Features:**
- Loads dynamic field mappings from a configuration file (`field_map.json`) so that renaming and harmonizing of keys is flexible and easy to update.
- Uses utility functions to safely extract nested information and handle missing or variant fields.
- Calls specialized normalization functions for each key data block, including:
    - **Players** (`normalize_member`)
    - **Lineups** (`normalize_lineup`)
    - **Stats** (`normalize_stats`)
    - **Events** (`normalize_event`)
    - **Match Duration** (`normalize_duration`)
- Merges player information across data sources (e.g., lineups and members) to ensure no duplicates or missing details.

**Core Workflow:**
1. **Field Mapping:**  
   All fields are dynamically mapped using `field_map.json`, allowing the normalization process to be easily adapted if the source data changes its structure or key names.

2. **Nested Extraction:**  
   The normalizer uses helper functions to access nested or optional fields robustly, returning defaults when data is missing or malformed.

3. **Block Normalization:**  
   For each main data block (e.g., players, teams, events), dedicated normalization functions are applied to clean and structure the data consistently.

4. **Player Merging:**  
   Lineup and member information is joined on player IDs, ensuring each player appears only once per match and all attributes are consolidated.

5. **Output Structure:**  
   The result is a well-formed Python `dict` with the following main keys:
   - `match_id`
   - `matchday`
   - `local_team`
   - `away_team`
   - `stadium`
   - `duration`
   - `events`
   - `players`

**Example Output (simplified):**

```python
{
    "match_id": "12345",
    "matchday": 18,
    "local_team": {
        "team_id": 2,
        "team_name": "Atlético Nacional",
        "team_score": 3
    },
    "away_team": {
        "team_id": 5,
        "team_name": "Millonarios",
        "team_score": 1
    },
    "stadium": "Estadio Atanasio Girardot",
    "duration": 90,
    "events": [ ... ],
    "players": [ ... ]
}
