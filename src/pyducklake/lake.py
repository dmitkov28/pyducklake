from typing import Optional

from duckdb import DuckDBPyConnection
import duckdb

from pyducklake.storage import Storage
from pyducklake.catalog import Catalog


class PyDuckLake:
    def __init__(
        self,
        storage: Storage,
        catalog: Catalog,
        lake_name: str = "ducklake",
        duckdb_conn: DuckDBPyConnection | None = None,
    ):
        self.ddb = duckdb_conn or duckdb.connect()
        self._storage = storage
        self._catalog = catalog
        self._lake = lake_name
        self._initialize()

    def _initialize(self):
        self.ddb.execute("INSTALL ducklake; INSTALL postgres; INSTALL httpfs;")
        self.ddb.execute("LOAD ducklake; LOAD postgres; LOAD httpfs;")

    def connect(self):
        self._storage.create_duckdb_secret(self.ddb)
        self.ddb.execute(
            f"""
            ATTACH 'ducklake:{self._catalog.catalog}'
            AS {self._lake} (DATA_PATH 's3://{self._storage.bucket}/');
            """,
        )

    def execute(self, query: str, params: Optional[list[object]] = None):
        return self.ddb.execute(query=query, parameters=params)

    def query(self, query: str, params: Optional[list[object]] = None):
        return self.ddb.query(query=query, params=params)

    def disconnect(self):
        self.ddb.execute(f"DETACH {self._lake}")
