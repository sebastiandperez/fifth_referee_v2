from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

api = FastAPI(title="Fifth Referee API", version="1.0")

# CORS (ajusta orígenes si hace falta)
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8050", "http://localhost:8050", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMPORTA routers *después* de crear `api` (evita import circular)
from .routers import (
    discovery,
    seasons,
    teams,
    players,
    matchdays,
    matches,
    standings,
    stats,
    events,
)

# Monta routers con prefijo /v1
api.include_router(discovery.router, prefix="/v1")
api.include_router(seasons.router,   prefix="/v1")
api.include_router(teams.router,     prefix="/v1")
api.include_router(players.router,   prefix="/v1")
api.include_router(matchdays.router, prefix="/v1")
api.include_router(matches.router,   prefix="/v1")
api.include_router(standings.router, prefix="/v1")
api.include_router(stats.router,     prefix="/v1")
api.include_router(events.router,    prefix="/v1")
