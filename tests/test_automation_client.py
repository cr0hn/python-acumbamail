import pytest
from pytest_httpx import HTTPXMock
from acumbamail.automation_client import AutomationClient

BASE = "https://acumbamail.com"
LOGIN_HTML = '<form><input name="csrfmiddlewaretoken" value="csrf_token_123"></form>'


@pytest.fixture
def client():
    return AutomationClient("user@test.com", "password123")


def mock_login(httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/login/", text=LOGIN_HTML, status_code=200)
    httpx_mock.add_response(
        method="POST", url=f"{BASE}/login/2fa/",
        text="<html>ok</html>",
        status_code=200,
        headers={"Set-Cookie": "sessionid=test_session_123; Path=/; HttpOnly"},
    )


class TestLogin:
    def test_login_extracts_and_stores_csrf(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        client.login()
        assert client._csrf_token == "csrf_token_123"

    def test_login_sends_credentials_in_post(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        client.login()
        requests = httpx_mock.get_requests()
        post_req = requests[1]
        assert post_req.method == "POST"
        assert "/login/2fa/" in str(post_req.url)
        body = post_req.content.decode()
        assert "auth-username" in body
        assert "auth-password" in body
        assert "user%40test.com" in body or "user@test.com" in body
        assert "password123" in body

    def test_extract_csrf_from_html(self, client):
        html = '<input name="csrfmiddlewaretoken" value="abc123">'
        assert client._extract_csrf(html) == "abc123"

    def test_extract_csrf_raises_if_missing(self, client):
        with pytest.raises(ValueError, match="CSRF token not found"):
            client._extract_csrf("<html>no token here</html>")

    def test_login_updates_csrf_from_post_response(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            method="GET", url=f"{BASE}/login/",
            text='<input name="csrfmiddlewaretoken" value="old_csrf">',
            status_code=200,
        )
        httpx_mock.add_response(
            method="POST", url=f"{BASE}/login/2fa/",
            text='<input name="csrfmiddlewaretoken" value="new_csrf_456">',
            status_code=200,
            headers={"Set-Cookie": "sessionid=test_session_123; Path=/; HttpOnly"},
        )
        client.login()
        assert client._csrf_token == "new_csrf_456"

    def test_login_raises_if_no_session_cookie(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(method="GET", url=f"{BASE}/login/", text=LOGIN_HTML, status_code=200)
        httpx_mock.add_response(
            method="POST", url=f"{BASE}/login/2fa/",
            text="<html>wrong credentials</html>",
            status_code=200,
        )
        with pytest.raises(ValueError, match="Login failed"):
            client.login()

    def test_context_manager_calls_login(self, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        with AutomationClient("user@test.com", "password123") as client:
            assert client._csrf_token == "csrf_token_123"


WORKFLOW_BASIC = {"id": 35925, "name": "test", "description": None, "active": True, "booting": False}
WORKFLOW_FULL = {
    "id": "35925", "name": "test", "description": None,
    "active": True, "booting": False,
    "entry_point": {"id": "234068", "parent_id": 0, "workflow": 35925, "nodeType": "Trigger", "siblings": []},
}


class TestListWorkflows:
    def test_returns_list_of_automations(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(
            url=f"{BASE}/automation/api/basic-workflow/",
            json=[WORKFLOW_BASIC],
        )
        client.login()
        result = client.list_workflows()
        assert len(result) == 1
        assert result[0].id == 35925
        assert result[0].name == "test"

    def test_returns_empty_list(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(url=f"{BASE}/automation/api/basic-workflow/", json=[])
        client.login()
        assert client.list_workflows() == []


class TestGetWorkflow:
    def test_returns_automation_with_entry_point(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(url=f"{BASE}/automation/api/workflow/35925/", json=WORKFLOW_FULL)
        client.login()
        result = client.get_workflow(35925)
        assert result.id == 35925
        assert result.entry_point is not None
        assert result.entry_point.node_type == "Trigger"


class TestCreateWorkflow:
    def test_posts_name_and_description(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="POST",
            url=f"{BASE}/automation/api/workflow/",
            json=WORKFLOW_FULL,
            status_code=201,
        )
        client.login()
        result = client.create_workflow("test", "desc")
        post_req = httpx_mock.get_requests()[-1]
        body = _json.loads(post_req.content)
        assert body["name"] == "test"
        assert body["description"] == "desc"
        assert result.id == 35925

    def test_description_can_be_none(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(method="POST", url=f"{BASE}/automation/api/workflow/", json=WORKFLOW_FULL, status_code=201)
        client.login()
        client.create_workflow("test")
        post_req = httpx_mock.get_requests()[-1]
        body = _json.loads(post_req.content)
        assert "description" not in body


class TestDeleteWorkflow:
    def test_sends_delete_request(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(method="DELETE", url=f"{BASE}/automation/api/workflow/35925/", status_code=204)
        client.login()
        result = client.delete_workflow(35925)
        delete_req = httpx_mock.get_requests()[-1]
        assert delete_req.method == "DELETE"
        assert result is None


class TestActivateWorkflow:
    def test_activate_sends_patch_with_active_true(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="PATCH",
            url=f"{BASE}/automation/api/basic-workflow/35925/",
            json={**WORKFLOW_BASIC, "active": True},
        )
        client.login()
        result = client.activate_workflow(35925)
        patch_req = httpx_mock.get_requests()[-1]
        body = _json.loads(patch_req.content)
        assert body["active"] is True
        assert result.active is True

    def test_deactivate_sends_patch_with_active_false(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="PATCH",
            url=f"{BASE}/automation/api/basic-workflow/35925/",
            json={**WORKFLOW_BASIC, "active": False},
        )
        client.login()
        client.deactivate_workflow(35925)
        patch_req = httpx_mock.get_requests()[-1]
        body = _json.loads(patch_req.content)
        assert body["active"] is False


class TestUpdateWorkflow:
    def test_raises_when_no_kwargs(self, client):
        with pytest.raises(ValueError, match="At least one"):
            client.update_workflow(35925)


NODE_DELAY_RESPONSE = {
    "id": "275481", "parent_id": 0, "workflow": 36215,
    "nodeType": "Delay", "wait_time": 1, "wait_unit": 2, "siblings": [],
}


class TestNodeCRUD:
    def test_create_node_posts_correct_payload(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="POST",
            url=f"{BASE}/automation/api/delay/",
            json=NODE_DELAY_RESPONSE,
            status_code=201,
        )
        client.login()
        result = client.create_node("Delay", 36215, "235966")
        post_req = httpx_mock.get_requests()[-1]
        body = _json.loads(post_req.content)
        assert body["sourceId"] == "235966"
        assert body["nodeType"] == "Delay"
        assert body["workflow"] == "36215"
        assert result["id"] == "275481"

    def test_create_node_uses_lowercase_nodetype_in_url(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="POST",
            url=f"{BASE}/automation/api/sendtemplate/",
            json={"id": "999", "nodeType": "SendTemplate", "workflow": 1, "siblings": []},
            status_code=201,
        )
        client.login()
        client.create_node("SendTemplate", 1, "100")
        post_req = httpx_mock.get_requests()[-1]
        assert "/automation/api/sendtemplate/" in str(post_req.url)

    def test_update_node_sends_put(self, client, httpx_mock: HTTPXMock):
        import json as _json
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="PUT",
            url=f"{BASE}/automation/api/delay/275481/",
            json={**NODE_DELAY_RESPONSE, "wait_time": 3},
        )
        client.login()
        result = client.update_node("Delay", "275481", {**NODE_DELAY_RESPONSE, "wait_time": 3})
        put_req = httpx_mock.get_requests()[-1]
        body = _json.loads(put_req.content)
        assert body["wait_time"] == 3
        assert result["wait_time"] == 3

    def test_delete_node_sends_delete(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        httpx_mock.add_response(
            method="DELETE",
            url=f"{BASE}/automation/api/delay/275481/",
            status_code=204,
        )
        client.login()
        client.delete_node("Delay", "275481")
        delete_req = httpx_mock.get_requests()[-1]
        assert delete_req.method == "DELETE"
        assert "/automation/api/delay/275481/" in str(delete_req.url)
