"""API tests. They swap in a fake `solver` module with a hard-coded path,
so they never depend on (or contain) the group's A* implementation."""

import os
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module  # noqa: E402

START = [1, 2, 3, 4, 5, 6, 0, 7, 8]
MID = [1, 2, 3, 4, 5, 6, 7, 0, 8]
GOAL = [1, 2, 3, 4, 5, 6, 7, 8, 0]


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def fake_solver(monkeypatch, fn):
    module = types.ModuleType("solver")
    if fn is not None:
        module.solve = fn
    monkeypatch.setitem(sys.modules, "solver", module)


def test_valid_path(client, monkeypatch):
    fake_solver(monkeypatch, lambda start: [START, MID, GOAL])
    res = client.post("/api/solve", json={"start": START})
    assert res.status_code == 200
    data = res.get_json()
    assert data["solvable"] is True
    assert data["path"] == [START, MID, GOAL]
    assert data["moves"] == ["right", "right"]
    assert data["nodes_expanded"] is None


def test_dict_result_with_stats(client, monkeypatch):
    fake_solver(monkeypatch, lambda s: {"path": [START, MID, GOAL], "nodes_expanded": 7})
    data = client.post("/api/solve", json={"start": START}).get_json()
    assert data["nodes_expanded"] == 7


def test_already_solved(client, monkeypatch):
    fake_solver(monkeypatch, lambda s: [GOAL])
    data = client.post("/api/solve", json={"start": GOAL}).get_json()
    assert data["path"] == [GOAL] and data["moves"] == []


def test_missing_solver(client, monkeypatch):
    monkeypatch.setitem(sys.modules, "solver", None)  # forces ModuleNotFoundError
    res = client.post("/api/solve", json={"start": START})
    assert res.status_code == 501
    assert res.get_json()["solver_missing"] is True
    assert client.get("/api/health").get_json()["solver_loaded"] is False


def test_solver_without_solve_function(client, monkeypatch):
    fake_solver(monkeypatch, None)
    assert client.post("/api/solve", json={"start": START}).status_code == 501


def test_illegal_step(client, monkeypatch):
    fake_solver(monkeypatch, lambda s: [START, GOAL])  # skips a move
    res = client.post("/api/solve", json={"start": START})
    assert res.status_code == 422
    assert "Illegal step 0 -> 1" in res.get_json()["error"]


def test_path_wrong_start(client, monkeypatch):
    fake_solver(monkeypatch, lambda s: [MID, GOAL])
    assert client.post("/api/solve", json={"start": START}).status_code == 422


def test_unsolvable(client, monkeypatch):
    fake_solver(monkeypatch, lambda s: None)
    data = client.post("/api/solve", json={"start": START}).get_json()
    assert data["solvable"] is False


def test_solver_exception(client, monkeypatch):
    def boom(start):
        raise ValueError("oops")
    fake_solver(monkeypatch, boom)
    res = client.post("/api/solve", json={"start": START})
    assert res.status_code == 500
    assert "oops" in res.get_json()["error"]


@pytest.mark.parametrize("bad", [
    None,
    [1, 2, 3],
    [1, 1, 2, 3, 4, 5, 6, 7, 8],
    [1, 2, 3, 4, 5, 6, 7, 8, 9],
    ["1", 2, 3, 4, 5, 6, 7, 8, 0],
    [True, 2, 3, 4, 5, 6, 7, 8, 0],
])
def test_bad_input(client, monkeypatch, bad):
    fake_solver(monkeypatch, lambda s: [GOAL])
    assert client.post("/api/solve", json={"start": bad}).status_code == 400


def test_health_with_solver(client, monkeypatch):
    fake_solver(monkeypatch, lambda s: [GOAL])
    assert client.get("/api/health").get_json()["solver_loaded"] is True
