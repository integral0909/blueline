import pytest

from blueline.config import ENV_PREFIX, Settings, for_testing, from_env
from blueline.db.session import DEFAULT_URL, MEMORY_URL


@pytest.fixture()
def clean_env(monkeypatch):
    for name in ("DATABASE_URL", "CREATE_TABLES", "SEED_ON_START", "ECHO_SQL"):
        monkeypatch.delenv(ENV_PREFIX + name, raising=False)
    return monkeypatch


class TestDefaults:
    def test_it_points_at_a_file_by_default(self):
        assert Settings().database_url == DEFAULT_URL

    def test_it_creates_the_tables_by_default(self):
        assert Settings().create_tables

    def test_it_does_not_seed_by_default(self):
        assert not Settings().seed_on_start

    def test_it_does_not_echo_by_default(self):
        assert not Settings().echo_sql

    def test_it_knows_when_it_is_in_memory(self):
        assert Settings(database_url=MEMORY_URL).is_in_memory
        assert not Settings().is_in_memory


class TestFromEnv:
    def test_an_empty_environment_gives_the_defaults(self, clean_env):
        assert from_env() == Settings()

    def test_it_reads_the_url(self, clean_env):
        clean_env.setenv(ENV_PREFIX + "DATABASE_URL", MEMORY_URL)
        assert from_env().database_url == MEMORY_URL

    @pytest.mark.parametrize("word", ["1", "true", "TRUE", "yes", "on"])
    def test_the_obvious_words_turn_a_flag_on(self, clean_env, word):
        clean_env.setenv(ENV_PREFIX + "SEED_ON_START", word)
        assert from_env().seed_on_start

    @pytest.mark.parametrize("word", ["0", "false", "no", "off"])
    def test_the_obvious_words_turn_it_off(self, clean_env, word):
        clean_env.setenv(ENV_PREFIX + "SEED_ON_START", word)
        assert not from_env().seed_on_start

    def test_something_unrecognised_is_off_rather_than_on(self, clean_env):
        # A typo that quietly turns a feature on is worse than one that
        # leaves it off.
        clean_env.setenv(ENV_PREFIX + "SEED_ON_START", "maybe")
        assert not from_env().seed_on_start

    def test_it_does_not_mind_stray_space(self, clean_env):
        clean_env.setenv(ENV_PREFIX + "SEED_ON_START", "  yes  ")
        assert from_env().seed_on_start

    def test_a_flag_that_defaults_on_stays_on_when_unset(self, clean_env):
        assert from_env().create_tables

    def test_a_flag_that_defaults_on_can_be_turned_off(self, clean_env):
        clean_env.setenv(ENV_PREFIX + "CREATE_TABLES", "no")
        assert not from_env().create_tables


class TestForTesting:
    def test_it_points_at_memory(self):
        assert for_testing().is_in_memory

    def test_it_creates_the_tables(self):
        assert for_testing().create_tables

    def test_it_does_not_seed(self):
        assert not for_testing().seed_on_start


class TestImmutability:
    def test_settings_cannot_be_changed_after_the_fact(self):
        settings = Settings()
        with pytest.raises(Exception):
            settings.database_url = MEMORY_URL  # type: ignore[misc]
