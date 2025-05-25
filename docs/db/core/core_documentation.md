# fifth_referee_v2 Database Documentation

## Schema: core

### Overview
The `core` schema stores the main match and season data required for football analytics. It connects competitions, seasons, matchdays, matches, events, player participation, and basic match statistics. While it captures key details, advanced per-position statistics are stored in the `stats` schema.

---

### Main Entities and Relationships

- **season**: Represents a season of a competition.
  Linked to `reference.competition`. Uniqueness is enforced on the pair (competition_id, season_label).
- **matchday**: Represents a round or matchday within a season.
  Linked to a `season`. Uniqueness is enforced on (season_id, matchday_number).
- **match**: Represents an individual football match, linked to a specific matchday and both home (local) and away teams. Enforces home and away team cannot be the same.
- **event**: In-game events (goals, cards, etc.) associated with a match, player(s), and optionally a team.
- **participation**: Links players to matches, storing their status and position. Composite PK (match_id, player_id).
- **basic_stats**: Stores basic stats for a player in a match. Enforced uniqueness on (match_id, player_id) and foreign key to participation.

---

### Table Summaries

#### `season`

| Column           | Type         | Description                                     |
|------------------|--------------|-------------------------------------------------|
| season_id        | SMALLINT, PK, auto-increment | Unique identifier                  |
| season_label     | VARCHAR(20), NOT NULL        | Season label (e.g., 2022_2023)     |
| competition_id   | SMALLINT, NOT NULL, FK       | References `reference.competition` |
| is_completed     | BOOLEAN, NOT NULL, default FALSE | Is the season finished?         |
| UNIQUE (competition_id, season_label)           | Ensures no duplicate seasons per competition |

#### `matchday`

| Column           | Type         | Description                                 |
|------------------|--------------|---------------------------------------------|
| matchday_id      | INTEGER, PK, auto-increment | Unique matchday ID                |
| season_id        | SMALLINT, NOT NULL, FK      | References `core.season`          |
| matchday_number  | SMALLINT, NOT NULL          | Sequential number (>0)            |
| UNIQUE (season_id, matchday_number)            | Ensures unique round per season   |

#### `match`

| Column           | Type          | Description                                  |
|------------------|---------------|----------------------------------------------|
| match_id         | INTEGER, PK   | Unique match ID                              |
| matchday_id      | INTEGER, NOT NULL, FK | References `core.matchday`            |
| local_team_id    | INTEGER, NOT NULL, FK | References `reference.team`           |
| away_team_id     | INTEGER, NOT NULL, FK | References `reference.team`           |
| local_score      | SMALLINT      | Home team goals (>=0)                        |
| away_score       | SMALLINT      | Away team goals (>=0)                        |
| duration         | SMALLINT, NOT NULL, default 90 | Match duration (>=0)          |
| stadium          | VARCHAR(100)  | Match venue                                  |
| CHECK (local_team_id <> away_team_id)   | Prevents same team playing itself           |
| UNIQUE (matchday_id, local_team_id, away_team_id) | Prevents duplicate matches          |

#### `event`

| Column           | Type         | Description                                  |
|------------------|--------------|----------------------------------------------|
| event_id         | SERIAL, PK   | Unique event ID                              |
| match_id         | INTEGER, NOT NULL, FK | References `core.match`               |
| event_type       | reference.event_type_enum, NOT NULL | Event type      |
| minute           | SMALLINT     | Minute of occurrence                         |
| main_player_id   | INTEGER, NOT NULL, FK | Main player in the event              |
| extra_player_id  | INTEGER, FK  | Secondary player involved                    |
| team_id          | INTEGER, FK  | Team related to event                        |

#### `participation`

| Column           | Type                       | Description                               |
|------------------|----------------------------|-------------------------------------------|
| match_id         | INTEGER, NOT NULL, FK      | References `core.match`                   |
| player_id        | INTEGER, NOT NULL, FK      | References `reference.player`             |
| status           | reference.status_enum, NOT NULL | Player's match status              |
| position         | reference.position_enum, NOT NULL | Player's position                    |
| PRIMARY KEY (match_id, player_id)             | Unique player per match                   |

#### `basic_stats`

| Column              | Type        | Description                                    |
|---------------------|-------------|------------------------------------------------|
| basic_stats_id      | INTEGER, PK, auto-increment | Unique stats record            |
| match_id            | INTEGER, NOT NULL | Match played                           |
| player_id           | INTEGER, NOT NULL | Player                                  |
| minutes             | INTEGER, NOT NULL | Minutes played                          |
| goals               | SMALLINT, >=0     | Goals scored                            |
| assists             | SMALLINT, >=0     | Assists                                 |
| touches             | SMALLINT, >=0     | Touches                                 |
| passes_total        | SMALLINT, >=0     | Total passes                            |
| passes_completed    | SMALLINT, >=0     | Completed passes                        |
| ball_recoveries     | SMALLINT, >=0     | Recoveries                              |
| possessions_lost    | SMALLINT, >=0     | Lost possessions                        |
| aerial_duels_won    | SMALLINT, >=0     | Aerial duels won                        |
| aerial_duels_total  | SMALLINT, >=0     | Aerial duels attempted                  |
| ground_duels_won    | SMALLINT, >=0     | Ground duels won                        |
| ground_duels_total  | SMALLINT, >=0     | Ground duels attempted                  |
| UNIQUE (match_id, player_id)            | One stats record per player per match   |
| FK (match_id, player_id) → core.participation | Ensures stats only for participating players |

---

## Triggers

- **Automatic matchdays insertion**
  
  After a new season is created in `core.season`, the trigger `trg_insert_matchdays` automatically calls the procedure `core.insert_matchdays`, creating all matchdays based on the competition's default number of rounds.  
  This ensures every season always has the correct number of matchdays upon insertion.

---

## Procedures

Procedures are used for **controlled insertion** of records, ensuring data integrity and preventing duplicates.

- **`core.insert_season(p_season_label, p_competition_id)`**  
  Inserts a new season with a given label for a specific competition.  
  - Validates uniqueness (no duplicate seasons for a competition)
  - Ensures non-empty season label and valid competition ID

- **`core.insert_matchdays(p_season_id, p_total_matchdays)`**  
  Bulk-inserts the specified number of matchdays for a given season.  
  - Used by the trigger and can be called manually

---

## Functions

Functions provide **data retrieval** and utility helpers for analytics and system operations.

- **`core.get_season_id(p_season_label, p_competition_id)`**  
  Returns the ID of a season given its label and competition.

- **`core.get_matchday_ids_in_season(p_season_id)`**  
  Returns all matchday IDs and numbers for a given season.

- **`core.count_matchdays(p_season_id)`**  
  Returns the total number of matchdays in a season.

- **`core.get_matches_in_matchdays(p_matchday_ids)`**  
  Returns the match IDs for a list of matchday IDs.

- **`core.get_player_ids_by_match_ids(p_match_ids)`**  
  Returns distinct player IDs for the given match IDs (from participation).

- **`core.match_has_events(p_match_id)`**  
  Returns a boolean indicating if the match has any events registered.

- **`core.get_participations_by_season(p_season_id)`**  
  Returns the match and player IDs for participations in a season  
  where basic stats have **not yet** been recorded.

- **`core.get_basic_stats_keys_by_season(p_season_id)`**  
  Returns match and player IDs for all basic stats recorded in a season.

- **`core.get_basic_stats_ids_by_season(p_season_id)`**  
  Returns detailed basic stats IDs, match IDs, player IDs, and positions for a season.

---


---

### Example Usage

```sql
-- Insert a new season for a competition
CALL core.insert_season('2024_2025', 5);

-- Insert matchdays automatically for a new season (done by trigger)
-- Or manually:
CALL core.insert_matchdays(9, 38);

-- Retrieve all matchdays in a season
SELECT * FROM core.get_matchday_ids_in_season(9);

-- Get all players who participated in matches in a season but lack basic stats
SELECT * FROM core.get_participations_by_season(9);

-- Get basic stats keys by season
SELECT * FROM core.get_basic_stats_keys_by_season(9);
