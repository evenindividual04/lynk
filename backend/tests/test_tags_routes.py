def _create_person(client, slug: str) -> dict:
    return client.post("/api/people", json={
        "linkedin_url": f"https://www.linkedin.com/in/{slug}/",
        "full_name": slug.replace("-", " ").title(),
        "first_name": "Tag",
        "last_name": "Test",
    }).json()


def test_create_tag(client):
    resp = client.post("/api/tags", json={"name": "vip", "color": "#ff0000"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "vip"


def test_list_tags(client):
    client.post("/api/tags", json={"name": "ps-priority"})
    resp = client.get("/api/tags")
    assert resp.status_code == 200
    names = [t["name"] for t in resp.json()]
    assert "ps-priority" in names


def test_add_tag_to_person(client):
    person = _create_person(client, "tag-person-1")
    resp = client.post(f"/api/people/{person['id']}/tags", json={"name": "recruiter"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "recruiter"


def test_tag_appears_in_person_detail(client):
    person = _create_person(client, "tag-person-2")
    client.post(f"/api/people/{person['id']}/tags", json={"name": "hot-lead"})
    detail = client.get(f"/api/people/{person['id']}").json()
    assert any(t["name"] == "hot-lead" for t in detail["tags"])


def test_remove_tag_from_person(client):
    person = _create_person(client, "tag-person-3")
    tag = client.post(f"/api/people/{person['id']}/tags", json={"name": "to-remove"}).json()
    resp = client.delete(f"/api/people/{person['id']}/tags/{tag['id']}")
    assert resp.status_code == 204
    detail = client.get(f"/api/people/{person['id']}").json()
    assert not any(t["name"] == "to-remove" for t in detail["tags"])


def test_add_tag_person_not_found(client):
    resp = client.post("/api/people/99999/tags", json={"name": "ghost"})
    assert resp.status_code == 404
