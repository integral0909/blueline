class TestHealth:
    def test_it_answers(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_it_says_it_is_up(self, client):
        assert client.get("/health").json() == {"status": "ok"}


class TestDocs:
    def test_the_schema_is_served(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_the_schema_names_the_application(self, client):
        assert client.get("/openapi.json").json()["info"]["title"] == "blueline"

    def test_every_route_is_in_the_schema(self, client):
        paths = client.get("/openapi.json").json()["paths"]
        for path in ("/health", "/analyse", "/methods", "/methods/{title}"):
            assert path in paths
