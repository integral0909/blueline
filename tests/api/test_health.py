class TestHealth:
    def test_it_answers(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_it_says_it_is_up(self, client):
        assert client.get("/health").json() == {"status": "ok"}


class TestReadiness:
    def test_it_answers(self, client):
        assert client.get("/ready").status_code == 200

    def test_a_working_database_is_ready(self, client):
        assert client.get("/ready").json()["ready"] is True

    def test_the_database_is_named_in_the_checks(self, client):
        names = [check["name"] for check in client.get("/ready").json()["checks"]]
        assert names == ["database"]

    def test_a_check_says_how_long_it_took(self, client):
        check = client.get("/ready").json()["checks"][0]
        assert check["took"] >= 0

    def test_a_broken_database_is_not_ready(self, client):
        # Drop the table the readiness check looks at, through the same
        # factory the application uses, then ask.
        from sqlalchemy import text

        from blueline.api.deps import get_factory

        session = get_factory()()
        try:
            session.execute(text("drop table methods"))
            session.commit()
        finally:
            session.close()

        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json()["ready"] is False


class TestWhatIsMounted:
    """There is no generated schema to check against, so check the routes.

    A framework would have handed over an openapi document. Writing one by
    hand and keeping it right would be a second description of the same
    thing, so what is asserted here is that the paths are actually served.
    """

    def test_the_paths_a_client_needs_are_all_mounted(self, client):
        from blueline.api.routers import ROUTERS

        served = {path for router in ROUTERS for path in router.paths()}
        for path in ("/health", "/ready", "/analyse", "/methods", "/methods/{title}"):
            assert path in served

    def test_an_unmounted_path_says_so(self, client):
        reply = client.get("/nowhere")
        assert reply.status_code == 404
        assert "nothing is served" in reply.json()["detail"]

    def test_a_wrong_method_is_not_a_wrong_path(self, client):
        assert client.delete("/health").status_code == 405
