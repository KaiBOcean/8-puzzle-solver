// Thin wrappers around the Flask API in backend/app.py.

export async function getHealth() {
  const res = await fetch('/api/health')
  if (!res.ok) throw new Error(`Health check failed (${res.status})`)
  return res.json()
}

/**
 * Ask the backend (and therefore backend/solver.py) to solve `start`.
 * Resolves to { solvable, path, moves, nodes_expanded, time_ms }.
 * Rejects with an Error whose `.status` and `.solverMissing` describe the failure.
 */
export async function solvePuzzle(start) {
  let res
  try {
    res = await fetch('/api/solve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ start }),
    })
  } catch {
    throw new Error('Could not reach the Flask server. Is it running on port 5001?')
  }
  let data = {}
  try {
    data = await res.json()
  } catch {
    // non-JSON response (e.g. proxy error page)
  }
  if (!res.ok) {
    const err = new Error(data.error || `Request failed (${res.status})`)
    err.status = res.status
    err.solverMissing = Boolean(data.solver_missing)
    throw err
  }
  return data
}
