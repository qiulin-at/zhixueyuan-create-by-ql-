import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
os.environ["DATABASE_URL"] = f"sqlite:///{(BASE / 'test_zhixueyun.db').as_posix()}"
os.environ["LLM_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

import seed
from app.main import app


@pytest.fixture(scope="session")
def client():
    seed.main()
    with TestClient(app) as test_client:
        yield test_client