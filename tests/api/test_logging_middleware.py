
from typing import Dict

import json

from blueline.api.middlewares.logging import (
    DURATION_HEADER,
    REQUEST_ID_HEADER,
    request_id_of,
)
from blueline.logging import JSON, configure


class TestRequestId:
    def test_every_response_carries_one(self, client):
        response = client.get("/health")
        assert response.headers[REQUEST_ID_HEADER]

    def test_two_requests_get_different_ones(self, client):
        first = client.get("/health").headers[REQUEST_ID_HEADER]
        second = client.get("/health").headers[REQUEST_ID_HEADER]
        assert first != second

    def test_a_caller_supplied_one_is_kept(self, client):
        response = client.get("/health", headers={REQUEST_ID_HEADER: "mine-123"})
        assert response.headers[REQUEST_ID_HEADER] == "mine-123"

    def test_an_empty_one_is_replaced(self, client):
        response = client.get("/health", headers={REQUEST_ID_HEADER: "   "})
        assert response.headers[REQUEST_ID_HEADER].strip()

    def test_it_is_on_error_responses_too(self, client):
        response = client.get("/methods/Nowhere Surprise Major")
        assert response.status_code == 404
        assert response.headers[REQUEST_ID_HEADER]


class TestTiming:
    def test_every_response_says_how_long_it_took(self, client):
        assert DURATION_HEADER in client.get("/health").headers

    def test_it_is_a_number_of_milliseconds(self, client):
        assert float(client.get("/health").headers[DURATION_HEADER]) >= 0

    def test_a_slower_endpoint_takes_longer(self, seeded):
        quick = float(seeded.get("/health").headers[DURATION_HEADER])
        slow = float(
            seeded.get("/methods/Cambridge Surprise Major/falseness").headers[DURATION_HEADER]
        )
        assert slow > quick


class TestLogging:
    def test_a_request_is_logged(self, client, capsys):
        configure(JSON)
        client.get("/health")
        lines = [line for line in capsys.readouterr().err.strip().split("\n") if line]
        events = [json.loads(line) for line in lines]
        assert any(event["event"] == "request" for event in events)

    def test_the_line_carries_the_status_and_the_path(self, client, capsys):
        configure(JSON)
        client.get("/health")
        events = [json.loads(x) for x in capsys.readouterr().err.strip().split("\n") if x]
        request = next(e for e in events if e["event"] == "request")
        assert request["status"] == 200
        assert request["path"] == "/health"
        assert request["method"] == "GET"

    def test_the_line_carries_the_request_id(self, client, capsys):
        configure(JSON)
        response = client.get("/health", headers={REQUEST_ID_HEADER: "mine-456"})
        events = [json.loads(x) for x in capsys.readouterr().err.strip().split("\n") if x]
        request = next(e for e in events if e["event"] == "request")
        assert request["request_id"] == "mine-456"
        assert response.headers[REQUEST_ID_HEADER] == "mine-456"

    def test_the_context_does_not_leak_between_requests(self, client, capsys):
        configure(JSON)
        client.get("/health", headers={REQUEST_ID_HEADER: "first"})
        capsys.readouterr()
        client.get("/health", headers={REQUEST_ID_HEADER: "second"})
        events = [json.loads(x) for x in capsys.readouterr().err.strip().split("\n") if x]
        request = next(e for e in events if e["event"] == "request")
        assert request["request_id"] == "second"


class TestIdHelper:
    def test_it_takes_what_the_caller_gave(self):
        assert request_id_of({"HTTP_X_REQUEST_ID": "supplied"}) == "supplied"

    def test_it_invents_one_where_there_is_none(self):
        class Fake:
            headers: Dict[str, str] = {}

        assert len(request_id_of({})) == 32
