MARCHGATE = {"place": "St Andrew, Marchgate", "bells": 8, "tenor": "23-1-14"}
ASHCOMBE = {"place": "St Mary, Ashcombe", "bells": 6, "tenor": "8-0-0"}
KELBROOK = {"place": "All Saints, Kelbrook", "bells": 12, "tenor": "31-2-7"}


def load(client):
    for tower in (MARCHGATE, ASHCOMBE, KELBROOK):
        client.post("/towers", json=tower)
    return client


class TestAdding:
    def test_one_can_be_added(self, client):
        response = client.post("/towers", json=MARCHGATE)
        assert response.status_code == 201
        assert response.json()["bells"] == 8

    def test_the_weight_comes_back_both_ways(self, client):
        body = client.post("/towers", json=MARCHGATE).json()
        assert body["tenor"] == "23-1-14"
        assert body["tenor_pounds"] == 23 * 112 + 28 + 14

    def test_a_heavy_ring_says_so(self, client):
        assert client.post("/towers", json=MARCHGATE).json()["is_heavy"]

    def test_a_light_one_does_not(self, client):
        assert not client.post("/towers", json=ASHCOMBE).json()["is_heavy"]

    def test_the_same_place_twice_is_a_conflict(self, client):
        client.post("/towers", json=MARCHGATE)
        assert client.post("/towers", json=MARCHGATE).status_code == 409

    def test_a_weight_it_cannot_read_is_unprocessable(self, client):
        response = client.post("/towers", json={**MARCHGATE, "tenor": "heavy"})
        assert response.status_code == 422
        assert response.json()["detail"]["reason"] == "invalid"

    def test_a_nonsense_weight_is_unprocessable(self, client):
        assert client.post("/towers", json={**MARCHGATE, "tenor": "23-9-0"}).status_code == 422

    def test_an_empty_place_is_rejected_by_the_schema(self, client):
        assert client.post("/towers", json={**MARCHGATE, "place": "  "}).status_code == 422

    def test_a_silly_number_of_bells_is_rejected_by_the_schema(self, client):
        assert client.post("/towers", json={**MARCHGATE, "bells": 2}).status_code == 422


class TestFetching:
    def test_one_can_be_fetched(self, client):
        load(client)
        response = client.get("/towers/St Andrew, Marchgate")
        assert response.status_code == 200
        assert response.json()["rings_up_to"] == 8

    def test_lookup_ignores_case(self, client):
        load(client)
        assert client.get("/towers/st andrew, marchgate").status_code == 200

    def test_one_that_is_not_there_is_a_404(self, client):
        assert client.get("/towers/Nowhere").status_code == 404


class TestListing:
    def test_an_empty_store_lists_nothing(self, client):
        assert client.get("/towers").json() == {"count": 0, "towers": []}

    def test_it_lists_what_is_there(self, client):
        load(client)
        assert client.get("/towers").json()["count"] == 3

    def test_the_heaviest_comes_first(self, client):
        load(client)
        body = client.get("/towers").json()
        assert body["towers"][0]["place"] == "All Saints, Kelbrook"

    def test_it_filters_by_place(self, client):
        load(client)
        assert client.get("/towers", params={"place": "Marchgate"}).json()["count"] == 1

    def test_it_filters_by_bells(self, client):
        load(client)
        assert client.get("/towers", params={"min_bells": 8}).json()["count"] == 2

    def test_it_filters_by_tenor_weight(self, client):
        load(client)
        assert client.get("/towers", params={"min_tenor": "20-0-0"}).json()["count"] == 2

    def test_a_weight_it_cannot_read_is_unprocessable(self, client):
        load(client)
        assert client.get("/towers", params={"min_tenor": "heavy"}).status_code == 422

    def test_a_stage_out_of_range_is_rejected(self, client):
        assert client.get("/towers", params={"min_bells": 99}).status_code == 422


class TestDeleting:
    def test_one_can_be_deleted(self, client):
        load(client)
        assert client.delete("/towers/St Mary, Ashcombe").status_code == 204

    def test_it_is_gone_afterwards(self, client):
        load(client)
        client.delete("/towers/St Mary, Ashcombe")
        assert client.get("/towers/St Mary, Ashcombe").status_code == 404

    def test_deleting_one_that_is_not_there_is_a_404(self, client):
        assert client.delete("/towers/Nowhere").status_code == 404
