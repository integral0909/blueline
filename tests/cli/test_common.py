"""What every group of commands leans on."""

from __future__ import annotations

import pytest

from blueline.cli.declare import Exit
from blueline.cli.commands.common import EXIT_FOR, changing, show, stores, unwrap
from blueline.service.results import Reason, invalid, not_found, succeeded


class TestUnwrap:
    def test_a_success_gives_the_value(self) -> None:
        assert unwrap(succeeded(7)) == 7

    @pytest.mark.parametrize("reason", list(Reason))
    def test_every_reason_has_an_exit_code(self, reason) -> None:
        assert reason in EXIT_FOR

    def test_the_codes_are_all_different(self) -> None:
        assert len(set(EXIT_FOR.values())) == len(EXIT_FOR)

    def test_none_of_them_look_like_success(self) -> None:
        assert all(code > 0 for code in EXIT_FOR.values())

    def test_a_refusal_exits_with_the_matching_code(self) -> None:
        with pytest.raises(Exit) as caught:
            unwrap(not_found("gone"))
        assert caught.value.code == EXIT_FOR[Reason.NOT_FOUND]

    def test_something_that_does_not_make_sense(self) -> None:
        with pytest.raises(Exit) as caught:
            unwrap(invalid("no"))
        assert caught.value.code == EXIT_FOR[Reason.INVALID]


class TestStores:
    def test_every_repository_shares_one_session(self, library) -> None:
        store = stores()
        sessions = {
            store.methods.session,
            store.performances.session,
            store.towers.session,
            store.ringers.session,
            store.competitions.session,
            store.compositions.session,
            store.collections.session,
        }
        assert len(sessions) == 1

    def test_the_session_is_the_one_on_the_store(self, library) -> None:
        store = stores()
        assert store.methods.session is store.session


class TestChanging:
    def test_it_commits_when_nothing_raised(self, library) -> None:
        from blueline.core.towers import Tower, weight_from_pounds

        with changing() as store:
            store.towers.add(Tower(place="St Andrew", bells=8, tenor=weight_from_pounds(2604)))
        assert stores().towers.count() == 1

    def test_it_rolls_back_when_something_did(self, library) -> None:
        from blueline.core.towers import Tower, weight_from_pounds

        with pytest.raises(RuntimeError), changing() as store:
            store.towers.add(Tower(place="St Andrew", bells=8, tenor=weight_from_pounds(2604)))
            raise RuntimeError("something went wrong halfway")
        assert stores().towers.count() == 0

    def test_a_refusal_rolls_back_too(self, library) -> None:
        from blueline.core.towers import Tower, weight_from_pounds

        with pytest.raises(Exit), changing() as store:
            store.towers.add(Tower(place="St Andrew", bells=8, tenor=weight_from_pounds(2604)))
            unwrap(invalid("no"))
        assert stores().towers.count() == 0


class TestShow:
    def test_it_prints(self, capsys) -> None:
        show("hello")
        assert "hello" in capsys.readouterr().out
