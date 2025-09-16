from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection

def get_engine(url: str | None = None) -> Engine:
    url = url or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL no configurado")
    engine = create_engine(url, future=True, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine

@contextmanager
def connect(engine: Engine) -> Iterator[Connection]:
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()
