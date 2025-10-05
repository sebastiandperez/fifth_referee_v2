from functools import lru_cache
from typing import Dict

from .connection import get_conn
from domain.ids import SeasonId, TeamId

@lru_cache(maxsize=256)
def season_team_names(season_id: int) -> Dict[int, str]:
    """
    Map team_id -> team_name for a given season, cached in-process.
    """
    sql = """
    SELECT t.team_id, t.team_name
    FROM registry.season_team st
    JOIN reference.team t USING (team_id)
    WHERE st.season_id = %s
    ORDER BY t.team_id
    """
    with get_conn() as conn:
        rows = conn.execute(sql, (int(season_id),)).fetchall()
    return {int(r["team_id"]): r["team_name"] for r in rows}
