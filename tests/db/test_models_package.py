"""The package the tables were split into."""

from __future__ import annotations

import importlib
import pkgutil

import blueline.db.models as package
from blueline.db.models.base import Base
from tests.packages import duplicates, exported

SUBJECTS = ["base", "competitions", "methods", "ringers", "towers"]


class TestPackage:
    def test_every_subject_has_a_module(self) -> None:
        found = {module.name for module in pkgutil.iter_modules(package.__path__)}
        assert set(SUBJECTS) <= found

    def test_nothing_is_exported_from_two_places(self) -> None:
        assert duplicates(package) == set()

    def test_every_table_is_exported(self) -> None:
        for subject in SUBJECTS:
            module = importlib.import_module(f"blueline.db.models.{subject}")
            tables = {
                name
                for name, value in vars(module).items()
                if name.startswith("Stored") and getattr(value, "__module__", "") == module.__name__
            }
            assert tables <= exported(package), subject

    def test_the_base_is_on_its_own(self) -> None:
        """A table has to be able to import it without importing the rest."""
        module = importlib.import_module("blueline.db.models.base")
        assert not any(name.startswith("Stored") for name in vars(module))

    def test_every_table_is_on_one_metadata(self) -> None:
        # Two declarative bases would give two metadatas, and create_all would
        # quietly build half the schema.
        assert len(Base.metadata.tables) >= 7

    def test_the_metadata_holds_what_the_package_exports(self) -> None:
        stored = {name for name in exported(package) if name.startswith("Stored")}
        assert len(stored) == len(Base.metadata.tables)
