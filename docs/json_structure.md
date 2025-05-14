## Understanding the Match JSON Format

Each `.json` file in this project represents a single football match in a structured, clean format — designed for analysis, modeling, and reproducibility.

This format isn’t just technical — it reflects a way of **thinking about football data**. Below, we walk through each part of the structure and explain the reasoning behind it.

---

### `match_id`

This is the **unique identifier** for the match. It’s how we avoid counting the same match twice. No matter where the data goes — a database, a model, or a report — this `match_id` is the root reference.

---

### `matchday`

Each match belongs to a matchday, which indicates **when in the season** it was played. This helps organize the competition’s timeline and makes it easier to filter or segment performance across early, mid, or late stages of the season.

---

### `homeCompetitor` / `awayCompetitor`

These hold the basic info about each team:
- `team_id` 
- `team_name` 
- `team_score` – goals scored

This separation is **crucial for context**: performance at home is often very different from away. By explicitly splitting home and away, we keep that context embedded in the data itself.

---

### `stadium`

This tells us where the match was played. Even if a team is marked as the "home team", they might not play in their usual stadium — because of construction, sanctions, or special events. Keeping track of the actual stadium gives **geographical and logistical context** to the match.

---

### `duration`

We record how many minutes were effectively played — usually a number like 95, 97, 102, etc. This might seem small, but **total playtime affects fatigue, pacing, and even strategy**. It matters more than it looks.

---

### `events`

Here we track **things that happened in the match but aren’t just player stats**. For example:
- Substitutions
- Goals
- Cards
- Woodwork (shots hitting post or bar)

Each event has:
- `team_id` – which team it belongs to
- `minute` – when it happened
- `eventType` – type of event
- `player_id` – the main actor
- `extra_player_id` – second actor (e.g., substitute coming in)

These events add **narrative to the match**, and help us reconstruct its flow.

---

### `players`

This is a **combined registry** of all the players (and coaches) involved in the match. Each entry includes:
- `team_id`
- `player_id`
- `name`
- `jersey_number`
- `position`
- `ranking` (if available)
- `status` (starter = 1, substitute = 2, missing = 3)
- `stats`

The `stats` field is a dictionary of performance data. Each stat has:
- `name` → e.g., "Total Shots"
- `value` → e.g., 4

This lets you track **what each player did, where they played, and how they performed**. It’s structured for both team-level and individual-level analysis.

---

### Why This Structure?

Because raw data is chaotic. This structure brings:
- **Consistency**: all matches follow the same shape.
- **Traceability**: every number is linked to a match, a team, a player.
- **Flexibility**: it’s easy to reshape this data into tables, dashboards, or ML-ready datasets.

