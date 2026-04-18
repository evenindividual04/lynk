def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_people_empty(client):
    resp = client.get("/api/people")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_create_person(client):
    payload = {
        "linkedin_url": "https://www.linkedin.com/in/jane-doe/",
        "full_name": "Jane Doe",
        "first_name": "Jane",
        "last_name": "Doe",
    }
    resp = client.post("/api/people", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["linkedin_url"] == "https://www.linkedin.com/in/jane-doe/"
    assert data["source"] == "manual"


def test_create_person_normalizes_url(client):
    payload = {
        "linkedin_url": "http://linkedin.com/in/Jane-Doe",
        "full_name": "Jane Doe",
        "first_name": "Jane",
        "last_name": "Doe",
    }
    resp = client.post("/api/people", json=payload)
    assert resp.status_code == 201
    assert resp.json()["linkedin_url"] == "https://www.linkedin.com/in/jane-doe/"


def test_get_person_not_found(client):
    resp = client.get("/api/people/99999")
    assert resp.status_code == 404


def test_get_person_detail(client):
    payload = {
        "linkedin_url": "https://www.linkedin.com/in/detail-test/",
        "full_name": "Detail Test",
        "first_name": "Detail",
        "last_name": "Test",
    }
    created = client.post("/api/people", json=payload).json()
    resp = client.get(f"/api/people/{created['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tags"] == []
    assert data["notes"] == []


def test_patch_person_stage(client):
    payload = {
        "linkedin_url": "https://www.linkedin.com/in/patch-test/",
        "full_name": "Patch Test",
        "first_name": "Patch",
        "last_name": "Test",
    }
    person_id = client.post("/api/people", json=payload).json()["id"]
    resp = client.patch(f"/api/people/{person_id}", json={"stage": "contacted_li"})
    assert resp.status_code == 200
    assert resp.json()["stage"] == "contacted_li"


def test_list_people_filter_q(client):
    for name in ["Alice Smith", "Bob Jones"]:
        first, last = name.split()
        client.post("/api/people", json={
            "linkedin_url": f"https://www.linkedin.com/in/{name.lower().replace(' ', '-')}/",
            "full_name": name,
            "first_name": first,
            "last_name": last,
        })
    resp = client.get("/api/people?q=Alice")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["full_name"] == "Alice Smith"


def test_pagination(client):
    for i in range(5):
        client.post("/api/people", json={
            "linkedin_url": f"https://www.linkedin.com/in/person-{i}/",
            "full_name": f"Person {i}",
            "first_name": "Person",
            "last_name": str(i),
        })
    resp = client.get("/api/people?page=1&page_size=2")
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
