"""Single-table SQLite storage; one transaction per validated batch."""

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from models import CityStatisticBatch

DB_PATH = Path(
    os.environ.get(
        "CITY_STATISTICS_DB",
        Path(__file__).resolve().parent.parent / "data" / "city_statistics.db",
    )
)


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("""CREATE TABLE IF NOT EXISTS city_statistics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city_name TEXT NOT NULL, year INTEGER NOT NULL,
        indicator_code TEXT NOT NULL, indicator_name TEXT NOT NULL, dimension TEXT,
        value REAL, value_text TEXT, unit TEXT NOT NULL,
        scope TEXT, time_point TEXT, value_origin TEXT,
        source_name TEXT NOT NULL, source_url TEXT NOT NULL, source_quote TEXT NOT NULL,
        status TEXT, raw_json TEXT, created_at TEXT NOT NULL,
        UNIQUE(city_name, year, indicator_code, source_url))""")
    conn.commit()
    return conn


def save_city_statistics(records: list[dict]) -> dict:
    batch = CityStatisticBatch.model_validate({"records": records})
    written = 0
    with closing(init_db()) as conn, conn:
        for record in batch.records:
            item = record.model_dump()
            old = conn.execute(
                "SELECT scope,time_point,unit,value_origin FROM city_statistics WHERE city_name=? AND year=? AND indicator_code=? AND source_url=?",
                (
                    record.city_name,
                    record.year,
                    record.indicator_code,
                    record.source_url,
                ),
            ).fetchone()
            if old and old != (
                record.scope,
                record.time_point,
                record.unit,
                record.value_origin,
            ):
                raise ValueError(
                    "同城市/年份/指标/来源已有不同口径、时点、单位或数据类型，拒绝覆盖；请先核实"
                )
            columns = list(item) + ["raw_json", "created_at"]
            values = list(item.values()) + [
                json.dumps(item, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ]
            # Columns come exclusively from the validated model, never user SQL.
            updates = ",".join(f"{key}=excluded.{key}" for key in item)
            conn.execute(
                f"INSERT INTO city_statistics ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)}) "
                f"ON CONFLICT(city_name,year,indicator_code,source_url) DO UPDATE SET {updates},raw_json=excluded.raw_json",
                values,
            )
            written += 1
    return {"success": True, "written_count": written, "database": str(DB_PATH)}


def query_city_statistics(
    city_name: str | None = None, year: int | None = None, limit: int = 100
) -> dict:
    if not 1 <= limit <= 500:
        raise ValueError("limit必须在1到500之间")
    with closing(init_db()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM city_statistics WHERE (? IS NULL OR city_name=?) AND (? IS NULL OR year=?) ORDER BY year DESC,city_name,indicator_code LIMIT ?",
            (city_name, city_name, year, year, limit),
        ).fetchall()
    return {"records": [dict(row) for row in rows], "count": len(rows)}
