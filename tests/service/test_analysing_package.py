"""The package the method analysis was split into."""

from __future__ import annotations

import importlib
import pkgutil

import blueline.service.analysing as package
from tests.packages import duplicates, exported

SUBJECTS = ["comparing", "groups", "lines", "variations"]


class TestPackage:
    def test_every_subject_has_a_module(self) -> None:
        found = {module.name for module in pkgutil.iter_modules(package.__path__)}
        assert set(SUBJECTS) <= found

    def test_nothing_is_exported_from_two_places(self) -> None:
        assert duplicates(package) == set()

    def test_every_public_function_is_exported(self) -> None:
        for subject in SUBJECTS:
            module = importlib.import_module(f"blueline.service.analysing.{subject}")
            public = {
                name
                for name, value in vars(module).items()
                if not name.startswith("_")
                and callable(value)
                and getattr(value, "__module__", "") == module.__name__
            }
            assert public <= exported(package), subject

    def test_the_old_module_is_gone(self) -> None:
        import pytest

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("blueline.service.analysis")


class TestStillWorks:
    def test_a_line_can_still_be_drawn(self, loaded) -> None:
        assert package.line(loaded, "Plain Bob Minor", 2).ok

    def test_falseness_still_answers(self, loaded) -> None:
        assert package.falseness(loaded, "Cambridge Surprise Minor").ok

    def test_a_variation_can_still_be_made(self, loaded) -> None:
        assert package.vary(loaded, "Plain Bob Minor", "reverse").ok

    def test_the_groups_still_answer(self, loaded) -> None:
        assert package.lead_head_groups(loaded).ok

    def test_two_methods_can_still_be_compared(self, loaded) -> None:
        assert package.compare_methods(
            loaded, "Cambridge Surprise Major", "Yorkshire Surprise Major"
        ).ok

    def test_the_variations_table_is_still_reachable(self) -> None:
        assert set(package.VARIATIONS) == {"reverse", "mirror", "double"}
