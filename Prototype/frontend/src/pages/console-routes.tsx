import { useEffect, useMemo, useState } from 'react'
import { Dashboard } from '../components/Dashboard'
import { ImageDetect } from '../components/ImageDetect'
import { VideoDetect } from '../components/VideoDetect'
import { WebcamDetect } from '../components/WebcamDetect'
import { fetchCompare } from '../lib/api'
import { Button, Card } from '../ui/components'
import { BarChart3, Cpu, Gauge, RefreshCw, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

export function ComparePage() {
  const [compare, setCompare] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  async function refresh() {
    setError(null)
    try {
      setCompare(await fetchCompare())
    } catch (e: any) {
      setError(e?.message ?? String(e))
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  const cards = useMemo(() => {
    const by = compare?.by_model ?? {}
    return Object.entries(by).map(([k, v]: any) => ({
      model: k,
      count: v.count ?? 0,
      ms: v.avg_processing_ms ?? null,
      fps: v.avg_fps ?? null,
    }))
  }, [compare])

  return (
    <div className="vb-stack">
      <div className="vb-pageHead">
        <div>
          <div className="vb-pageTitle">Model Comparison</div>
          <div className="vb-muted">Premium comparison view across stored performance runs.</div>
        </div>
        <div className="vb-pageActions">
          <Button variant="soft" onClick={refresh}>
            <span className="vb-inlineIcon"><RefreshCw size={16} /></span>
            Refresh
          </Button>
          <Link to="/console/image">
            <Button>
              <span className="vb-inlineIcon"><Sparkles size={16} /></span>
              Run a test
            </Button>
          </Link>
        </div>
      </div>

      {error ? <div className="error">{error}</div> : null}

      <Card className="vb-block">
        <div className="vb-blockHead">
          <div>
            <div className="vb-blockTitle">Averages by model</div>
            <div className="vb-muted">Latency and throughput from historical runs.</div>
          </div>
        </div>
        <div className="vb-compareRow">
          {cards.map((c) => (
            <div key={c.model} className="vb-compareCard">
              <div className="vb-compareName">{String(c.model).toUpperCase()}</div>
              <div className="vb-compareMeta">
                <BarChart3 size={14} /> {c.count} runs
              </div>
              <div className="vb-compareStats">
                <div>
                  <div className="vb-compareLbl"><Gauge size={14} /> Avg ms</div>
                  <div className="vb-compareVal">{c.ms ? Math.round(c.ms) : '—'}</div>
                </div>
                <div>
                  <div className="vb-compareLbl"><Cpu size={14} /> Avg FPS</div>
                  <div className="vb-compareVal">{c.fps ? Number(c.fps).toFixed(1) : '—'}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card className="vb-block">
        <div className="vb-blockHead">
          <div>
            <div className="vb-blockTitle">Operational dashboard</div>
            <div className="vb-muted">Runs, queue status, and downloads.</div>
          </div>
        </div>
        <Dashboard />
      </Card>
    </div>
  )
}

export const ConsoleRoutes = {
  Dashboard,
  WebcamDetect,
  ImageDetect,
  VideoDetect,
  ComparePage,
}

