from blueline.service import calls as touches
from blueline.service.results import Reason


class TestPositions:
    def test_it_names_the_positions(self, loaded):
        found = touches.positions(loaded, "Plain Bob Major").unwrap()
        assert [p.name for p in found][-1] == "Home"

    def test_there_is_one_per_lead(self, loaded):
        found = touches.positions(loaded, "Plain Bob Major").unwrap()
        assert len(found) == 7

    def test_it_carries_where_the_tenor_is(self, loaded):
        found = touches.positions(loaded, "Plain Bob Major").unwrap()
        assert found[-1].tenor_place == 8

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        assert (
            touches.positions(loaded, "Nowhere Surprise Major").failure.reason is Reason.NOT_FOUND
        )


class TestProvePositions:
    def test_it_proves_a_touch_called_by_position(self, loaded):
        report = touches.prove_positions(loaded, "Plain Bob Major", ["Home"]).unwrap()
        assert report.leads == 7

    def test_two_homes_run_on_into_another_course(self, loaded):
        report = touches.prove_positions(
            loaded, "Plain Bob Major", ["Wrong", "Home", "Home"]
        ).unwrap()
        assert report.leads == 14

    def test_the_calling_comes_back_in_symbols(self, loaded):
        report = touches.prove_positions(loaded, "Plain Bob Major", ["Home"]).unwrap()
        assert report.calling == "pppppp-"

    def test_calling_nothing_is_the_plain_course(self, loaded):
        report = touches.prove_positions(loaded, "Plain Bob Major", []).unwrap()
        assert report.is_ringable
        assert report.length == 112

    def test_a_position_it_does_not_know_is_invalid(self, loaded):
        result = touches.prove_positions(loaded, "Plain Bob Major", ["Sideways"])
        assert result.failure.reason is Reason.INVALID

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        result = touches.prove_positions(loaded, "Nowhere Surprise Major", ["Home"])
        assert result.failure.reason is Reason.NOT_FOUND


class TestCallingAsPositions:
    def test_it_reads_a_calling_back(self, loaded):
        found = touches.calling_as_positions(loaded, "Plain Bob Major", "pppppp-").unwrap()
        assert found == ["Home"]

    def test_it_goes_round_trip(self, loaded):
        report = touches.prove_positions(
            loaded, "Plain Bob Major", ["Wrong", "Home", "Home"]
        ).unwrap()
        back = touches.calling_as_positions(loaded, "Plain Bob Major", report.calling).unwrap()
        assert back == ["Wrong", "Home", "Home"]

    def test_a_plain_course_has_no_positions(self, loaded):
        found = touches.calling_as_positions(loaded, "Plain Bob Major", "ppppppp").unwrap()
        assert found == []

    def test_a_method_that_is_not_there_is_not_found(self, loaded):
        result = touches.calling_as_positions(loaded, "Nowhere Surprise Major", "-")
        assert result.failure.reason is Reason.NOT_FOUND
