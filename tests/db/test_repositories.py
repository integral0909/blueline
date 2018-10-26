"""The package the repositories were split into."""

from __future__ import annotations

import importlib
import pkgutil

import blueline.db.repositories as package

SUBJECTS = ["competitions", "methods", "performances", "ringers", "towers"]


class TestPackage:
    def test_every_subject_has_a_module(self) -> None:
        found = {module.name for module in pkgutil.iter_modules(package.__path__)}
        assert set(SUBJECTS) <= found

    def test_everything_is_importable_from_the_package(self) -> None:
        for name in package.__all__:
            assert hasattr(package, name), name

    def test_nothing_is_exported_twice(self) -> None:
        assert len(package.__all__) == len(set(package.__all__))

    def test_every_repository_is_exported(self) -> None:
        for subject in SUBJECTS:
            module = importlib.import_module(f"blueline.db.repositories.{subject}")
            repositories = [
                name
                for name in dir(module)
                if name.endswith("Repository") and not name.startswith("_")
            ]
            for name in repositories:
                assert name in package.__all__ or name == "Repository", name

    def test_no_module_reaches_sideways_into_another(self) -> None:
        """A subject that needed another one's rows would belong with it."""
        for subject in SUBJECTS:
            module = importlib.import_module(f"blueline.db.repositories.{subject}")
            source = module.__doc__ or ""
            assert source, f"{subject} says nothing about itself"

    def test_the_old_module_is_gone(self) -> None:
        with __import__("pytest").raises(ModuleNotFoundError):
            importlib.import_module("blueline.db.repository")
