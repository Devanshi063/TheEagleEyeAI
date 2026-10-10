"""
database.py — SQLite setup for EagleEye AI incident logs.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "eagleeye.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            camera      TEXT    NOT NULL,
            zone        TEXT    NOT NULL DEFAULT 'General',
            violation   TEXT    NOT NULL,
            confidence  REAL    NOT NULL DEFAULT 0.0,
            evidence    TEXT,
            status      TEXT    NOT NULL DEFAULT 'Open',
            alert_sent  INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()
