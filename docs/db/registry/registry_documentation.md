# fifth_referee_v2 Database Documentation

## Schema: registry

### Overview

The `registry` schema tracks the **historical associations** between teams, players, and seasons.  
It allows you to record which teams participated in each season, and which players belonged to each team for a given season (with optional jersey numbers).  
This schema is essential for historical queries, squad analysis, and transfer histories.

---

### Main Entities and Relationships

- **season_team**:  
  Associates a team with a particular season (e.g., FC Barcelona in La Liga 2021/2022).  
  Uniqueness is enforced on (season_id, team_id).

- **team_player**:  
  Associates a player with a specific team in a specific season, optionally recording the player's jersey number.  
  Composite PK: (season_team_id, player_id).

---

### Table Summaries

#### `season_team`

| Column         | Type                      | Description                                 |
|----------------|---------------------------|---------------------------------------------|
| season_team_id | INTEGER, PK, auto-increment | Unique association record               |
| season_id      | INTEGER, NOT NULL, FK     | References `core.season`                    |
| team_id        | INTEGER, NOT NULL, FK     | References `reference.team`                 |
| UNIQUE (season_id, team_id)                | Ensures a team only appears once per season |

#### `team_player`

| Column         | Type                      | Description                                 |
|----------------|---------------------------|---------------------------------------------|
| season_team_id | INTEGER, NOT NULL, FK     | References `registry.season_team`           |
| player_id      | INTEGER, NOT NULL, FK     | References `reference.player`               |
| jersey_number  | SMALLINT                  | Player's jersey number (optional)           |
| PRIMARY KEY (season_team_id, player_id)    | Unique player-team-season assignment        |

---

## Functions

- **`registry.get_season_team_id(p_season_id, p_team_id)`**  
  Returns the `season_team_id` for a specific season and team.

- **`registry.get_season_team_ids(p_season_id, p_team_ids)`**  
  Returns a list of `season_team_id` values for a given season and set of teams.

- **`registry.get_player_ids_by_season_team_ids(p_season_team_ids)`**  
  Returns the unique player IDs associated with a list of `season_team_id` values.

- **`registry.get_team_ids_in_season(p_season_id)`**  
  Returns all team IDs associated with a specific season.

---

### Example Usage

```sql
-- Get the season_team_id for FC Barcelona in the 2021/2022 season
SELECT registry.get_season_team_id(5, 10);

-- Get all season_team_ids for a set of teams in a given season
SELECT * FROM registry.get_season_team_ids(5, ARRAY[10, 11, 12]);

-- Get all players who played for certain teams in a season
SELECT * FROM registry.get_player_ids_by_season_team_ids(ARRAY[100, 101, 102]);

-- Get all team IDs that participated in a season
SELECT * FROM registry.get_team_ids_in_season(5);
