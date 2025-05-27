# Data Loading Flow

This document describes the **recommended order for loading football data into the database** using the modular loaders in this repository.  
Following this flow ensures all foreign key dependencies are respected and that your data is always inserted correctly and efficiently.

---

## **Recommended Loading Sequence**

1. **Teams**  
   - Insert all teams and their associations with seasons.  
   - Loader: `TeamLoader`
2. **Players**  
   - Insert all players and their registrations (team-player relations).  
   - Loader: `PlayerLoader`
3. **Matches**  
   - Insert match records, player participations (appearances), and basic stats.  
   - Loader: `MatchLoader`
4. **Detailed Stats**  
   - Insert advanced player stats: goalkeepers, defenders, midfielders, forwards.  
   - Loader: `StatsLoader`

---

## **Why This Order?**

- **Teams must be loaded first** because both matches and players reference teams.
- **Players and their registrations** come next, as participations and stats require both player and team existence.
- **Matches** can only be loaded after teams and players, since a match references teams and participations link players and matches.
- **Detailed stats** depend on the existence of matches and players, as they reference participation and player IDs.

---

## **Summary Table**

| Step  | Loader       | What it inserts                                | Depends on |
|-------|--------------|------------------------------------------------|------------|
| 1     | TeamLoader   | Teams, Season-Teams                            | —          |
| 2     | PlayerLoader | Players, Team-Players                          | Teams      |
| 3     | MatchLoader  | Matches, Participations, Basic Stats           | Teams, Players |
| 4     | StatsLoader  | Goalkeeper/Defender/Midfielder/Forward Stats   | Matches, Players, Basic Stats |

---

## **Example Usage**

```python
# Open connection ONCE
conn = psycopg2.connect(...)

team_loader = TeamLoader(conn)
player_loader = PlayerLoader(conn)
match_loader = MatchLoader(conn)
stats_loader = StatsLoader(conn)

team_loader.insert_team_block(team_df, season_team_df)
player_loader.insert_player_block(player_df, team_player_df)
match_loader.insert_match_block(match_df, participation_df, basic_stats_df)
stats_loader.insert_stats_block(goalkeeper_df, defender_df, midfielder_df, forward_df)

conn.close()
