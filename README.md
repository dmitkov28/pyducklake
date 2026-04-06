# pyducklake
[![CI](https://github.com/dmitkov28/pyducklake/actions/workflows/ci.yml/badge.svg)](https://github.com/dmitkov28/pyducklake/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue)
[![License](https://img.shields.io/github/license/dmitkov28/pyducklake)](https://github.com/dmitkov28/pyducklake/blob/main/LICENSE)

A Python client for [DuckLake](https://ducklake.select) — manage lakehouse catalogs and object storage through [DuckDB](https://duckdb.org).

## Features

- **Multiple catalog backends** — DuckDB, SQLite, or PostgreSQL for metadata storage
- **Multiple storage backends** — S3 or MinIO for data files
- **Composable** — bring your own catalog and storage, wire them together
- **Thin wrapper** — delegates to DuckDB, stays out of your way

## Installation

TODO

## Quick Start

### Local development with MinIO + SQLite

```python
from pyducklake import PyDuckLake
from pyducklake.storage import MinioStorage
from pyducklake.catalog import SQLiteCatalog

storage = MinioStorage(
    endpoint="localhost:9000",
    bucket_name="ducklake",
    user="minioadmin",
    password="minioadmin",
)
storage.create_bucket()

lake = PyDuckLake(storage=storage, catalog=SQLiteCatalog())
lake.connect()

lake.execute("CREATE TABLE ducklake.main.events (id INTEGER, name VARCHAR)")
print(lake.query("SELECT * FROM ducklake.main.events"))

lake.disconnect()
```

### Production with S3 + PostgreSQL

```python
from pyducklake import PyDuckLake
from pyducklake.storage import S3Storage
from pyducklake.catalog import PostgresCatalog

storage = S3Storage(
    bucket_name="my-data-lake",
    region="eu-west-1",
    access_key_id="...",
    secret_access_key="...",
)

catalog = PostgresCatalog(
    dbname="ducklake",
    host="pg.internal",
    port=5432,
    user="postgres",
    password="...",
)

lake = PyDuckLake(storage=storage, catalog=catalog)
lake.connect()
```

## Catalogs

The catalog stores DuckLake metadata (table definitions, snapshots, etc.).

| Class | Backend | Default |
|---|---|---|
| `DuckDBCatalog` | DuckDB file | `metadata.ducklake` |
| `SQLiteCatalog` | SQLite file | `sqlite:metadata.sqlite` |
| `PostgresCatalog` | PostgreSQL | `localhost:5432/ducklake` |

```python
from pyducklake.catalog import DuckDBCatalog, SQLiteCatalog, PostgresCatalog

DuckDBCatalog()                          # metadata.ducklake
DuckDBCatalog(catalog="my.ducklake")     # custom path

SQLiteCatalog()                          # sqlite:metadata.sqlite
SQLiteCatalog(db_name="mydb")            # sqlite:mydb.sqlite

PostgresCatalog()                        # localhost defaults
PostgresCatalog(
    dbname="mydb",
    host="pg.internal",
    port=5433,
    user="admin",
    password="secret",
)
```

## Storage

The storage backend holds the actual data files (Parquet).

| Class | Backend | Protocol |
|---|---|---|
| `MinioStorage` | MinIO | S3-compatible |
| `S3Storage` | AWS S3 | S3 |

Both implement the `Storage` protocol and can:
- `create_bucket()` — create the bucket if it doesn't exist
- `create_duckdb_secret(ddb)` — register S3 credentials with DuckDB

```python
from pyducklake.storage import MinioStorage, S3Storage

MinioStorage(
    endpoint="localhost:9000",
    bucket_name="ducklake",
    user="minioadmin",
    password="minioadmin",
)

S3Storage(
    bucket_name="my-bucket",
    region="us-east-1",
    access_key_id="...",
    secret_access_key="...",
)
```

## API

### `PyDuckLake(storage, catalog, lake_name="ducklake", duckdb_conn=None)`

| Parameter | Type | Description |
|---|---|---|
| `storage` | `Storage` | Storage backend instance |
| `catalog` | `Catalog` | Catalog backend instance |
| `lake_name` | `str` | Name for the attached DuckLake database |
| `duckdb_conn` | `DuckDBPyConnection \| None` | Optional existing DuckDB connection |

### Methods

| Method | Description |
|---|---|
| `connect()` | Register secrets and attach the DuckLake catalog |
| `execute(query, params)` | Execute a SQL statement |
| `query(query, params)` | Execute a SQL query and return results |
| `disconnect()` | Detach the DuckLake catalog |

## Development

```bash
git clone https://github.com/dmitkov28/pyducklake.git
cd pyducklake
uv sync --group dev
```

### Run tests

```bash
uv run pytest tests/ -v
```

### Run tests across Python versions

```bash
uvx --with tox-uv tox
```

### Lint

```bash
uv run ruff check src/
uv run ruff format --check src/
```

## Compatibility

- Python 3.10+
- DuckDB 1.4.x (DuckLake 0.3) — see the [DuckLake compatibility matrix](https://duckdb.org/docs/current/core_extensions/ducklake#compatibility-matrix)

## License

MIT
