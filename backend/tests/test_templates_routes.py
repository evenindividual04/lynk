def test_create_template(client):
    resp = client.post(
        "/api/templates",
        json={
            "name": "My template",
            "scenario": "ps_outreach",
            "channel": "cold_email",
            "body_template": "Hi {{ person.first_name }}",
            "subject_template": "Hello from {{ company.name }}",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My template"
    assert data["scenario"] == "ps_outreach"
    assert data["channel"] == "cold_email"
    assert data["active_version_id"] is not None


def test_list_templates(client):
    client.post(
        "/api/templates",
        json={
            "name": "T1",
            "scenario": "alumni",
            "channel": "li_dm",
            "body_template": "Hello",
        },
    )
    client.post(
        "/api/templates",
        json={
            "name": "T2",
            "scenario": "founder",
            "channel": "li_connection_note",
            "body_template": "Hi",
        },
    )
    resp = client.get("/api/templates")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_list_templates_filter_by_scenario(client):
    client.post(
        "/api/templates",
        json={
            "name": "Scenario Filter",
            "scenario": "research_gsoc",
            "channel": "li_dm",
            "body_template": "Hi",
        },
    )
    resp = client.get("/api/templates?scenario=research_gsoc")
    assert resp.status_code == 200
    assert all(t["scenario"] == "research_gsoc" for t in resp.json())


def test_get_template_detail(client):
    created = client.post(
        "/api/templates",
        json={
            "name": "Detail test",
            "scenario": "info_call",
            "channel": "cold_email",
            "body_template": "Hello {{ person.full_name }}",
        },
    ).json()

    resp = client.get(f"/api/templates/{created['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["versions"]) == 1
    assert data["versions"][0]["version"] == 1


def test_add_version_auto_increments(client):
    created = client.post(
        "/api/templates",
        json={
            "name": "Versioned",
            "scenario": "referral_request",
            "channel": "li_dm",
            "body_template": "v1 body",
        },
    ).json()
    tmpl_id = created["id"]

    resp = client.post(f"/api/templates/{tmpl_id}/versions", json={"body_template": "v2 body"})
    assert resp.status_code == 201
    assert resp.json()["version"] == 2

    detail = client.get(f"/api/templates/{tmpl_id}").json()
    assert len(detail["versions"]) == 2
    assert detail["active_version_id"] == resp.json()["id"]


def test_update_template_active_version(client):
    created = client.post(
        "/api/templates",
        json={
            "name": "Set active",
            "scenario": "alumni",
            "channel": "li_dm",
            "body_template": "v1",
        },
    ).json()
    tmpl_id = created["id"]
    v1_id = created["active_version_id"]

    client.post(f"/api/templates/{tmpl_id}/versions", json={"body_template": "v2"})

    # Revert to v1
    resp = client.patch(f"/api/templates/{tmpl_id}", json={"active_version_id": v1_id})
    assert resp.status_code == 200
    assert resp.json()["active_version_id"] == v1_id
