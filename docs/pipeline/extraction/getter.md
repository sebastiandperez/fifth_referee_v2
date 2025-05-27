### getter.py

**Purpose:**  
`getter.py` provides a general-purpose function to fetch raw match data from a given reference (such as a URL, file path, or API endpoint). The details of how the data is obtained are abstracted away, ensuring that downstream modules always receive a consistent raw data structure.

**Key Function:**

- `fetch_raw_match_json(reference, ...)`
  Returns the raw match data object (typically a Python `dict`) for a given match reference.  
  The reference may point to a local file, a database record, or a remote API, depending on project needs.

**Expected Output:**

The function should always return a raw match object with at least the following characteristics:

- Type: `dict` (or compatible mapping)
- Contains all relevant fields for the match, such as teams, events, players, and statistics, **in the original, unprocessed format**.

```python
{
  "id": "123456",
  "matchday": 14,
  "local_team": { ... },
  "away_team": { ... },
  "stadium": { ... },
  "events": [ ... ],
  "members": [ ... ]
  # ...other raw fields as provided by the source
}
