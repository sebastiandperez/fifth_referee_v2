from __future__ import annotations

from typing import Dict, List, Optional
from etl.config.settings import load_settings, Settings
from etl.db.tx import db_connection, transaction
from etl.db import etl_meta
from etl.discovery.discovery import discover_pending_matches, update_checkpoint
from etl.dimensions.dimensions import upsert_dimensions_for_match
from etl.transform.match_transform import process_match


def run_etl(trigger_source: str = "scheduler") -> None:
    """
    Orquesta la ejecución completa del ETL.

    Args:
        trigger_source (str): Identificador de la fuente que disparó la ejecución.
                              Ejemplos: "manual", "scheduler", "cron", etc.

    Returns:
        None. El resultado se registra en la base mediante etl.*.
    """
    settings: Settings = load_settings()

    # =====================================================
    # Bloque 0: Crear run + lock
    # =====================================================
    with db_connection() as conn, transaction(conn):
        run_id: int = etl_meta.start_run(
            conn,
            trigger_source=trigger_source,
            etl_version=settings.etl_version,
            source_context={"trigger": trigger_source},
        )

        # Intentar tomar lock para evitar doble ejecución simultánea
        lock_acquired: bool = etl_meta.acquire_etl_lock(
            conn, owner=trigger_source, run_id=run_id
        )
        if not lock_acquired:
            etl_meta.finish_run(conn, run_id, "failed", "Could not acquire ETL lock.")
            return

    # =====================================================
    # Bloque 1: Descubrir y procesar partidos
    # =====================================================
    try:
        with db_connection() as conn:
            processed: int = 0
            errors: int = 0
            max_seen_match_id: int = 0

            while True:
                pending: List[int] = discover_pending_matches(
                    conn, settings.batch_size
                )
                if not pending:
                    break

                for match_id in pending:
                    max_seen_match_id = max(max_seen_match_id, match_id)

                    try:
                        with transaction(conn):
                            etl_meta.register_match_status(
                                conn,
                                run_id,
                                match_id,
                                stage="facts",
                                status="running",
                            )

                            # =====================================================
                            # Bloque 2: Dimensiones
                            # =====================================================
                            upsert_dimensions_for_match(conn, match_id, settings=settings)

                            # =====================================================
                            # Bloque 3: Hechos
                            # =====================================================
                            counters: Dict[str, int] = process_match(
                                conn, run_id, match_id
                            )

                            etl_meta.register_match_status(
                                conn,
                                run_id,
                                match_id,
                                stage="facts",
                                status="success",
                                rows_inserted_core=counters.get(
                                    "core_inserted", 0
                                ),
                                rows_updated_core=counters.get(
                                    "core_updated", 0
                                ),
                                rows_inserted_stats=counters.get(
                                    "stats_inserted", 0
                                ),
                                rows_updated_stats=counters.get(
                                    "stats_updated", 0
                                ),
                            )
                            processed += 1

                    except Exception as e:
                        errors += 1
                        # Registrar error del partido
                        with transaction(conn):
                            etl_meta.register_match_status(
                                conn,
                                run_id,
                                match_id,
                                stage="facts",
                                status="error",
                                error_code=type(e).__name__,
                                error_message=str(e),
                            )
                            etl_meta.log_error(
                                conn,
                                run_id=run_id,
                                run_match_id=None,
                                match_id=match_id,
                                stage="facts",
                                message="Error processing match",
                                detail=str(e),
                                context={"match_id": match_id},
                            )

                # =====================================================
                # Bloque 4: Guardar checkpoint
                # =====================================================
                with transaction(conn):
                    update_checkpoint(conn, max_seen_match_id)

            # =====================================================
            # Bloque 5: Finalizar run
            # =====================================================
            final_status: str = (
                "success"
                if errors == 0
                else ("partial" if processed > 0 else "failed")
            )

            with transaction(conn):
                etl_meta.finish_run(
                    conn,
                    run_id,
                    final_status,
                    error_summary=f"processed={processed}, errors={errors}",
                )
                etl_meta.release_etl_lock(conn)

    except Exception as e:
        # =====================================================
        # Falla global del ETL
        # =====================================================
        with db_connection() as conn, transaction(conn):
            etl_meta.finish_run(conn, run_id, "failed", str(e))
            etl_meta.release_etl_lock(conn)
        raise


if __name__ == "__main__":
    # Para ejecución manual durante pruebas
    run_etl(trigger_source="manual")
