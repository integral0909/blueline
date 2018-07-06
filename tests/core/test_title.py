import pytest

from blueline.core.stage import StageError
from blueline.core.title import (
    CLASS_WORDS,
    CLASSLESS_NAMES,
    Title,
    TitleError,
    parse_title,
    same_method,
    title_for,
)

REAL_TITLES = [
    ("Cambridge Surprise Major", "Cambridge", "Surprise", 8),
    ("Plain Bob Minor", "Plain", "Bob", 6),
    ("Grandsire Triples", "Grandsire", None, 7),
    ("Kent Treble Bob Royal", "Kent", "Treble Bob", 10),
    ("Double Norwich Court Bob Major", "Double Norwich Court", "Bob", 8),
    ("London Surprise Royal", "London", "Surprise", 10),
    ("Stedman Caters", "Stedman", None, 9),
    ("Bristol Surprise Maximus", "Bristol", "Surprise", 12),
    ("Reverse Canterbury Place Doubles", "Reverse Canterbury", "Place", 5),
    ("St Clements College Bob Minor", "St Clements College", "Bob", 6),
]


class TestParse:
    @pytest.mark.parametrize(
        ("text", "name", "kind", "stage"), REAL_TITLES, ids=[t[0] for t in REAL_TITLES]
    )
    def test_reads_a_real_title(self, text, name, kind, stage):
        parsed = parse_title(text)
        assert parsed.name == name
        assert parsed.classification == kind
        assert parsed.stage == stage

    @pytest.mark.parametrize("text", [t[0] for t in REAL_TITLES])
    def test_every_title_writes_back_the_way_it_came(self, text):
        assert str(parse_title(text)) == text

    def test_treble_bob_beats_bob(self):
        # Otherwise Kent Treble Bob Major comes out as a method called Kent Treble.
        assert parse_title("Kent Treble Bob Major").name == "Kent"

    def test_treble_place_is_found_too(self):
        assert parse_title("Barford Treble Place Minor").classification == "Treble Place"

    def test_little_bob_keeps_its_name(self):
        # Little is the name here, not a modifier on something else, and
        # stripping it would leave a title with no method in it.
        parsed = parse_title("Little Bob Major")
        assert parsed.name == "Little"
        assert parsed.classification == "Bob"
        assert parsed.stage == 8

    def test_a_class_typed_in_lower_case_still_reads(self):
        parsed = parse_title("cambridge surprise major")
        assert parsed.classification == "Surprise"
        assert parsed.stage == 8

    def test_refuses_something_too_short_to_be_a_title(self):
        with pytest.raises(TitleError):
            parse_title("Cambridge")

    def test_refuses_a_stage_that_is_not_one(self):
        with pytest.raises(StageError):
            parse_title("Cambridge Surprise Octuples")

    def test_refuses_a_title_with_no_name_left(self):
        with pytest.raises(TitleError):
            parse_title("Surprise Major")

    def test_does_not_mind_stray_space(self):
        assert parse_title("  Plain Bob   Minor  ").name == "Plain"


class TestBuild:
    def test_builds_an_ordinary_title(self):
        assert str(title_for("Cambridge", 8, "Surprise")) == "Cambridge Surprise Major"

    def test_drops_the_class_for_grandsire(self):
        assert str(title_for("Grandsire", 7, "Bob")) == "Grandsire Triples"

    def test_drops_it_for_stedman_too(self):
        assert str(title_for("Stedman", 9, "Principle")) == "Stedman Caters"

    def test_every_classless_name_stays_classless(self):
        for name in CLASSLESS_NAMES:
            assert title_for(name, 8, "Bob").is_classless

    def test_trims_the_name(self):
        assert title_for("  Cambridge  ", 8, "Surprise").name == "Cambridge"

    def test_refuses_an_empty_name(self):
        with pytest.raises(TitleError):
            Title(name="   ", stage=8)

    def test_refuses_a_stage_with_no_name(self):
        with pytest.raises(StageError):
            Title(name="Cambridge", stage=99)


class TestClassWords:
    def test_the_longer_phrases_come_first(self):
        lengths = [len(word.split()) for word in CLASS_WORDS]
        assert lengths == sorted(lengths, reverse=True)

    def test_bob_is_in_the_list(self):
        assert "Bob" in CLASS_WORDS


class TestSameMethod:
    def test_the_same_title_is_the_same_method(self):
        assert same_method("Cambridge Surprise Major", "Cambridge Surprise Major")

    def test_case_and_spacing_do_not_matter(self):
        assert same_method("cambridge surprise major", "Cambridge  Surprise Major")

    def test_a_different_stage_is_a_different_method(self):
        assert not same_method("Cambridge Surprise Major", "Cambridge Surprise Royal")

    def test_a_different_class_is_a_different_method(self):
        assert not same_method("Yorkshire Surprise Major", "Yorkshire Delight Major")

    def test_something_unparseable_matches_nothing(self):
        assert not same_method("Cambridge", "Cambridge Surprise Major")
