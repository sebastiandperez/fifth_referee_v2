# fifth_referee_v2 Database Documentation

## Schema: stats

### Overview

The `stats` schema stores detailed, position-specific statistics for player performance in each match.  
It extends the basic statistics recorded in the `core` schema and provides deep insights for analytical and scouting purposes.  
Each table links **one-to-one** with a record in `core.basic_stats` through the `basic_stats_id` primary/foreign key.

---

### Main Entities and Relationships

- **goalkeeper_stats**: Detailed stats for goalkeepers in a match.  
- **defender_stats**: Detailed stats for defenders in a match.  
- **midfielder_stats**: Detailed stats for midfielders in a match.  
- **forward_stats**: Detailed stats for forwards in a match.  

Each of these tables uses `basic_stats_id` as both a **primary key** and a **foreign key** referencing `core.basic_stats(basic_stats_id)`.  
This ensures only one detailed stats record per player per match, and only for valid participations recorded in the `core` schema.

---

### Table Summaries

#### `goalkeeper_stats`

| Column                 | Type     | Description                    |
|------------------------|----------|--------------------------------|
| basic_stats_id         | INTEGER, PK, FK | Link to core.basic_stats   |
| goalkeeper_saves       | SMALLINT | Saves made                    |
| saves_inside_box       | SMALLINT | Saves inside penalty box       |
| goals_conceded         | SMALLINT | Goals conceded                 |
| xg_on_target_against   | FLOAT    | Expected goals on target faced |
| goals_prevented        | FLOAT    | Goals prevented (xG-based)     |
| punches_cleared        | SMALLINT | Punches away                   |
| high_claims            | SMALLINT | High balls claimed             |
| clearances             | SMALLINT | Clearances                     |
| penalties_received     | SMALLINT | Penalties faced                |
| penalties_saved        | SMALLINT | Penalties saved                |
| interceptions          | SMALLINT | Interceptions                  |
| times_dribbled_past    | SMALLINT | Times dribbled past            |

#### `defender_stats`

| Column                     | Type     | Description                    |
|----------------------------|----------|--------------------------------|
| basic_stats_id             | INTEGER, PK, FK | Link to core.basic_stats   |
| tackles_won                | SMALLINT | Tackles won                   |
| interceptions              | SMALLINT | Interceptions                  |
| clearances                 | SMALLINT | Clearances                     |
| times_dribbled_past        | SMALLINT | Times dribbled past            |
| errors_leading_to_goal     | SMALLINT | Errors leading to goals        |
| errors_leading_to_shot     | SMALLINT | Errors leading to shots        |
| possessions_won_final_third| SMALLINT | Possessions won in final third |
| fouls_committed            | SMALLINT | Fouls committed                |
| tackles_total              | SMALLINT | Total tackles                  |

#### `midfielder_stats`

| Column                        | Type     | Description                    |
|-------------------------------|----------|--------------------------------|
| basic_stats_id                | INTEGER, PK, FK | Link to core.basic_stats   |
| expected_assists              | REAL     | Expected assists                |
| tackles_won                   | SMALLINT | Tackles won                     |
| tackles_total                 | SMALLINT | Total tackles                   |
| crosses                       | SMALLINT | Crosses completed               |
| fouls_committed               | SMALLINT | Fouls committed                 |
| fouls_suffered                | SMALLINT | Fouls suffered                  |
| expected_goals                | REAL     | Expected goals                  |
| xg_from_shots_on_target       | REAL     | xG from shots on target         |
| big_chances                   | SMALLINT | Big chances                     |
| big_chances_missed            | SMALLINT | Big chances missed              |
| big_chances_scored            | SMALLINT | Big chances scored              |
| interceptions                 | SMALLINT | Interceptions                   |
| key_passes                    | SMALLINT | Key passes                      |
| passes_in_final_third         | SMALLINT | Passes in final third           |
| back_passes                   | SMALLINT | Back passes                     |
| long_passes_completed         | SMALLINT | Long passes completed           |
| woodwork                      | SMALLINT | Hits to woodwork                |
| possessions_won_final_third   | SMALLINT | Possessions won final third     |
| times_dribbled_past           | SMALLINT | Times dribbled past             |
| dribbles_completed            | SMALLINT | Dribbles completed              |
| dribbles_total                | SMALLINT | Total dribbles                  |
| long_passes_total             | SMALLINT | Total long passes               |
| crosses_total                 | SMALLINT | Total crosses                   |
| shots_off_target              | SMALLINT | Shots off target                |
| shots_on_target               | SMALLINT | Shots on target                 |
| shots_total                   | SMALLINT | Total shots                     |

#### `forward_stats`

| Column                 | Type     | Description                    |
|------------------------|----------|--------------------------------|
| basic_stats_id         | INTEGER, PK, FK | Link to core.basic_stats   |
| expected_assists       | REAL     | Expected assists                |
| expected_goals         | REAL     | Expected goals                  |
| xg_from_shots_on_target| REAL     | xG from shots on target         |
| goals                  | SMALLINT | Goals scored                    |
| assists                | SMALLINT | Assists                         |
| shots_total            | SMALLINT | Total shots                     |
| shots_on_target        | SMALLINT | Shots on target                 |
| shots_off_target       | SMALLINT | Shots off target                |
| big_chances            | SMALLINT | Big chances                     |
| big_chances_missed     | SMALLINT | Big chances missed              |
| big_chances_scored     | SMALLINT | Big chances scored              |
| penalties_won          | SMALLINT | Penalties won                   |
| penalties_missed       | SMALLINT | Penalties missed                |
| offside                | SMALLINT | Offsides                        |
| key_passes             | SMALLINT | Key passes                      |
| dribbles_completed     | SMALLINT | Dribbles completed              |
| dribbles_total         | SMALLINT | Total dribbles                  |
| times_dribbled_past    | SMALLINT | Times dribbled past             |
| fouls_committed        | SMALLINT | Fouls committed                 |
| fouls_suffered         | SMALLINT | Fouls suffered                  |
| woodwork               | SMALLINT | Hits to woodwork                |

---

## Functions

- **`stats.get_all_registered_basic_stat_ids()`**  
  Returns all `basic_stats_id` values that are present in any of the detailed stats tables (goalkeeper, defender, midfielder, forward).  
  Useful for checking which matches/players have already been analyzed at the advanced (position-specific) level.

---

### Example Usage

```sql
-- Get all basic_stats_id with advanced stats registered
SELECT * FROM stats.get_all_registered_basic_stat_ids();
