import { useState } from 'react'
import { login, register } from '../lib/api'
import { clearToken, setRefreshToken, setToken } from '../lib/auth'

export function AuthPanel(props: { onAuthed: () => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit() {
    setLoading(true)
    setError(null)
    try {
      const res = mode === 'login' ? await login(email, password) : await register(email, password)
      setToken(res.access_token)
      if (res.refresh_token) setRefreshToken(res.refresh_token)
      props.onAuthed()
    } catch (e: any) {
      setError(e?.message ?? String(e))
      clearToken()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <div>
          <div className="title">Account</div>
          <div className="muted">JWT auth is required for detections.</div>
        </div>
        <div className="row">
          <button className={mode === 'login' ? 'activeTab' : ''} onClick={() => setMode('login')}>
            Login
          </button>
          <button className={mode === 'register' ? 'activeTab' : ''} onClick={() => setMode('register')}>
            Register
          </button>
        </div>
      </div>

      <div className="row" style={{ marginTop: 12 }}>
        <div style={{ flex: 1, minWidth: 240 }}>
          <div className="label">Email</div>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
        </div>
        <div style={{ flex: 1, minWidth: 240 }}>
          <div className="label">Password</div>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min 8 chars" />
        </div>
        <button disabled={loading || !email || password.length < 8} onClick={onSubmit}>
          {loading ? 'Working…' : mode === 'login' ? 'Login' : 'Register'}
        </button>
      </div>

      {error ? <div className="error">{error}</div> : null}
    </div>
  )
}

