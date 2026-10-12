import pytest
from dotenv import load_dotenv

load_dotenv()

from fastapi.testclient import TestClient
from app import app
from constants import INTERNAL_TOKEN


@pytest.fixture(scope="function")
def client():
    with TestClient(app) as test_client:
        test_client.headers.update({"INTERNAL-TOKEN": INTERNAL_TOKEN})
        yield test_client
