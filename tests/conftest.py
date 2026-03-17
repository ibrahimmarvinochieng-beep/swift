"""Shared pytest fixtures for Swift tests.

Forces PERSISTENCE_BACKEND=memory so tests don't touch the SQLite
database on disk and run in full isolation.
"""

import os
os.environ["PIPELINE_AUTOSTART"] = "false"
os.environ["PERSISTENCE_BACKEND"] = "memory"

import pytest
from api.auth import create_default_admin


@pytest.fixture(scope="session", autouse=True)
def setup_admin():
    create_default_admin()
