# -*- coding: utf-8 -*-
"""
Database Bootstrapper for Sewa Setu.
Automatically initializes tables from schema.sql and seed data on fresh deployments (e.g. Render, Railway).
"""

import os
import sys
import io
import logging

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import app as portal

logger = logging.getLogger("sewasetu.bootstrap")


def ensure_database_initialized():
    """Ensure PostgreSQL schema and baseline data exist. Safe to run on every startup."""
    try:
        conn = portal.get_db()
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'applications'")
        table_exists = cur.fetchone()[0] > 0

        if not table_exists:
            logger.info("Fresh database detected. Initializing schema.sql...")
            schema_file = os.path.join(APP_DIR, "schema.sql")
            if os.path.exists(schema_file):
                with open(schema_file, "r", encoding="utf-8") as f:
                    cur.execute(f.read())
                conn.commit()
                logger.info("Database schema initialized successfully.")

            # Load seed data if applications table is empty
            seed_file = os.path.join(os.path.dirname(APP_DIR), "seed", "seed.sql")
            if os.path.exists(seed_file):
                logger.info("Loading baseline seed data snapshot (~100k records)...")
                _load_seed_snapshot(conn, cur, seed_file)
                logger.info("Seed data loaded successfully.")
        else:
            cur.execute("SELECT count(*) FROM applications")
            count = cur.fetchone()[0]
            logger.info("PostgreSQL database verified. Current applications count: %d", count)

        cur.close()
        conn.close()
    except Exception as e:
        logger.warning("Database bootstrap check: %s", e)


def _load_seed_snapshot(conn, cur, seed_path):
    """Parses COPY FROM stdin blocks from seed.sql and streams them into PostgreSQL."""
    with open(seed_path, "r", encoding="utf-8", errors="ignore") as f:
        copy_cmd = None
        buffer = []
        for line in f:
            if line.startswith("COPY ") and "FROM stdin;" in line:
                copy_cmd = line.strip()
                buffer = []
            elif line.strip() == r"\.":
                if copy_cmd and buffer:
                    copy_stmt = copy_cmd.replace("stdin", "STDIN")
                    cur.copy_expert(copy_stmt, io.StringIO("".join(buffer)))
                    conn.commit()
                    logger.info("Loaded table partition via %s", copy_cmd.split()[1])
                copy_cmd = None
                buffer = []
            elif line.startswith("SELECT setval("):
                cur.execute(line.strip())
                conn.commit()
            elif copy_cmd:
                buffer.append(line)
