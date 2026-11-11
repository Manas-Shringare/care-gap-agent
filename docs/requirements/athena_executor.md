# Athena executor: requirements (Tier A3, step S1)

Written by me (Manas) for Claude Code. Plan mode first; I approve every edit.

## Goal
A small module that runs **one read-only query** in Athena as the app identity
(`prompttrace-local-dev`) and returns rows, with hard limits. Nothing else:
no SQL guard, no tools, no agent, no views. Those are separate steps.

## Where
- Module: `app/services/athena.py` (next to `app/services/bedrock.py`; both wrap one AWS service).
- Tests: `tests/test_athena_executor.py`.
- Follow the error-wrapping pattern of `TracePersistenceError` in `app/repositories/trace_repository.py`
  (carry the AWS error code, never the message) and its Stubber tests in `tests/test_trace_repository.py`.
- No new dependencies (boto3 and botocore's Stubber are already installed).

## Interface
- `AthenaExecutor(client, *, timeout_s=30.0, max_rows=1000, sleep=time.sleep, clock=time.monotonic)`
  - `client` is a boto3 Athena client, passed in (never created inside the class).
- `run_query(sql: str, params: list[str] | None = None) -> QueryResult`
- `QueryResult` (frozen dataclass): `query_execution_id: str`, `columns: list[str]`,
  `rows: list[list[str | None]]`, `truncated: bool`, `data_scanned_bytes: int`, `total_ms: int`.

## Fixed settings (module constants, never caller-supplied)
- `WORKGROUP = "caregap"`: the only workgroup the app's IAM policy allows.
- `QueryExecutionContext = {"Catalog": "AwsDataCatalog", "Database": "caregap_silver"}`.
  Callers must still fully qualify every table name.
- **Do not pass `ResultConfiguration` or `OutputLocation`.** The workgroup is enforced and
  decides where results go. The app never needs the bucket name.

## Parameters
- `params` is passed unchanged as `ExecutionParameters`. Omit the key when `params` is None or empty.
- Each parameter is already a SQL literal (strings in single quotes). The executor does
  **not** build, quote, escape or format SQL. Never use f-strings or `%` to put values into SQL.
- Athena allows `?` placeholders only in the WHERE clause.

## Polling
- Call `GetQueryExecution` until the state is `SUCCEEDED`, `FAILED` or `CANCELLED`.
  `QUEUED` and `RUNNING` mean keep polling.
- Interval starts at 0.25 s and doubles up to 2 s, using the injected `sleep`.
- If `timeout_s` passes (measured with the injected `clock`), call `StopQueryExecution`
  with the query ID, then raise `AthenaTimeoutError`. If the stop call itself fails,
  still raise `AthenaTimeoutError`.

## Results (only after SUCCEEDED)
- Column names from `ResultSetMetadata.ColumnInfo[].Name`.
- Paginate `GetQueryResults` with `NextToken` (`MaxResults=1000`).
  The **first row of the first page is the header**: skip it.
- A cell without `VarCharValue` is SQL NULL → `None`.
- Stop at `max_rows`. Set `truncated=True` if any row was left out. Don't fetch more pages after the cap.
- `data_scanned_bytes` from `Statistics.DataScannedInBytes`;
  `total_ms` from `Statistics.TotalExecutionTimeInMillis`.

## Errors
- One base class `AthenaExecutorError(code, query_execution_id | None)`, with:
  - `AthenaQueryFailedError`: state FAILED; carries `Status.AthenaError.ErrorCategory` and `ErrorType`.
  - `AthenaQueryCancelledError`: state CANCELLED.
  - `AthenaTimeoutError`: our timeout.
  - `AthenaClientError`: wraps `ClientError` (code = AWS error code, e.g. `AccessDeniedException`)
    and `BotoCoreError` (code = the exception class name).
- Catch `ClientError` and `BotoCoreError` only. No `except Exception`.
- **Never** put AWS error messages or `StateChangeReason` into an exception message or a log
  line. They contain the account ID and the user ARN. An admin looks up the query ID instead.
- Two ways Athena denies (both seen live on Nov 10), both must be handled:
  1. Workgroup not allowed → `AccessDeniedException` from `StartQueryExecution`.
  2. Database/table not allowed → the query is accepted, then ends `FAILED`.

## Logging
- Use the logger setup in `app/logging.py` (don't configure logging in the module).
- One INFO line per query: query ID, final state, `total_ms`, `data_scanned_bytes`, row count, `truncated`.
- Never log SQL, parameters, rows, AWS error messages or `StateChangeReason`.

## Unit tests (Stubber; no real AWS, no real sleeping)
1. Happy path: QUEUED → RUNNING → SUCCEEDED, one page; header skipped; columns and stats correct.
2. Two pages joined via `NextToken`.
3. Row cap: `truncated=True`, and no page is fetched after the cap.
4. FAILED → `AthenaQueryFailedError` with category and type; the reason text appears nowhere in the error.
5. CANCELLED → `AthenaQueryCancelledError`.
6. Timeout (fake clock) → `StopQueryExecution` called with the right ID, then `AthenaTimeoutError`;
   also when `StopQueryExecution` itself raises `ClientError`.
7. `AccessDeniedException` on start → `AthenaClientError(code="AccessDeniedException")`; no polling call.
8. The start request has `WorkGroup="caregap"` and the context database, and **no** `ResultConfiguration`.
   `ExecutionParameters` is passed through exactly, or omitted when there are no params.
9. A NULL cell becomes `None`.
10. `BotoCoreError` during polling → `AthenaClientError`.
11. Exactly `max_rows` rows and no more → `truncated=False` (the cap is not an off-by-one).

## Live check (I run this myself, as the app identity; Claude Code does not call AWS)
A script `scripts/live_check_athena.py` that creates `boto3.client("athena", region_name="us-east-1")`
(or the region from `app/config.py`, if it defines one), then:
1. Runs the query in `sql/checks/checkpoint1_a1c_gap_silver.sql` → one row with columns
   `gap_patients`, `never_tested` = **24**, **0** (the same answer as Checkpoint 1 and the Python ground truth).
2. Runs `SELECT count(*) FROM caregap_bronze.patients` → `AthenaQueryFailedError`.
3. Runs `SELECT count(*) AS n FROM caregap_silver.patients WHERE gender = ?` with param
   `'x'' OR ''1''=''1'` (a correctly quoted literal) → `n = 0`.
4. The same query with the raw param `'x' OR '1'='1'` → **record what happens**.
    **Result (Nov 10):** `QUERY_FAILED`, `TYPE_MISMATCH: Logical expression term must evaluate to a boolean`.
   Athena parses each parameter as a SQL expression (`gender = ('x' OR '1'='1')`): it can't change the
   surrounding query, but it is not inert data. Callers must build parameters in code from validated typed values.
   `n = 0` or an error = parameters are treated as one value. `n = 1163` = they're spliced in as SQL,
   and the tool layer must validate every value (it will anyway). This is a learning either way.
Print the query ID, rows, ms and bytes. No SQL and no account details.

## Out of scope
SQL guard, tools, views, panels, retries/backoff for throttling (Tier B), async, Lambda.

## Done when
`uv run pytest` passes (all old tests + the 11 new), `ruff check` is clean,
and my live check prints 24 for the checkpoint query.