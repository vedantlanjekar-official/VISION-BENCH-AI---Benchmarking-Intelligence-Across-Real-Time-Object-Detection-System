import { useEffect, useState } from 'react'
import { apiUrl } from '../lib/api'

export function AdminPanel() {
  const [users, setUsers] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setError(null)
    const token = localStorage.getItem('ann_token')
    const res = await fetch(apiUrl('/admin/users'), { headers: token ? { Authorization: `Bearer ${token}` } : {} })
    if (!res.ok) {
      setError(`Failed /admin/users: ${res.status}`)
      return
    }
    const json = await res.json()
    setUsers(json.users ?? [])
  }

  async function setRole(userId: number, role: 'user' | 'admin') {
    const token = localStorage.getItem('ann_token')
    const res = await fetch(apiUrl(`/admin/users/${userId}/role`), {
      method: 'PATCH',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ role }),
    })
    if (!res.ok) {
      setError(`Failed role update: ${res.status}`)
      return
    }
    await load()
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="panel">
      <div className="panelTitle">Admin</div>
      {error ? <div className="error">{error}</div> : null}
      {users.length ? (
        <div className="table" style={{ marginTop: 10 }}>
          <div className="thead">
            <div>User</div>
            <div>Role</div>
            <div>Action</div>
          </div>
          {users.map((u) => (
            <div className="trow" key={u.id}>
              <div className="mono">
                #{u.id} • {u.email}
              </div>
              <div>{u.role}</div>
              <div className="row">
                <button onClick={() => setRole(u.id, 'user')}>Make user</button>
                <button onClick={() => setRole(u.id, 'admin')}>Make admin</button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="muted">Loading…</div>
      )}
    </div>
  )
}

