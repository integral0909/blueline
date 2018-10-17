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
        from sqlalchemy import text

        from blueline.api.deps import get_session

        def broken():
            session = next(get_session())
            session.execute(text("drop table methods"))
            yield session

        client.app.dependency_overrides[get_session] = broken
        try:
            response = client.get("/ready")
        finally:
            client.app.dependency_overrides.pop(get_session, None)
        assert response.status_code == 503
        assert response.json()["ready"] is False


class TestDocs:
    def test_the_schema_is_served(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_the_schema_names_the_application(self, client):
        assert client.get("/openapi.json").json()["info"]["title"] == "blueline"

    def test_every_route_is_in_the_schema(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        for path in ("/health", "/ready", "/analyse", "/methods", "/methods/{title}"):
            assert path in paths
