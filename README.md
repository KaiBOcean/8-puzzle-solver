# 8-puzzle-solver

8-puzzle A* solver and web app visualization.

## Solver file

**The A\* solver is [`backend/solver.py`](backend/solver.py). Our group wrote it entirely by hand, with no AI-generated code.**

Every other file in this repo is visualization or glue code (the React front end in `frontend/` and the Flask API in `backend/app.py`). Generative AI was used only for that front-end/visualization part, which the assignment allows.

GitHub repository: <!-- TODO: paste the repo link here and in the report -->

## How the app talks to the solver

`backend/app.py` imports `solver.py` and calls one function:

```python
solve(start: list[int]) -> list[list[int]] | None
```

- A **state** is a flat list of 9 ints, row by row, with `0` as the blank.
  Example: `[1, 2, 3, 4, 5, 6, 7, 0, 8]` is

  ```
  1 2 3
  4 5 6
  7 _ 8
  ```
- The goal is always `[1, 2, 3, 4, 5, 6, 7, 8, 0]`.
- Return the path from `start` to the goal, **including both the start and the goal**. If `start` is already the goal, return `[start]`.
- Return `None` if the puzzle can't be solved.
- Optional: return a dict to show search stats in the UI:
  `{"path": [...], "nodes_expanded": 1234}`

The API checks the returned path: it must begin at `start`, end at the goal, and every step must slide the blank by one cell. If it doesn't, the app shows the step that broke. Until `solver.py` exists, the app runs and shows a "solver not available" banner.

## Running it

You need Python 3.10+ and Node 20+.

**1. Backend (Flask, port 5001).** From the repo root:

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r backend/requirements.txt
```

```bash
python backend/app.py
```

(The app uses port 5001 because macOS uses 5000 for AirPlay Receiver.)

**2. Front end (React + Vite, port 5173).** In a second terminal:

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:5173.

## Using the app

- Enter a start state in the 3×3 grid (leave one cell empty for the blank), click **Shuffle** for a random solvable start, or pick a preset.
- Click **Solve with A\***. The board animates through the path. Use ⏮ ◀ ▶ ▶ ⏭, the speed slider, or the ← / → / space keys.
- The **All steps** strip shows every state from start to goal. Click any of them to jump there.

## Tests

The API tests use a fake solver that returns a hard-coded path. They don't depend on, or contain, our A* code.

```bash
python -m pytest backend/tests
```

## Project layout

```
backend/
  app.py            Flask API (visualization glue)
  solver.py         A* solver (written by our group)
  tests/test_api.py API tests
frontend/
  src/App.jsx       page layout and state
  src/api.js        calls to the Flask API
  src/puzzle.js     board helpers (input checks, shuffle, labels)
  src/components/   Board, StateInput, PlaybackControls, StepList
```
