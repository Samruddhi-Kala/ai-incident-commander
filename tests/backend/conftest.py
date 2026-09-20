import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.main import app


@pytest.fixture
def client():
    """
    FastAPI TestClient fixture.
    """
    with TestClient(app) as test_client:
        yield test_client
