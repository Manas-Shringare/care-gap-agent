#!/usr/bin/env python3
"""Generate Athena CTAS statements that build the typed Parquet (silver) tables.

Usage: python3 scripts/gen_silver_ctas.py [bronze_ddl_dir] [out_dir]

Column names come from the committed bronze DDL (sql/bronze/), so silver can
never drift from bronze. Rules:
- every empty string becomes NULL
- dates, timestamps and numbers use a hard CAST, so one bad value fails the
  whole statement instead of silently turning into NULL
- codes, IDs and ZIPs stay strings (leading zeros, very long SNOMED codes)
- observations.value stays text; value_num is the only TRY_CAST, because
  that column mixes numbers and text by design
"""
import re
import sys
from pathlib import Path

DATE_COLS = {
    ("allergies", "start"), ("allergies", "stop"),
    ("careplans", "start"), ("careplans", "stop"),
    ("conditions", "start"), ("conditions", "stop"),
    ("patients", "birthdate"), ("patients", "deathdate"),
}
TIMESTAMP_COLS = {
    ("encounters", "start"), ("encounters", "stop"),
    ("immunizations", "date"),
    ("medications", "start"), ("medications", "stop"),
    ("observations", "date"),
    ("procedures", "start"), ("procedures", "stop"),
}
DOUBLE_COLS = {
    "base_cost", "base_encounter_cost", "total_claim_cost", "payer_coverage",
    "totalcost", "healthcare_expenses", "healthcare_coverage",
    "lat", "lon", "revenue",
}
BIGINT_COLS = {"dispenses", "utilization"}


def expr(table: str, col: str) -> str:
    v = f"NULLIF(\"{col}\", '')"
    if (table, col) in DATE_COLS:
        return f"CAST({v} AS date) AS \"{col}\""
    if (table, col) in TIMESTAMP_COLS:
        return f"CAST(from_iso8601_timestamp({v}) AS timestamp) AS \"{col}\""
    if col in DOUBLE_COLS:
        return f"CAST({v} AS double) AS \"{col}\""
    if col in BIGINT_COLS:
        return f"CAST({v} AS bigint) AS \"{col}\""
    return f"{v} AS \"{col}\""


def main() -> None:
    bronze = Path(sys.argv[1] if len(sys.argv) > 1 else "sql/bronze")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "sql/silver")

    tables = {}
    for ddl in sorted(bronze.glob("*.sql")):
        text = ddl.read_text()
        m = re.search(r"CREATE EXTERNAL TABLE caregap_bronze\.(\w+)", text)
        if m:
            tables[m.group(1)] = re.findall(r"`(\w+)` string", text)
    if len(tables) != 11:
        sys.exit(f"expected 11 bronze tables, found {len(tables)}: {sorted(tables)}")

    seen = {(t, c) for t, cols in tables.items() for c in cols}
    missing = (DATE_COLS | TIMESTAMP_COLS) - seen
    if missing:
        sys.exit(f"typed columns not in bronze DDL: {sorted(missing)}")

    out.mkdir(parents=True, exist_ok=True)
    (out / "00_database.sql").write_text(
        "CREATE DATABASE IF NOT EXISTS caregap_silver\n"
    )
    counts = []
    for table, cols in tables.items():
        select = [expr(table, c) for c in cols]
        if table == "observations":
            select.append("TRY_CAST(NULLIF(\"value\", '') AS double) AS value_num")
        body = ",\n  ".join(select)
        (out / f"{table}.sql").write_text(
            f"CREATE TABLE caregap_silver.{table}\n"
            "WITH (\n"
            "  format = 'PARQUET',\n"
            "  write_compression = 'SNAPPY',\n"
            f"  external_location = 's3://__DATA_BUCKET__/silver/{table}/'\n"
            ")\n"
            f"AS SELECT\n  {body}\n"
            f"FROM caregap_bronze.{table}\n"
        )
        counts.append(
            f"SELECT '{table}' AS t, count(*) AS n FROM caregap_silver.{table}"
        )
        print(f"{table}: {len(select)} columns")

    checks = out.parent / "checks"
    checks.mkdir(parents=True, exist_ok=True)
    (checks / "silver_counts.sql").write_text(
        " UNION ALL\n".join(counts) + "\nORDER BY t\n"
    )


if __name__ == "__main__":
    main()