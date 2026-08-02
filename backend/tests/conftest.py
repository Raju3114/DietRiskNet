"""Shared pytest fixtures for backend tests.

Ensures the database schema exists before any test runs.  ``create_all`` is
idempotent: it creates only missing tables, so running the suite against a
fresh (e.g. CI) database and against the developer's existing dev database
both work without dropping any data.
"""

import pytest

from backend.database.database import Base, engine
# Import every model so Base.metadata includes all tables (including
# ai_dietitian_results, meal_fusions, recommendations, etc.).
import backend.database.models  # noqa: F401, E402


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield
