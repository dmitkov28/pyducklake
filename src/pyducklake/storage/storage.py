from typing import Protocol

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from duckdb import DuckDBPyConnection


class Storage(Protocol):
    bucket: str

    def create_bucket(self) -> None: ...
    def create_duckdb_secret(self, ddb: DuckDBPyConnection) -> None: ...


class MinioStorage(Storage):
    def __init__(self, endpoint: str, bucket_name: str, user: str, password: str):
        self._endpoint = endpoint
        self._bucket_name = bucket_name
        self._user = user
        self._password = password

    @property
    def bucket(self) -> str:
        return self._bucket_name

    def create_bucket(self) -> None:
        s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{self._endpoint}",
            aws_access_key_id=self._user,
            aws_secret_access_key=self._password,
            config=Config(signature_version="s3v4"),
        )
        try:
            s3.create_bucket(Bucket=self._bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
                raise

    def create_duckdb_secret(self, ddb: DuckDBPyConnection) -> None:
        ddb.execute(
            f"""
            CREATE SECRET s3_secret (
                TYPE S3,
                KEY_ID '{self._user}',
                SECRET '{self._password}',
                ENDPOINT '{self._endpoint}',
                USE_SSL false,
                URL_STYLE 'path'
            );
        """
        )


class S3Storage(Storage):
    def __init__(
        self, bucket_name: str, region: str, access_key_id: str, secret_access_key: str
    ):
        self._bucket_name = bucket_name
        self._region = region
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key

    @property
    def bucket(self) -> str:
        return self._bucket_name

    def create_bucket(self) -> None:
        s3 = boto3.client("s3", region_name=self._region)
        try:
            s3.create_bucket(
                Bucket=self._bucket_name,
                CreateBucketConfiguration={"LocationConstraint": self._region},
            )
        except ClientError as e:
            if e.response["Error"]["Code"] not in (
                "BucketAlreadyOwnedByYou",
                "BucketAlreadyExists",
            ):
                raise

    def create_duckdb_secret(self, ddb: DuckDBPyConnection) -> None:
        ddb.execute(
            f"""
            CREATE SECRET s3_secret (
                TYPE S3,
                KEY_ID '{self._access_key_id}',
                SECRET '{self._secret_access_key}',
                REGION '{self._region}',
                USE_SSL true
            );
        """
        )
