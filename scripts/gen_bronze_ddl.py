#!/usr/bin/env python3
"""Generate Athena DDL for the bronze Synthea tables from the CSV headers.

Usage: python3 scripts/gen_bronze_ddl.py <csv_dir> [out_dir]

Every column is STRING; types are cast later in the silver CTAS.
The bucket is a placeholder (__DATA_BUCKET__) so no bucket name is committed.
"""
import csv
import re
import sys
from pathlib import Path

TABLES = [
    "allergies", "careplans", "conditions", "encounters", "immunizations",
    "medications", "observations", "organizations", "patients", "procedures",
    "providers",
]


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    csv_dir = Path(sys.argv[1])
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "sql/bronze")
    out.mkdir(parents=True, exist_ok=True)
    (out / "00_database.sql").write_text(
        "CREATE DATABASE IF NOT EXISTS caregap_bronze\n"
    )
    for t in TABLES:
        with open(csv_dir / f"{t}.csv", newline="", encoding="utf-8-sig") as fh:
            header = [h.strip().lower() for h in next(csv.reader(fh))]
        bad = [h for h in header if not re.fullmatch(r"[a-z0-9_]+", h)]
        if bad or len(set(header)) != len(header):
            sys.exit(f"{t}: bad or duplicate column names: {bad or header}")
        cols = ",\n".join(f"  `{h}` string" for h in header)
        ddl = (
            f"CREATE EXTERNAL TABLE caregap_bronze.{t} (\n{cols}\n)\n"
            "ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'\n"
            "WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '\"', "
            "'escapeChar' = '\\\\')\n"
            f"LOCATION 's3://__DATA_BUCKET__/bronze/{t}/'\n"
            "TBLPROPERTIES ('skip.header.line.count' = '1')\n"
        )
        (out / f"{t}.sql").write_text(ddl)
        print(f"{t}: {len(header)} columns")


if __name__ == "__main__":
    main()
