"""
Capa de acceso a datos del ETL.

Incluye:
- connection: creación de conexiones a PostgreSQL.
- tx: context managers para conexión y transacciones.
- etl_meta: helpers para tablas y funciones del esquema etl.*.
"""

from . import etl_meta

__all__ = ["etl_meta"]
