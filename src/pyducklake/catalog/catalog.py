from dataclasses import dataclass
from typing import Protocol


class Catalog(Protocol):
    catalog: str


@dataclass(frozen=True)
class DuckDBCatalog(Catalog):
    catalog: str = "metadata.ducklake"


@dataclass
class SQLiteCatalog(Catalog):
    db_name: str = "metadata"

    @property
    def catalog(self) -> str:
        return f"sqlite:{self.db_name}.sqlite"


@dataclass
class PostgresCatalog(Catalog):
    dbname: str = "ducklake"
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = ""

    @property
    def catalog(self) -> str:
        dsn = f"dbname={self.dbname} host={self.host} port={self.port} user={self.user}"
        if self.password:
            dsn += f" password={self.password}"
        return f"postgres:{dsn}"
