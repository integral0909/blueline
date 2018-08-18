import json


class TestExport:
    def test_it_writes_json_by_default(self, seeded):
        response = seeded.get("/methods/export")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")

    def test_the_json_is_a_collection(self, seeded):
        document = json.loads(seeded.get("/methods/export").text)
        assert document["format"] == "blueline.methods"
        assert len(document["methods"]) == 15

    def test_it_can_write_the_line_format(self, seeded):
        response = seeded.get("/methods/export", params={"shape": "lines"})
        assert response.headers["content-type"].startswith("text/plain")
        assert response.text.lstrip().startswith("#")

    def test_it_can_export_one_stage(self, seeded):
        document = json.loads(seeded.get("/methods/export", params={"stage": 6}).text)
        assert all(record["stage"] == 6 for record in document["methods"])

    def test_a_shape_it_does_not_know_is_rejected(self, seeded):
        assert seeded.get("/methods/export", params={"shape": "xml"}).status_code == 422

    def test_a_stage_out_of_range_is_rejected(self, seeded):
        assert seeded.get("/methods/export", params={"stage": 99}).status_code == 422

    def test_an_empty_library_exports_an_empty_collection(self, client):
        document = json.loads(client.get("/methods/export").text)
        assert document["methods"] == []


class TestImport:
    def test_it_reads_a_line_collection(self, client):
        body = {"body": "Plain, 6, x16x16x16,12\nCambridge, 6, x36x14x12x36x14x56,12\n"}
        response = client.post("/methods/import", json=body)
        assert response.status_code == 200
        assert response.json()["added"] == ["Plain Bob Minor", "Cambridge Surprise Minor"]

    def test_the_methods_are_there_afterwards(self, client):
        client.post("/methods/import", json={"body": "Plain, 6, x16x16x16,12"})
        assert client.get("/methods").json()["count"] == 1

    def test_it_reads_json_too(self, client, seeded):
        text = seeded.get("/methods/export").text
        response = client.post("/methods/import", json={"body": text})
        assert response.json()["total"] == 15

    def test_anything_already_there_is_skipped(self, seeded):
        text = seeded.get("/methods/export").text
        body = seeded.post("/methods/import", json={"body": text}).json()
        assert body["added"] == []
        assert len(body["skipped"]) == 15

    def test_a_bad_record_is_reported_and_the_rest_go_in(self, client):
        body = {"body": "Plain, 6, x16x16x16,12\nrubbish\n"}
        result = client.post("/methods/import", json=body).json()
        assert result["added"] == ["Plain Bob Minor"]
        assert len(result["problems"]) == 1

    def test_the_summary_says_what_happened(self, client):
        body = {"body": "Plain, 6, x16x16x16,12\nrubbish\n"}
        assert "1 added" in client.post("/methods/import", json=body).json()["summary"]

    def test_a_document_it_cannot_read_is_unprocessable(self, client):
        body = {"body": '{"format": "something.else"}'}
        response = client.post("/methods/import", json=body)
        assert response.status_code == 422
        assert response.json()["detail"]["reason"] == "invalid"

    def test_an_empty_body_is_rejected_by_the_schema(self, client):
        assert client.post("/methods/import", json={"body": ""}).status_code == 422


class TestRoundTrip:
    def test_what_is_exported_puts_back_what_is_removed(self, seeded):
        text = seeded.get("/methods/export").text
        seeded.delete("/methods/Plain Bob Minor")
        assert seeded.get("/methods/Plain Bob Minor").status_code == 404

        result = seeded.post("/methods/import", json={"body": text}).json()
        assert result["added"] == ["Plain Bob Minor"]
        assert seeded.get("/methods/Plain Bob Minor").status_code == 200

    def test_the_line_format_round_trips_as_well(self, seeded):
        text = seeded.get("/methods/export", params={"shape": "lines"}).text
        seeded.delete("/methods/Cambridge Surprise Major")
        result = seeded.post("/methods/import", json={"body": text}).json()
        assert result["added"] == ["Cambridge Surprise Major"]
