import { useEffect, useState } from 'react'
import { detectImage, downloadRunUrl, type DetectResponse, type ModelName } from '../lib/api'
import { Button, Card } from '../ui/components'
import { Download, Image as ImgIcon, Sparkles } from 'lucide-react'

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

export function ImageDetect() {
  const [model, setModel] = useState<ModelName>('yolo')
  const [scoreThresh, setScoreThresh] = useState(0.25)
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [artifactUrl, setArtifactUrl] = useState<string | null>(null)
  const [result, setResult] = useState<DetectResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onRun() {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    if (artifactUrl) URL.revokeObjectURL(artifactUrl)
    setArtifactUrl(null)
    try {
      const res = await detectImage({ file, model, scoreThresh })
      setResult(res)
    } catch (e: any) {
      setError(e?.message ?? String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!result?.run_id) return
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetch(downloadRunUrl(result.run_id!))
        if (!res.ok) return
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        if (cancelled) {
          URL.revokeObjectURL(url)
          return
        }
        setArtifactUrl(url)
      } catch {
        // ignore preview failures
      }
    })()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result?.run_id])

  useEffect(() => {
    return () => {
      if (artifactUrl) URL.revokeObjectURL(artifactUrl)
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="vb-stack">
      <Card className="vb-block">
        <div className="vb-blockHead">
          <div>
            <div className="vb-blockTitle">Image Detection</div>
            <div className="vb-muted">Upload an image, run inference, and download an annotated artifact.</div>
          </div>
          {result?.run_id ? (
            <Button
              variant="soft"
              onClick={async () => {
                const res = await fetch(downloadRunUrl(result.run_id!))
                if (!res.ok) return
                const blob = await res.blob()
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `run-${result.run_id}-annotated.jpg`
                a.click()
                URL.revokeObjectURL(url)
              }}
            >
              <span className="vb-inlineIcon"><Download size={16} /></span>
              Download artifact
            </Button>
          ) : null}
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
            <input type="number" step="0.05" min="0" max="1" value={scoreThresh} onChange={(e) => setScoreThresh(clamp(Number(e.target.value), 0, 1))} />
          </div>
          <div className="vb-field vb-field--actions">
            <div className="vb-label">Run</div>
            <Button disabled={!file || loading} onClick={onRun}>
              <span className="vb-inlineIcon"><Sparkles size={16} /></span>
              {loading ? 'Detecting…' : 'Detect'}
            </Button>
          </div>
        </div>

        <div className="vb-uploadRow">
          <input
            className="vb-file"
            type="file"
            accept="image/*"
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null
              setFile(f)
              setPreviewUrl(f ? URL.createObjectURL(f) : null)
              setResult(null)
            }}
          />
        </div>

        {error ? <div className="error">{error}</div> : null}

        <div className="vb-grid2">
          <div className="vb-mediaPanel">
            <div className="vb-panelTitle"><ImgIcon size={16} /> Input</div>
            {previewUrl ? <img className="media" src={previewUrl} alt="preview" /> : <div className="vb-empty">Choose an image.</div>}
          </div>
          <div className="vb-mediaPanel">
            <div className="vb-panelTitle">Output</div>
            {result ? (
              <>
                <div className="vb-inline" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
                  <span className="vb-pill">{String(result.model).toUpperCase()}</span>
                  <span className="vb-pill">{result.processing_ms} ms • {result.detections.length} objects</span>
                </div>
                {artifactUrl ? (
                  <div className="vb-outputPreview">
                    <img className="media" src={artifactUrl} alt="annotated output" />
                  </div>
                ) : (
                  <div className="vb-empty" style={{ marginBottom: 10 }}>Generating preview…</div>
                )}
                <div className="vb-table vb-table--compact">
                  <div className="vb-thead">
                    <div>Label</div>
                    <div>Score</div>
                    <div>Box</div>
                  </div>
                  {result.detections.map((d, i) => (
                    <div className="vb-trow" key={i}>
                      <div className="vb-chip">{d.label}</div>
                      <div>{d.score.toFixed(2)}</div>
                      <div className="vb-mono">[{d.box.x1.toFixed(0)},{d.box.y1.toFixed(0)}]-[{d.box.x2.toFixed(0)},{d.box.y2.toFixed(0)}]</div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="vb-empty">Run detection to see results.</div>
            )}
          </div>
        </div>
      </Card>
    </div>
  )
}

