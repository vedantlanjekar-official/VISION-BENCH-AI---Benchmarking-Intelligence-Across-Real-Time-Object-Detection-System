import { useEffect, useMemo, useRef, useState } from 'react'
import { apiUrl, type ModelName } from '../lib/api'
import { Button, Card } from '../ui/components'
import { Camera, Gauge, Play, Square } from 'lucide-react'

type WsResponse = {
  model: string
  device: string
  processing_ms: number
  detections: Array<{ label: string; score: number; box: { x1: number; y1: number; x2: number; y2: number } }>
  annotated_jpeg_b64: string
}

export function WebcamDetect() {
  const [model, setModel] = useState<ModelName>('yolo')
  const [scoreThresh, setScoreThresh] = useState(0.25)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [last, setLast] = useState<WsResponse | null>(null)

  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const loopRef = useRef<number | null>(null)

  const wsUrl = useMemo(() => {
    const http = apiUrl('')
    const u = new URL(http)
    u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:'
    u.pathname = '/detect/webcam'
    return u.toString()
  }, [])

  async function start() {
    setError(null)
    setLast(null)
    setRunning(true)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      if (!videoRef.current) return
      videoRef.current.srcObject = stream
      await videoRef.current.play()

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data) as WsResponse
        setLast(msg)
      }
      ws.onerror = () => setError('WebSocket error')
      ws.onclose = () => {
        // no-op
      }

      const tick = async () => {
        if (!running) return
        const v = videoRef.current
        const c = canvasRef.current
        if (!v || !c) {
          loopRef.current = window.setTimeout(tick, 100)
          return
        }
        const w = v.videoWidth || 640
        const h = v.videoHeight || 480
        c.width = w
        c.height = h
        const ctx = c.getContext('2d')
        if (!ctx) return
        ctx.drawImage(v, 0, 0, w, h)
        const jpeg = c.toDataURL('image/jpeg', 0.75)

        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ model, score_thresh: scoreThresh, frame_b64: jpeg }))
        }
        loopRef.current = window.setTimeout(tick, 120)
      }

      loopRef.current = window.setTimeout(tick, 250)
    } catch (e: any) {
      setError(e?.message ?? String(e))
      setRunning(false)
    }
  }

  function stop() {
    setRunning(false)
    if (loopRef.current) window.clearTimeout(loopRef.current)
    loopRef.current = null

    const v = videoRef.current
    const stream = v?.srcObject as MediaStream | null
    if (stream) stream.getTracks().forEach((t) => t.stop())
    if (v) v.srcObject = null

    const ws = wsRef.current
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) ws.close()
    wsRef.current = null
  }

  useEffect(() => {
    return () => stop()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="vb-stack">
      <Card className="vb-block">
        <div className="vb-blockHead">
          <div>
            <div className="vb-blockTitle">Live Webcam Detection</div>
            <div className="vb-muted">Stream frames, benchmark latency, and visualize annotations in real time.</div>
          </div>
          <div className="vb-inline">
            <div className="vb-pill">
              <Gauge size={16} />
              <span>{last ? `${last.processing_ms} ms` : '— ms'}</span>
            </div>
            <div className="vb-pill">
              <Camera size={16} />
              <span>{last ? `${last.detections.length} objects` : '0 objects'}</span>
            </div>
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
            <input
              type="number"
              step="0.05"
              min="0"
              max="1"
              value={scoreThresh}
              onChange={(e) => setScoreThresh(Number(e.target.value))}
            />
          </div>
          <div className="vb-field vb-field--actions">
            <div className="vb-label">Controls</div>
            {!running ? (
              <Button onClick={start}>
                <span className="vb-inlineIcon"><Play size={16} /></span>
                Start
              </Button>
            ) : (
              <Button variant="soft" onClick={stop}>
                <span className="vb-inlineIcon"><Square size={16} /></span>
                Stop
              </Button>
            )}
          </div>
        </div>

        {error ? <div className="error">{error}</div> : null}

        <div className="vb-grid2">
          <div className="vb-mediaPanel">
            <div className="vb-panelTitle">Raw</div>
            <video ref={videoRef} className="media" playsInline muted />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
          </div>
          <div className="vb-mediaPanel">
            <div className="vb-panelTitle">Annotated</div>
            {last ? (
              <img className="media" src={last.annotated_jpeg_b64} alt="annotated" />
            ) : (
              <div className="vb-empty">Start the stream to see annotations.</div>
            )}
          </div>
        </div>

        {last?.detections?.length ? (
          <div className="vb-detectList">
            <div className="vb-panelTitle">Detections</div>
            <div className="vb-chips">
              {last.detections.slice(0, 12).map((d, i) => (
                <span key={i} className="vb-chip">{d.label} • {d.score.toFixed(2)}</span>
              ))}
            </div>
          </div>
        ) : null}
      </Card>
    </div>
  )
}

