import { useEffect, useMemo, useState } from 'react'
import { downloadRunUrl, fetchCompare, fetchRecentRuns } from '../lib/api'
import { getToken } from '../lib/auth'
import { JobsList } from './JobsList'
import { Card, Button } from '../ui/components'
import { BarChart3, Clock, Cpu, Download, Gauge, RefreshCw, Trophy, Video } from 'lucide-react'

export function Dashboard() {
  const [compare, setCompare] = useState<any>(null)
  const [recent, setRecent] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  async function refresh() {
    setError(null)
    try {
      const [c, r] = await Promise.all([fetchCompare(), fetchRecentRuns()])
      setCompare(c)
      setRecent(r)
    } catch (e: any) {
      setError(e?.message ?? String(e))
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  const compareCards = useMemo(() => {
    const by = compare?.by_model ?? {}
    const items = Object.entries(by).map(([model, v]: any) => ({
      model,
      count: v.count ?? 0,
      avgMs: v.avg_processing_ms ?? null,
      avgFps: v.avg_fps ?? null,
    }))
    const order = ['yolo', 'ssd', 'fasterrcnn']
    items.sort((a, b) => order.indexOf(a.model) - order.indexOf(b.model))
    return items
  }, [compare])

  const summary = useMemo(() => {
    const runs = recent?.runs ?? []
    const totalRuns = runs.length
    const totalDetections = runs.reduce((acc: number, r: any) => acc + (Number(r.detections_count ?? r.num_detections ?? 0) || 0), 0)
    const bestLatency = compareCards
      .filter((c) => c.avgMs != null)
      .slice()
      .sort((a, b) => Number(a.avgMs) - Number(b.avgMs))[0]
    const bestFps = compareCards
      .filter((c) => c.avgFps != null)
      .slice()
      .sort((a, b) => Number(b.avgFps) - Number(a.avgFps))[0]
    const latest = runs[0] ?? null
    const maxMs = Math.max(1, ...compareCards.map((c) => Number(c.avgMs ?? 0)))
    const maxFps = Math.max(1, ...compareCards.map((c) => Number(c.avgFps ?? 0)))
    return { totalRuns, totalDetections, bestLatency, bestFps, latest, maxMs, maxFps }
  }, [compareCards, recent])

  return (
    <div className="vb-stack">
      <div className="vb-pageHead">
        <div>
          <div className="vb-pageTitle">Executive Overview</div>
          <div className="vb-muted">Benchmarked runtime metrics across recent runs.</div>
        </div>
        <div className="vb-pageActions">
          <Button variant="soft" onClick={refresh}>
            <span className="vb-inlineIcon"><RefreshCw size={16} /></span>
            Refresh
          </Button>
        </div>
      </div>

      {error ? <div className="error">{error}</div> : null}

      <div className="vb-kpiGrid">
        <Card className="vb-kpi">
          <div className="vb-kpiIcon"><BarChart3 size={18} /></div>
          <div>
            <div className="vb-kpiLabel">Models</div>
            <div className="vb-kpiValue">3</div>
          </div>
        </Card>
        <Card className="vb-kpi">
          <div className="vb-kpiIcon"><Clock size={18} /></div>
          <div>
            <div className="vb-kpiLabel">Recent runs</div>
            <div className="vb-kpiValue">{summary.totalRuns || '—'}</div>
          </div>
        </Card>
        <Card className="vb-kpi">
          <div className="vb-kpiIcon"><Cpu size={18} /></div>
          <div>
            <div className="vb-kpiLabel">Device</div>
            <div className="vb-kpiValue">{summary.latest?.device ?? '—'}</div>
          </div>
        </Card>
        <Card className="vb-kpi">
          <div className="vb-kpiIcon"><Video size={18} /></div>
          <div>
            <div className="vb-kpiLabel">Best avg FPS</div>
            <div className="vb-kpiValue">
              {summary.bestFps?.avgFps ? Number(summary.bestFps.avgFps).toFixed(1) : '—'}
            </div>
          </div>
        </Card>
      </div>

      <div className="vb-sectionGrid">
        <Card className="vb-block">
          <div className="vb-blockHead">
            <div>
              <div className="vb-blockTitle">Model comparison</div>
              <div className="vb-muted">Average latency and FPS from stored runs.</div>
            </div>
          </div>
          <div className="vb-compareRow">
            {compareCards.map((c: any) => (
              <div key={c.model} className="vb-compareCard">
                <div className="vb-compareName">{c.model.toUpperCase()}</div>
                <div className="vb-compareMeta">{c.count} runs</div>
                <div className="vb-compareStats">
                  <div>
                    <div className="vb-compareLbl">Avg ms</div>
                    <div className="vb-compareVal">{c.avgMs ? Math.round(c.avgMs) : '—'}</div>
                  </div>
                  <div>
                    <div className="vb-compareLbl">Avg FPS</div>
                    <div className="vb-compareVal">{c.avgFps ? c.avgFps.toFixed(1) : '—'}</div>
                  </div>
                </div>
                <div className="vb-miniBars">
                  <div className="vb-miniBar">
                    <div className="vb-miniBarLbl"><Gauge size={14} /> Latency</div>
                    <div className="vb-miniBarTrack">
                      <div
                        className="vb-miniBarFill"
                        style={{ width: `${Math.round(((Number(c.avgMs ?? 0) || 0) / summary.maxMs) * 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="vb-miniBar">
                    <div className="vb-miniBarLbl"><Video size={14} /> FPS</div>
                    <div className="vb-miniBarTrack">
                      <div
                        className="vb-miniBarFill vb-miniBarFill--green"
                        style={{ width: `${Math.round(((Number(c.avgFps ?? 0) || 0) / summary.maxFps) * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="vb-insightRow">
            <div className="vb-insight">
              <Trophy size={16} />
              <div>
                <div className="vb-insightLbl">Fastest latency</div>
                <div className="vb-insightVal">{summary.bestLatency?.model ? summary.bestLatency.model.toUpperCase() : '—'}</div>
              </div>
            </div>
            <div className="vb-insight">
              <Video size={16} />
              <div>
                <div className="vb-insightLbl">Best throughput</div>
                <div className="vb-insightVal">{summary.bestFps?.model ? summary.bestFps.model.toUpperCase() : '—'}</div>
              </div>
            </div>
            <div className="vb-insight">
              <BarChart3 size={16} />
              <div>
                <div className="vb-insightLbl">Detections (recent)</div>
                <div className="vb-insightVal">{summary.totalDetections || '—'}</div>
              </div>
            </div>
          </div>
        </Card>

        <Card className="vb-block">
          <div className="vb-blockHead">
            <div>
              <div className="vb-blockTitle">Jobs</div>
              <div className="vb-muted">Background processing queue (video).</div>
            </div>
          </div>
          <JobsList />
        </Card>
      </div>

      <Card className="vb-block">
        <div className="vb-blockHead">
          <div>
            <div className="vb-blockTitle">Recent runs</div>
            <div className="vb-muted">Artifacts are downloadable per run.</div>
          </div>
        </div>
        {recent?.runs?.length ? (
          <div className="vb-table">
            <div className="vb-thead">
              <div>Run</div>
              <div>Model</div>
              <div>Latency</div>
              <div>FPS</div>
              <div>Artifact</div>
            </div>
            {recent.runs.map((r: any) => (
              <div className="vb-trow" key={r.id}>
                <div className="vb-mono">#{r.id}</div>
                <div className="vb-chip">{String(r.model_name).toUpperCase()}</div>
                <div>{r.processing_ms} ms</div>
                <div>{r.fps ? Number(r.fps).toFixed(1) : '—'}</div>
                <div>
                  <Button
                    variant="soft"
                    onClick={async () => {
                      const token = getToken()
                      const res = await fetch(downloadRunUrl(r.id), { headers: token ? { Authorization: `Bearer ${token}` } : {} })
                      if (!res.ok) return
                      const blob = await res.blob()
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement('a')
                      a.href = url
                      a.download = `run-${r.id}-artifact`
                      a.click()
                      URL.revokeObjectURL(url)
                    }}
                  >
                    <span className="vb-inlineIcon"><Download size={16} /></span>
                    Download
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="vb-muted" style={{ marginTop: 10 }}>No runs yet.</div>
        )}
      </Card>
    </div>
  )
}

