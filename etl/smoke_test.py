from etl.db.tx import db_connection, transaction

def run_smoke() -> None:
    print("Running ETL smoke test…")
    with db_connection() as conn, transaction(conn):
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
    if row and row["ok"] == 1:
        print("✅ DB connection works and returned SELECT 1")
    else:
        raise RuntimeError(f"Unexpected response: {row}")

if __name__ == "__main__":
    run_smoke()
