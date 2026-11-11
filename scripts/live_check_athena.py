"""Live check for AthenaExecutor against real Athena. Run it yourself, as the app identity:

    uv run python -m scripts.live_check_athena

Prints query IDs, columns, rows (counts only), timings and bytes scanned. Never
prints SQL, parameters or account details. Exits 1 if any of checks 1-3 fail;
check 4 only records what happens.
"""

import sys
from pathlib import Path

import boto3

from app.config import settings
from app.services.athena import (
    AthenaExecutor,
    AthenaExecutorError,
    AthenaQueryFailedError,
    QueryResult,
)

CHECKPOINT_SQL = (
    Path(__file__).resolve().parent.parent / "sql" / "checks" / "checkpoint1_a1c_gap_silver.sql"
)
BRONZE_SQL = "SELECT count(*) FROM caregap_bronze.patients"
GENDER_SQL = "SELECT count(*) AS n FROM caregap_silver.patients WHERE gender = ?"
QUOTED_PARAM = "'x'' OR ''1''=''1'"
RAW_PARAM = "'x' OR '1'='1'"


def _print_result(label: str, result: QueryResult) -> None:
    print(
        f"[{label}] query_id={result.query_execution_id} columns={result.columns} "
        f"rows={result.rows} truncated={result.truncated} total_ms={result.total_ms} "
        f"data_scanned_bytes={result.data_scanned_bytes}"
    )


def _print_error(label: str, exc: AthenaExecutorError) -> None:
    line = f"[{label}] error code={exc.code} query_id={exc.query_execution_id}"
    if isinstance(exc, AthenaQueryFailedError):
        line += f" error_category={exc.error_category} error_type={exc.error_type}"
    print(line)


def _verdict(label: str, ok: bool) -> int:
    print(f"[{label}] {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    executor = AthenaExecutor(boto3.client("athena", region_name=settings.AWS_REGION))
    failures = 0

    label = "1 checkpoint (expect 24, 0)"
    try:
        result = executor.run_query(CHECKPOINT_SQL.read_text())
        _print_result(label, result)
        ok = result.columns == ["gap_patients", "never_tested"] and result.rows == [["24", "0"]]
    except AthenaExecutorError as exc:
        _print_error(label, exc)
        ok = False
    failures += _verdict(label, ok)

    label = "2 bronze denied (expect QUERY_FAILED)"
    try:
        result = executor.run_query(BRONZE_SQL)
        _print_result(label, result)
        ok = False
    except AthenaQueryFailedError as exc:
        _print_error(label, exc)
        ok = True
    except AthenaExecutorError as exc:
        _print_error(label, exc)
        ok = False
    failures += _verdict(label, ok)

    label = "3 quoted param (expect n = 0)"
    try:
        result = executor.run_query(GENDER_SQL, [QUOTED_PARAM])
        _print_result(label, result)
        ok = result.rows == [["0"]]
    except AthenaExecutorError as exc:
        _print_error(label, exc)
        ok = False
    failures += _verdict(label, ok)

    label = "4 raw param (record only)"
    try:
        result = executor.run_query(GENDER_SQL, [RAW_PARAM])
        _print_result(label, result)
    except AthenaExecutorError as exc:
        _print_error(label, exc)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
