from unittest.mock import MagicMock, patch

import pytest

from pyducklake.lake import PyDuckLake
from pyducklake.catalog import DuckDBCatalog, SQLiteCatalog, PostgresCatalog
from pyducklake.storage import MinioStorage, S3Storage


@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.bucket = "test-bucket"
    return storage


@pytest.fixture
def mock_catalog():
    catalog = MagicMock()
    catalog.catalog = "sqlite:metadata.sqlite"
    return catalog


class TestPyDuckLakeInit:
    @patch.object(PyDuckLake, "_initialize")
    def test_default_values(self, mock_init, mock_storage, mock_catalog):
        lake = PyDuckLake(storage=mock_storage, catalog=mock_catalog)
        assert lake._storage is mock_storage
        assert lake._catalog is mock_catalog
        assert lake._lake == "ducklake"
        assert lake.ddb is not None

    @patch.object(PyDuckLake, "_initialize")
    def test_custom_lake_name(self, mock_init, mock_storage, mock_catalog):
        lake = PyDuckLake(
            storage=mock_storage, catalog=mock_catalog, lake_name="my_lake"
        )
        assert lake._lake == "my_lake"

    @patch.object(PyDuckLake, "_initialize")
    def test_custom_duckdb_conn(self, mock_init, mock_storage, mock_catalog):
        conn = MagicMock()
        lake = PyDuckLake(storage=mock_storage, catalog=mock_catalog, duckdb_conn=conn)
        assert lake.ddb is conn


class TestPyDuckLakeConnect:
    @patch.object(PyDuckLake, "_initialize")
    def test_connect_calls_storage_secret(self, mock_init, mock_storage, mock_catalog):
        lake = PyDuckLake(storage=mock_storage, catalog=mock_catalog)
        lake.ddb = MagicMock()
        lake.connect()
        mock_storage.create_duckdb_secret.assert_called_once_with(lake.ddb)

    @patch.object(PyDuckLake, "_initialize")
    def test_connect_executes_attach(self, mock_init, mock_storage, mock_catalog):
        lake = PyDuckLake(storage=mock_storage, catalog=mock_catalog)
        lake.ddb = MagicMock()
        lake.connect()
        sql = lake.ddb.execute.call_args[0][0]
        assert "ATTACH" in sql
        assert "ducklake:sqlite:metadata.sqlite" in sql
        assert "s3://test-bucket/" in sql


class TestPyDuckLakeDisconnect:
    @patch.object(PyDuckLake, "_initialize")
    def test_disconnect_detaches(self, mock_init, mock_storage, mock_catalog):
        lake = PyDuckLake(storage=mock_storage, catalog=mock_catalog)
        lake.ddb = MagicMock()
        lake.disconnect()
        sql = lake.ddb.execute.call_args[0][0]
        assert "DETACH ducklake" in sql


class TestPyDuckLakeExecuteAndQuery:
    @patch.object(PyDuckLake, "_initialize")
    def test_execute_delegates(self, mock_init, mock_storage, mock_catalog):
        lake = PyDuckLake(storage=mock_storage, catalog=mock_catalog)
        lake.ddb = MagicMock()
        lake.execute("SELECT 1", [42])
        lake.ddb.execute.assert_called_once_with(query="SELECT 1", parameters=[42])

    @patch.object(PyDuckLake, "_initialize")
    def test_query_delegates(self, mock_init, mock_storage, mock_catalog):
        lake = PyDuckLake(storage=mock_storage, catalog=mock_catalog)
        lake.ddb = MagicMock()
        lake.query("SELECT 1", [42])
        lake.ddb.query.assert_called_once_with(query="SELECT 1", params=[42])


class TestDuckDBCatalog:
    def test_default_catalog(self):
        c = DuckDBCatalog()
        assert c.catalog == "metadata.ducklake"

    def test_custom_catalog(self):
        c = DuckDBCatalog(catalog="my.ducklake")
        assert c.catalog == "my.ducklake"


class TestSQLiteCatalog:
    def test_default_catalog(self):
        c = SQLiteCatalog()
        assert c.catalog == "sqlite:metadata.sqlite"

    def test_custom_db_name(self):
        c = SQLiteCatalog(db_name="mydb")
        assert c.catalog == "sqlite:mydb.sqlite"


class TestPostgresCatalog:
    def test_default_catalog(self):
        c = PostgresCatalog()
        assert (
            c.catalog
            == "postgres:dbname=ducklake host=localhost port=5432 user=postgres"
        )

    def test_catalog_with_password(self):
        c = PostgresCatalog(password="secret")
        assert "password=secret" in c.catalog

    def test_catalog_without_password(self):
        c = PostgresCatalog()
        assert "password" not in c.catalog

    def test_custom_params(self):
        c = PostgresCatalog(dbname="mydb", host="pg.internal", port=5433, user="admin")
        assert "dbname=mydb" in c.catalog
        assert "host=pg.internal" in c.catalog
        assert "port=5433" in c.catalog
        assert "user=admin" in c.catalog
        assert c.catalog.startswith("postgres:")


class TestMinioStorage:
    def test_bucket_property(self):
        s = MinioStorage(
            endpoint="localhost:9000", bucket_name="mybucket", user="u", password="p"
        )
        assert s.bucket == "mybucket"

    def test_create_duckdb_secret(self):
        s = MinioStorage(
            endpoint="localhost:9000", bucket_name="b", user="myuser", password="mypass"
        )
        mock_ddb = MagicMock()
        s.create_duckdb_secret(mock_ddb)
        sql = mock_ddb.execute.call_args[0][0]
        assert "myuser" in sql
        assert "mypass" in sql
        assert "localhost:9000" in sql
        assert "USE_SSL false" in sql


class TestS3Storage:
    def test_bucket_property(self):
        s = S3Storage(
            bucket_name="mybucket",
            region="us-east-1",
            access_key_id="ak",
            secret_access_key="sk",
        )
        assert s.bucket == "mybucket"

    def test_create_duckdb_secret(self):
        s = S3Storage(
            bucket_name="b",
            region="eu-west-1",
            access_key_id="mykey",
            secret_access_key="mysecret",
        )
        mock_ddb = MagicMock()
        s.create_duckdb_secret(mock_ddb)
        sql = mock_ddb.execute.call_args[0][0]
        assert "mykey" in sql
        assert "mysecret" in sql
        assert "eu-west-1" in sql
        assert "USE_SSL true" in sql
