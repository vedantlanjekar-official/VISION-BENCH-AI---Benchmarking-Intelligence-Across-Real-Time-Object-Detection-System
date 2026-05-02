import { useEffect, useState } from 'react'
import { detectVideo, downloadRunUrl, fetchJob, type ModelName } from '../lib/api'
import { Button, Card } from '../ui/components'
import { Download, Film, Loader2, Play } from 'lucide-react'

export function VideoDetect() {
  const [model, setModel] = useState<ModelName>('yolo')
  const [scoreThresh, setScoreThresh] = useState(0.25)
  const [maxFrames, setMaxFrames] = useState(120)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [jobId, setJobId] = useState<number | null>(null)
  const [job, setJob] = useState<any>(null)

  async function onRun() {
    if (!file) return
    setLoading(true)
    setError(null)
    setJobId(null)
    setJob(null)
    try {
      const res = await detectVideo({ file, model, scoreThresh, maxFrames })
      setJobId(res.job_id)
    } catch (e: any) {
      setError(e?.message ?? String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!jobId) return
    let cancelled = false
    const t = window.setInterval(async () => {
      try {
        const j = await fetchJob(jobId)
        if (!cancelled) setJob(j)
        if (j.status === 'succeeded' || j.status === 'failed') window.clearInterval(t)
      } catch {
        // ignore
      }
    }, 1000)
    return () => {
      cancelled = true
      window.clearInterval(t)
    }
  }, [jobId])

  return (
    <div className="vb-stack">
      <Card className="vb-block">
        <div className="vb-blockHead">
          <div>
            <div className="vb-blockTitle">Video Processing Queue</div>
            <div className="vb-muted">Submit a video job. The worker produces an annotated MP4 artifact.</div>
          </div>
          <div className="vb-inline">
            {jobId ? <span className="vb-pill"><Film size={16} /> Job #{jobId}</span> : null}
            {job?.status ? (
              <span className="vb-pill">
                {job.status === 'running' ? <Loader2 size={16} className="vb-spin" /> : <Play size={16} />}
                {job.status}
              </span>
            ) : null}
          </div>
        </div>

        <div className="vb-formRow">
          <div className="vb-field">
            <div className="vb-label">Model</div>
            <select value={model} onChange={(e) => setModel(e.target.value as ModelName)}>
              <option value="yolo">YOLOv8</option>
              <option value="ssd">SSD300</option>
              <option value="fasterrcnn">Faster R-CNN</option>
            </select>
          </div>
          <div className="vb-field">
            <div className="vb-label">Score threshold</div>
            <input type="number" step="0.05" min="0" max="1" value={scoreThresh} onChange={(e) => setScoreThresh(Number(e.target.value))} />
          </div>
          <div className="vb-field">
            <div className="vb-label">Max frames</div>
            <input type="number" min="1" max="5000" value={maxFrames} onChange={(e) => setMaxFrames(Number(e.target.value))} />
          </div>
        </div>

        <div className="vb-uploadRow">
          <input className="vb-file" type="file" accept="video/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <Button disabled={!file || loading} onClick={onRun}>
            {loading ? 'Submitting…' : 'Submit job'}
          </Button>
        </div>

        {error ? <div className="error">{error}</div> : null}

        {jobId ? (
          <div className="vb-jobCard">
            <div className="vb-jobMeta">
              <div><b>Status</b> {job?.status ?? 'queued'}</div>
              <div><b>Asset</b> {job?.asset_id ?? '—'}</div>
              <div><b>Run</b> {job?.run_id ?? '—'}</div>
            </div>

            {job?.run_id ? (
              <div>
                <Button
                  variant="soft"
                  onClick={async () => {
                    const res = await fetch(downloadRunUrl(job.run_id))
                    if (!res.ok) return
                    const blob = await res.blob()
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = `job-${jobId}-annotated.mp4`
                    a.click()
                    URL.revokeObjectURL(url)
                  }}
                >
                  <span className="vb-inlineIcon"><Download size={16} /></span>
                  Download annotated video
                </Button>
              </div>
            ) : (
              <div className="vb-muted">When the job completes, the artifact will be downloadable here.</div>
            )}
          </div>
        ) : (
          <div className="vb-muted">Upload a video to enqueue a background job.</div>
        )}
      </Card>
    </div>
  )
}

