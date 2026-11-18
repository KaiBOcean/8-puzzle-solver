"""Flask API that connects the React visualization to the group's A* solver.

This file is glue/visualization support code only. It contains NO search
logic. The A* solver lives in backend/solver.py and is written by the group.

Expected solver contract (see README.md):

    solve(start: list[int]) -> list[list[int]] | dict | None

    * A state is a flat list of 9 ints, row by row, 0 = blank.
    * Return the path from start to GOAL, including both ends,
      or None if the puzzle cannot be solved.
    * Optionally return {"path": [...], "nodes_expanded": int}.
"""

import importlib
import os
import sys
import time

from flask import Flask, jsonify, request

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

GOAL = [1, 2, 3, 4, 5, 6, 7, 8, 0]
SOLVER_MISSING_MSG = (
    "solver.py not found. Implement solve(start) in backend/solver.py."
)

app = Flask(__name__)


class SolverUnavailable(Exception):
    """Raised when backend/solver.py or its solve() function is missing."""


def load_solve():
    """Import the group's solver lazily so the app runs before it exists."""
    try:
        module = importlib.import_module("solver")
    except ModuleNotFoundError as exc:
        # Only treat it as "missing" if solver.py itself is absent, not if
        # solver.py imports something that is missing.
        if exc.name == "solver":
            raise SolverUnavailable(SOLVER_MISSING_MSG) from exc
        raise
    solve = getattr(module, "solve", None)
    if not callable(solve):
        raise SolverUnavailable(
            "backend/solver.py was found but has no solve(start) function."
        )
    return solve


def is_valid_state(state):
    return (
        isinstance(state, list)
        and len(state) == 9
        and all(isinstance(v, int) and not isinstance(v, bool) for v in state)
        and sorted(state) == list(range(9))
    )


def blank_move(a, b):
    """Name the move the blank made from state a to state b, or None if the
    step is not a single legal slide."""
    ia, ib = a.index(0), b.index(0)
    ra, ca = divmod(ia, 3)
    rb, cb = divmod(ib, 3)
    if abs(ra - rb) + abs(ca - cb) != 1:
        return None
    expected = list(a)
    expected[ia], expected[ib] = expected[ib], expected[ia]
    if expected != b:
        return None
    if rb < ra:
        return "up"
    if rb > ra:
        return "down"
    if cb < ca:
        return "left"
    return "right"


def check_path(start, path):
    """Return (moves, error_message). Checks the solver's output only."""
    if not isinstance(path, (list, tuple)) or len(path) == 0:
        return None, "Solver returned an empty or non-list path."
    path = [list(s) if isinstance(s, (list, tuple)) else s for s in path]
    for i, state in enumerate(path):
        if not is_valid_state(state):
            return None, f"Step {i} is not a valid state: {state!r}"
    if path[0] != start:
        return None, f"Path must start with the start state, got {path[0]}."
    if path[-1] != GOAL:
        return None, f"Path must end with the goal state, got {path[-1]}."
    moves = []
    for i in range(len(path) - 1):
        move = blank_move(path[i], path[i + 1])
        if move is None:
            return None, (
                f"Illegal step {i} -> {i + 1}: {path[i]} -> {path[i + 1]} "
                "is not a single slide of the blank."
            )
        moves.append(move)
    return (path, moves), None


@app.get("/api/health")
def health():
    try:
        load_solve()
        loaded, error = True, None
    except SolverUnavailable as exc:
        loaded, error = False, str(exc)
    except Exception as exc:  # solver.py exists but fails to import
        loaded, error = False, f"solver.py failed to import: {exc!r}"
    return jsonify({"ok": True, "solver_loaded": loaded, "error": error})


@app.post("/api/solve")
def solve_endpoint():
    body = request.get_json(silent=True) or {}
    start = body.get("start")
    if not is_valid_state(start):
        return jsonify({
            "error": "start must be a list of 9 integers using 0-8 exactly once."
        }), 400

    try:
        solve = load_solve()
    except SolverUnavailable as exc:
        return jsonify({"error": str(exc), "solver_missing": True}), 501
    except Exception as exc:
        return jsonify({"error": f"solver.py failed to import: {exc!r}"}), 500

    t0 = time.perf_counter()
    try:
        result = solve(list(start))
    except Exception as exc:
        return jsonify({"error": f"solve() raised {exc!r}"}), 500
    time_ms = (time.perf_counter() - t0) * 1000

    if result is None:
        return jsonify({"solvable": False, "time_ms": time_ms})

    nodes_expanded = None
    path = result
    if isinstance(result, dict):
        path = result.get("path")
        nodes_expanded = result.get("nodes_expanded")
        if path is None:
            return jsonify({"solvable": False, "time_ms": time_ms,
                            "nodes_expanded": nodes_expanded})

    checked, error = check_path(start, path)
    if error:
        return jsonify({"error": f"Invalid solver output: {error}"}), 422
    path, moves = checked

    return jsonify({
        "solvable": True,
        "path": path,
        "moves": moves,
        "nodes_expanded": nodes_expanded,
        "time_ms": time_ms,
    })


if __name__ == "__main__":
    # Port 5001 because macOS uses 5000 for AirPlay Receiver.
    app.run(debug=True, port=5001)
