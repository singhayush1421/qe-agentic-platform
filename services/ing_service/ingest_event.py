
from datetime import datetime

import psycopg2
from loguru import logger
from psycopg2.extras import Json
from psycopg2.pool import SimpleConnectionPool

from .config import get_db_config


def ensure_schema() -> None:
    if not db_pool:
        return

    conn = None
    try:
        conn = psycopg2.connect(**get_db_config())
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    correlation_id TEXT,
                    tenant_id TEXT,
                    event_type TEXT,
                    change_type TEXT,
                    source_system TEXT,
                    environment TEXT,
                    application TEXT,
                    service TEXT,
                    timestamp TIMESTAMP,
                    materiality TEXT,
                    requires_impact_analysis BOOLEAN,
                    repository_name TEXT,
                    repository_owner TEXT,
                    branch TEXT,
                    commit_id TEXT,
                    author TEXT,
                    files_changed_count INTEGER,
                    total_additions INTEGER,
                    total_deletions INTEGER,
                    payload JSONB
                )
                """
            )
        conn.commit()
        logger.info("✅ Database schema ready")
    except Exception as exc:
        logger.warning(f"⚠️ Could not initialize DB schema: {exc}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


# -----------------------------------
# ✅ CREATE CONNECTION POOL (GLOBAL)
# -----------------------------------
try:
    db_config = get_db_config()
    db_pool = SimpleConnectionPool(minconn=1, maxconn=10, **db_config)
    logger.info(
        f"✅ PostgreSQL connection pool created for {db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    ensure_schema()

except Exception as e:
    logger.error(f"❌ Failed to create DB pool: {e}")
    db_pool = None


# -----------------------------------
# ✅ INSERT EVENT INTO DB
# -----------------------------------
def insert_event(event: dict):

    if not db_pool:
        logger.error("❌ DB pool not initialized")
        return

    conn = None

    try:
        # ✅ Get connection
        conn = db_pool.getconn()
        cur = conn.cursor()

        # ✅ Safe timestamp conversion (ISO → PostgreSQL TIMESTAMP)
        timestamp_value = None
        raw_ts = event.get("timestamp")

        if raw_ts:
            try:
                timestamp_value = datetime.fromisoformat(
                    raw_ts.replace("Z", "+00:00")
                )
            except Exception:
                logger.warning("⚠️ Timestamp parsing failed, storing NULL")

        # ✅ SQL INSERT
        query = """
        INSERT INTO events (
            event_id,
            correlation_id,
            tenant_id,
            event_type,
            change_type,
            source_system,
            environment,
            application,
            service,
            timestamp,
            materiality,
            requires_impact_analysis,
            repository_name,
            repository_owner,
            branch,
            commit_id,
            author,
            files_changed_count,
            total_additions,
            total_deletions,
            payload
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING;
        """

        # ✅ Execute insert
        cur.execute(query, (
            event.get("event_id"),
            event.get("correlation_id"),
            event.get("tenant_id"),
            event.get("event_type"),
            event.get("change_type"),
            event.get("source_system"),
            event.get("environment"),
            event.get("application"),
            event.get("service"),
            timestamp_value,
            event.get("classification", {}).get("materiality"),
            bool(event.get("classification", {}).get("requires_impact_analysis", False)),
            event.get("repository", {}).get("name"),
            event.get("repository", {}).get("owner"),
            event.get("change_reference", {}).get("branch"),
            event.get("change_reference", {}).get("commit_id"),
            event.get("change_reference", {}).get("author"),
            event.get("metadata", {}).get("files_changed_count", 0),
            event.get("metadata", {}).get("total_additions", 0),
            event.get("metadata", {}).get("total_deletions", 0),
            Json(event)  # ✅ full payload stored safely
        ))

        conn.commit()

        logger.info(
            f"✅ Event stored: {event.get('change_reference', {}).get('commit_id')}"
        )

    except Exception as e:
        logger.error(f"❌ DB insert failed: {e}")

        if conn:
            conn.rollback()

    finally:
        # ✅ Always return connection to pool
        if conn:
            db_pool.putconn(conn)


# -----------------------------------
# ✅ CLOSE POOL (GRACEFUL SHUTDOWN)
# -----------------------------------
def close_pool():
    if db_pool:
        db_pool.closeall()
        logger.info("✅ DB pool closed")
