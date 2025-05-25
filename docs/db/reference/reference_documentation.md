# fifth_referee_v2 Database Documentation

## Schema: reference

### Overview
The `reference` schema contains core reference data for football analytics, such as teams, players, and competitions. Entities in this schema are stable and atomic, serving as foundational references for other modules.

---

### Data Types

#### `continent_enum`
Enumeration of continents for classifying competitions:
- `Africa`
- `Asia`
- `Europe`
- `North America`
- `South America`
- `Australia`
- `International`

#### `status_enum`
Player participation status in a match:
- `starter`: Player started the match.
- `substitute`: Entered as a substitute.
- `unused`: Was on the bench, did not play.
- `other`: Undefined status.

#### `position_enum`
Football positions:
- `GK`: Goalkeeper
- `DF`: Defender
- `MF`: Midfielder
- `FW`: Forward
- `MNG`: Manager

#### `event_type_enum`
Types of events recorded in a match:
- `Substitution`
- `Yellow card`
- `Red card`
- `Woodwork`
- `Goal`
- `Own goal`
- `Penalty`
- `Penalty missed`
- `Disallowed goal`

---

### Tables

#### `competition`
Stores football competition details.

| Column               | Type                       | Description                            |
|----------------------|---------------------------|----------------------------------------|
| `competition_id`     | SMALLINT (PK, auto-incr.) | Unique competition identifier          |
| `current_champion_id`| SMALLINT (FK, nullable)   | Current champion team (optional)       |
| `competition_name`   | VARCHAR, UNIQUE, NOT NULL | Name of the competition                |
| `default_matchdays`  | SMALLINT, NOT NULL        | Default number of matchdays (default 38)|
| `is_international`   | BOOLEAN, NOT NULL         | Whether the competition is international|
| `continent`          | continent_enum, NOT NULL  | Continent for the competition          |

#### `team`
Stores basic team information.

| Column         | Type                    | Description                 |
|----------------|------------------------|-----------------------------|
| `team_id`      | INTEGER, PK            | Unique team identifier      |
| `team_name`    | VARCHAR(100), UNIQUE   | Team's name                 |
| `team_city`    | VARCHAR(25), nullable  | City of the team            |
| `team_stadium` | VARCHAR(50), nullable  | Team's stadium              |

#### `player`
Basic information for players.

| Column        | Type                | Description          |
|---------------|--------------------|----------------------|
| `player_id`   | INTEGER, PK        | Unique player ID     |
| `player_name` | VARCHAR(100), NOT NULL | Player's name    |

---

### Procedures and Functions

#### Procedures

- **`insert_competition`**:  
  Safely inserts a new competition, validating name, continent, and avoiding duplicates.

- **`insert_team`**:  
  Inserts a new team, ensuring unique name and mandatory fields.

- **`insert_player`**:  
  Adds a new player, validating uniqueness of ID and presence of name.

#### Functions

- **`get_competition_id_by_name`**:  
  Returns the competition ID given its name.

- **`get_active_competitions_by_continent`**:  
  Lists active competitions filtered by continent.

- **`get_all_team_ids`**:  
  Retrieves a list of all team IDs.

- **`get_all_player_ids`**:  
  Retrieves a list of all player IDs.

---

### Example Usage

```sql
-- Insert a new competition
CALL reference.insert_competition('Bundesliga', 'Europe', false, 38);

-- Get competition ID by name
SELECT * FROM reference.get_competition_id_by_name('La Liga');

-- List competitions in Europe
SELECT * FROM reference.get_active_competitions_by_continent('Europe');

-- Insert a team
CALL reference.insert_team(2, 'America', 'Cali', 'Palma Seca');

-- Insert a player
CALL reference.insert_player(0, 'Diego Armando Maradona');
