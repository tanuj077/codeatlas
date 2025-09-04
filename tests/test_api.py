import pytest
from fastapi.testclient import TestClient
from app.api import search
from app.main import app
from app.dependencies import get_code_searcher, get_chat_service

class DummySearcher:
    def semantic_search(self, repo_name, query, top_k=10):
        return [(0.99, {"path": "dummy.py", "name": "dummy_func", "type": "function", 
                        "start_line": 1, "end_line": 2})]
        
class DummySearcherEmpty:
    def semantic_search(self, repo_name, query, top_k=10):
        return []

class DummyChatService:
    def answer_question(self, repo_name, query):
        return "Dummy Answer"
    
client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "CodeAtlas API running"

def test_repos_endpoint():
    response = client.get("/repos/")
    assert response.status_code == 200
    assert "repos" in response.json()
    
def test_search_endpoint():
    app.dependency_overrides[get_code_searcher] = lambda repo_name : DummySearcher()
    params = {"repo_name": "dummy_repo", "query": "my_query", "top_k": 1}
    response = client.get("/search", params=params)
    assert response.status_code == 200
    assert "results" in response.json()
    assert isinstance(response.json()["results"], list)
    app.dependency_overrides = {}


def test_chat_endpoint():
    app.dependency_overrides[get_chat_service] = lambda repo_name : DummyChatService() 
    payload = {"query": "What is the functionality of xyz class"}
    response = client.post("/chat?repo_name=dummy_repo", json=payload)
    assert response.status_code == 200
    assert "answer" in response.json()
    app.dependency_overrides = {}

def test_search_missing_query():
    app.dependency_overrides[get_code_searcher] = lambda repo_name : DummySearcherEmpty()
    params = {"repo_name": "dummy_repo"}
    response = client.get("/search", params=params)
    assert response.status_code == 422
    app.dependency_overrides = {}

def test_search_empty_query():
    app.dependency_overrides[get_code_searcher] = lambda repo_name : DummySearcherEmpty()
    params = {"repo_name": "my_project", "query": ""}
    response = client.get("/search", params=params)
    assert response.status_code == 400
    assert response.json().get("detail") == "Query cannot be empty."
    app.dependency_overrides = {}

def test_chat_missing_payload():
    app.dependency_overrides[get_chat_service] = lambda repo_name : DummyChatService()
    response = client.post("/chat?repo_name=my_project")
    assert response.status_code == 422
    app.dependency_overrides = {}

