# Fifth Referee v2 — Documentation Index

This is the official documentation for the **Fifth Referee v2** data platform.  
It includes the full database architecture, user roles, JSON input structure, and references for internal components such as functions and views.

---

## System Architecture

- [Database Schemas Overview](architecture.md)  
  → Explains the purpose and relationships between schemas like `core`, `reference`, `stats`, and `registry`.

- [User Roles and Permissions](roles.md)  
  → Describes access levels, workflows, and privileges for different system users.

---

## JSON Input Format

- [/json/json_structure.md](json/json_structure.md)  
  → Explanation of the structure and rationale behind the clean match JSON format.

- [/json/sample.json](json/sample.json)  
  → Sample file using fictional data to demonstrate a valid clean match JSON format.

---

## Database Documentation

### reference/
- [player](db/reference/player.md)
- [team](db/reference/team.md)
- [competition](db/reference/competition.md)
- [enums](db/reference/enums.md)
- [logic] (db/reference/reference_logic.md)

### core/
- [season](db/core/season.md)
- [matchday](db/core/matchday.md)
- [match](db/core/match.md)
- [participation](db/core/participation.md)
- [basic_stats](db/core/basic_stats.md)
- [logic] (db/core/core_logic.md) 

### stats/
- [goalkeeper_stats](db/stats/goalkeeper_stats.md)
- [defender_stats](db/stats/defender_stats.md)
- [midfielder_stats](db/stats/midfielder_stats.md)
- [forward_stats](db/stats/forward_stats.md)
- [logic](db/stats/stats_logic.md)

### registry/
- [season_team](db/registry/season_team.md)
- [team_player](db/registry/team_player.md)
- [logic](db/registry/registry_logic.md)

---

## Notes

- This documentation evolves alongside the project.
- All contributions must follow naming conventions and schema boundaries as defined in `architecture.md`.
