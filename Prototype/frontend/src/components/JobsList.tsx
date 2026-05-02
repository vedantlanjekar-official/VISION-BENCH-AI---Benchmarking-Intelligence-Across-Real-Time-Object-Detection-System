import { useEffect, useState } from 'react'
import { apiUrl } from '../lib/api'
import { Button } from '../ui/components'
import { CheckCircle2, Clock3, Loader2, XCircle } from 'lucide-react'

export function JobsList() {
  const [page, setPage] = useState(1)
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setError(null)
    try {
      const headers: Record<string, string> = {}
      const t = localStorage.getItem('ann_token')
      if (t) headers.Authorization = `Bearer ${t}`
      const res = await fetch(`${apiUrl('')}/jobs?mine=true&page=${page}&page_size=20`, {
        headers,
      })
      if (!res.ok) throw new Error(`Failed /jobs: ${res.status}`)
      setData(await res.json())
    } catch (e: any) {
      setError(e?.message ?? String(e))
    }
  }

  useEffect(() => {
    load()
  }, [page])

  return (
    <div>
      {error ? <div className="error">{error}</div> : null}
      {data?.jobs?.length ? (
        <>
          <div className="vb-table vb-table--compact">
            <div className="vb-thead">
              <div>ID</div>
              <div>Status</div>
              <div>Model</div>
              <div>Run</div>
            </div>
            {data.jobs.map((j: any) => (
              <div className="vb-trow" key={j.id}>
                <div className="vb-mono">#{j.id}</div>
                <div className="vb-status">
                  {j.status === 'succeeded' ? <CheckCircle2 size={16} /> : null}
                  {j.status === 'failed' ? <XCircle size={16} /> : null}
                  {j.status === 'queued' ? <Clock3 size={16} /> : null}
                  {j.status === 'running' ? <Loader2 size={16} className="vb-spin" /> : null}
                  <span>{j.status}</span>
                </div>
                <div className="vb-chip">{String(j.model_name).toUpperCase()}</div>
                <div>{j.run_id ? <span className="vb-mono">#{j.run_id}</span> : '—'}</div>
              </div>
            ))}
          </div>

          <div className="row" style={{ marginTop: 10, justifyContent: 'space-between' }}>
            <Button variant="ghost" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
              Prev
            </Button>
            <Button variant="ghost" disabled={!data.has_next} onClick={() => setPage((p) => p + 1)}>
              Next
            </Button>
          </div>
        </>
      ) : (
        <div className="muted">{data ? 'No jobs yet.' : 'Loading…'}</div>
      )}
    </div>
  )
}

