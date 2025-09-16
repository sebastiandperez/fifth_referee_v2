from __future__ import annotations

from abc import ABC
from typing import Protocol, Sequence, runtime_checkable

from .models import (
    # IDs
    TeamId, PlayerId, CompetitionId, SeasonId, MatchdayId, MatchId,
    # Entidades
    Team, Player, Competition, Season, Matchday, Match, Event,
    # DTOs / agregados de lectura
    StandingRow, TeamFormRow, TeamSplit, ScorerRow, AssisterRow, KeeperKPI,
)

# =========================
# Excepciones de dominio
# =========================

class DomainError(Exception):
    """Error base del dominio (no depende de infraestructura)."""

class NotFoundError(DomainError):
    """Recurso solicitado no existe (p. ej. season_id inválido)."""

class DataSourceError(DomainError):
    """
    Error al obtener datos desde la fuente (p. ej. SQL mal formado, ruptura de contrato).
    Las capas superiores pueden registrar/mostrar un mensaje genérico.
    """

class TransientError(DataSourceError):
    """
    Error transitorio (timeouts de DB, conexiones puntuales).
    La aplicación puede decidir reintentar la operación.
    """


# =========================
# Ports (interfaces)
# =========================

@runtime_checkable
class CompetitionPort(Protocol):
    """Catálogo de competiciones y sus temporadas."""

    def list_competitions(self) -> Sequence[Competition]:
        """
        Devuelve todas las competiciones visibles para la aplicación.
        """

    def list_seasons(self, competition_id: CompetitionId) -> Sequence[Season]:
        """
        Devuelve las temporadas de una competición.
        Debe lanzar NotFoundError si la competición no existe.
        """


@runtime_checkable
class SeasonPort(Protocol):
    """Navegación y metadatos de temporada (season → matchdays, teams)."""

    def get_season(self, season_id: SeasonId) -> Season:
        """
        Devuelve la temporada.
        NotFoundError si no existe.
        """

    def list_matchdays(self, season_id: SeasonId) -> Sequence[Matchday]:
        """
        Devuelve las jornadas de la temporada, ordenadas por matchday_number.
        """

    def list_teams(self, season_id: SeasonId) -> Sequence[Team]:
        """
        Devuelve los equipos inscritos en la temporada.
        Si la fuente no tiene esta vista, puede armarse vía registry.*; NotFoundError si la season no existe.
        """


@runtime_checkable
class MatchPort(Protocol):
    """Acceso a partidos por temporada o por equipo."""

    def list_matches_by_season(
        self, season_id: SeasonId, *, only_finalized: bool = True
    ) -> Sequence[Match]:
        """
        Lista de partidos de la temporada; si only_finalized=True, excluye los que no tengan marcador completo.
        """

    def list_matches_for_team(
        self, season_id: SeasonId, team_id: TeamId, *, only_finalized: bool = True
    ) -> Sequence[Match]:
        """
        Lista de partidos de la temporada en los que participa team_id (local o visitante).
        Orden cronológico recomendado.
        """


@runtime_checkable
class StandingsPort(Protocol):
    """Cálculo/obtención de tabla de posiciones (lectura agregada)."""

    def get_standings(self, season_id: SeasonId) -> Sequence[StandingRow]:
        """
        Devuelve filas agregadas por equipo (MP, Pts, GF, GA, GD) ya listas para ordenar por Pts→GD→GF.
        Debe ignorar partidos sin marcador (no finalizados).
        """


@runtime_checkable
class TeamAnalyticsPort(Protocol):
    """Consultas de rendimiento de equipos."""

    def get_team_form(
        self, season_id: SeasonId, team_id: TeamId, *, n: int = 5
    ) -> Sequence[TeamFormRow]:
        """
        Últimos N partidos del equipo en la temporada, con resultado W/D/L desde su perspectiva.
        Debe excluir partidos sin marcador.
        """

    def get_team_splits(self, season_id: SeasonId, team_id: TeamId) -> TeamSplit:
        """
        Agregados de local/visitante (PPG, GF, GA, GD) para la temporada.
        """


@runtime_checkable
class PlayerStatsPort(Protocol):
    """Rankings y métricas por jugador."""

    def get_top_scorers(self, season_id: SeasonId, *, top: int = 10) -> Sequence[ScorerRow]:
        """
        Ranking de goleadores por temporada.
        """

    def get_top_assisters(self, season_id: SeasonId, *, top: int = 10) -> Sequence[AssisterRow]:
        """
        Ranking de asistentes por temporada.
        """

    def get_keeper_kpis(self, season_id: SeasonId, *, top: int = 10) -> Sequence[KeeperKPI]:
        """
        KPIs de porteros (saves, goals_prevented si aplica, goles encajados) por temporada.
        """


@runtime_checkable
class EventPort(Protocol):
    """Eventos de partido (cronología de goles, tarjetas, cambios, etc.)."""

    def list_events(self, match_id: MatchId) -> Sequence[Event]:
        """
        Devuelve los eventos del partido, ordenados por minuto/orden natural.
        """


# Opcional: un marcador común para identificar puertos (útil para DI)
class Port(ABC):
    """Marcador abstracto para puertos; no define métodos. Úsalo si quieres un registro central de adapters."""
    pass


__all__ = [
    # Exceptions
    "DomainError", "NotFoundError", "DataSourceError", "TransientError",
    # Marker
    "Port",
    # Ports
    "CompetitionPort", "SeasonPort", "MatchPort",
    "StandingsPort", "TeamAnalyticsPort",
    "PlayerStatsPort", "EventPort",
]
