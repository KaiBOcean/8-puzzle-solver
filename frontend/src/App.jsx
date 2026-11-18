import { useCallback, useEffect, useMemo, useState } from 'react'
import { getHealth, solvePuzzle } from './api.js'
import { GOAL, PRESETS, describeStep, validateCells } from './puzzle.js'
import Board from './components/Board.jsx'
import StateInput, { toCells } from './components/StateInput.jsx'
import PlaybackControls from './components/PlaybackControls.jsx'
import StepList from './components/StepList.jsx'

export default function App() {
  const [cells, setCells] = useState(() => toCells(PRESETS[1].state))
  const [result, setResult] = useState(null) // { path, moves, nodes_expanded, time_ms }
  const [status, setStatus] = useState({ kind: 'idle' }) // idle | loading | error | unsolvable
  const [health, setHealth] = useState(null)
  const [step, setStep] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(600)

  const { state: startState, error: inputError } = validateCells(cells)

  const refreshHealth = useCallback(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth({ ok: false, solver_loaded: false, error: 'Could not reach the Flask server on port 5001.' }))
  }, [])

  useEffect(refreshHealth, [refreshHealth])

  const handleCellsChange = (next) => {
    setCells(next)
    setResult(null)
    setStatus({ kind: 'idle' })
    setPlaying(false)
    setStep(0)
  }

  const handleSolve = async () => {
    if (!startState) return
    setStatus({ kind: 'loading' })
    setResult(null)
    setPlaying(false)
    setStep(0)
    try {
      const data = await solvePuzzle(startState)
      if (!data.solvable) {
        setStatus({ kind: 'unsolvable', time_ms: data.time_ms })
      } else {
        setResult(data)
        setStatus({ kind: 'idle' })
      }
    } catch (err) {
      setStatus({ kind: 'error', message: err.message, solverMissing: err.solverMissing })
    }
    refreshHealth()
  }

  const total = result ? result.path.length : 1
  const goTo = useCallback((i) => setStep(Math.max(0, Math.min(total - 1, i))), [total])

  // Auto-play
  useEffect(() => {
    if (!playing) return
    if (step >= total - 1) {
      setPlaying(false)
      return
    }
    const id = setTimeout(() => setStep((s) => s + 1), speed)
    return () => clearTimeout(id)
  }, [playing, step, total, speed])

  const togglePlay = () => {
    if (!playing && step >= total - 1) setStep(0)
    setPlaying((p) => !p)
  }

  // Keyboard: ←/→ step, space play/pause (ignored while typing in an input)
  useEffect(() => {
    if (!result) return
    const onKey = (e) => {
      if (e.target instanceof HTMLInputElement && e.target.type !== 'range') return
      if (e.key === 'ArrowRight') goTo(step + 1)
      else if (e.key === 'ArrowLeft') goTo(step - 1)
      else if (e.key === ' ') {
        e.preventDefault()
        togglePlay()
      } else return
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  const labels = useMemo(() => {
    if (!result) return []
    return result.path.map((s, i) => describeStep(result.path[i - 1], s, result.moves[i - 1]))
  }, [result])

  const shownState = result ? result.path[step] : startState ?? GOAL
  const movedTile = result && step > 0 ? result.path[step - 1][shownState.indexOf(0)] : null
  const solverMissing = health && !health.solver_loaded

  return (
    <div className="app">
      <header className="app-header">
        <h1>8-Puzzle A* Visualizer</h1>
        <p className="subtitle">
          Goal: <code>1 2 3 / 4 5 6 / 7 8 _</code> · Solver: <code>backend/solver.py</code>
        </p>
      </header>

      {solverMissing && (
        <div className="banner banner--warn" role="status">
          <strong>Solver not available.</strong> {health.error}
        </div>
      )}

      <main className="layout">
        <StateInput
          cells={cells}
          onCellsChange={handleCellsChange}
          onSolve={handleSolve}
          error={inputError}
          busy={status.kind === 'loading'}
        />

        <section className="panel viewer" aria-labelledby="viewer-heading">
          <h2 id="viewer-heading">{result ? 'Solution' : 'Preview'}</h2>
          <Board state={shownState} highlightTile={movedTile} />

          {result && (
            <>
              <PlaybackControls
                step={step}
                total={total}
                playing={playing}
                speed={speed}
                label={labels[step]}
                onStep={goTo}
                onTogglePlay={togglePlay}
                onSpeedChange={setSpeed}
              />
              <dl className="stats">
                <div><dt>Moves</dt><dd>{result.path.length - 1}</dd></div>
                <div><dt>Nodes expanded</dt><dd>{result.nodes_expanded ?? '—'}</dd></div>
                <div><dt>Solve time</dt><dd>{formatMs(result.time_ms)}</dd></div>
              </dl>
            </>
          )}

          {status.kind === 'loading' && <p className="status">Running A*…</p>}
          {status.kind === 'unsolvable' && (
            <p className="status status--warn">The solver reports this start state has no solution.</p>
          )}
          {status.kind === 'error' && (
            <p className={`status ${status.solverMissing ? 'status--warn' : 'status--error'}`} role="alert">
              {status.message}
            </p>
          )}
          {status.kind === 'idle' && !result && (
            <p className="status">Pick a start state and press <strong>Solve with A*</strong>.</p>
          )}
        </section>
      </main>

      {result && (
        <StepList path={result.path} labels={labels} current={step} onSelect={(i) => { setPlaying(false); goTo(i) }} />
      )}

      <footer className="app-footer">
        The A* search is in <code>backend/solver.py</code>, written by the group. This interface only displays its output.
      </footer>
    </div>
  )
}

function formatMs(ms) {
  if (ms == null) return '—'
  return ms < 1 ? `${(ms * 1000).toFixed(0)} µs` : ms < 1000 ? `${ms.toFixed(1)} ms` : `${(ms / 1000).toFixed(2)} s`
}
