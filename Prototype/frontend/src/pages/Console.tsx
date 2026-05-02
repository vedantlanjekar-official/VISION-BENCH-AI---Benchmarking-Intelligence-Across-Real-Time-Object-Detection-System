import { useEffect, useMemo, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Camera, Image as ImageIcon, Video, BarChart3, Shield, Moon, Sun } from 'lucide-react'
import { AdminPanel } from '../components/AdminPanel'
import { getTheme, setTheme, type Theme } from '../lib/theme'
import { Button, Container } from '../ui/components'
import { cx } from '../ui/cx'

export function ConsoleLayout() {
  const [me, setMe] = useState<{ id: number; email: string; role: string } | null>(null)
  const [theme, setThemeState] = useState<Theme>(getTheme())
  const nav = useNavigate()
  const loc = useLocation()

  useEffect(() => {
    // Auth removed: console is accessible without login.
    setMe({ id: 0, email: 'Guest', role: 'user' })
  }, [])

  useEffect(() => {
    if (loc.pathname === '/console') nav('/console/webcam', { replace: true })
  }, [loc.pathname, nav])

  const items = useMemo(
    () => [
      { to: '/console/dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
      { to: '/console/webcam', label: 'Webcam', icon: <Camera size={18} /> },
      { to: '/console/image', label: 'Image', icon: <ImageIcon size={18} /> },
      { to: '/console/video', label: 'Video', icon: <Video size={18} /> },
      { to: '/console/compare', label: 'Compare', icon: <BarChart3 size={18} /> },
    ],
    []
  )

  return (
    <div className="vb-consoleRoot">
      <aside className="vb-sidebar">
        <div className="vb-sideHeader">
          <Link to="/" className="vb-sideBrand">
            <div className="vb-brandMark">VB</div>
            <div>
              <div className="vb-sideName">VISION BENCH AI</div>
              <div className="vb-sideTag">Detection Console</div>
            </div>
          </Link>
        </div>

        <nav className="vb-sideNav">
          {items.map((it) => (
            <NavLink
              key={it.to}
              to={it.to}
              className={({ isActive }) => cx('vb-navItem', isActive && 'vb-navItem--active')}
            >
              <span className="vb-navIcon">{it.icon}</span>
              <span>{it.label}</span>
            </NavLink>
          ))}
          {me?.role === 'admin' ? (
            <NavLink to="/console/admin" className={({ isActive }) => cx('vb-navItem', isActive && 'vb-navItem--active')}>
              <span className="vb-navIcon">
                <Shield size={18} />
              </span>
              <span>Admin</span>
            </NavLink>
          ) : null}
        </nav>

        <div className="vb-sideFooter">
          {me ? <div className="vb-userPill">{me.email} • {me.role}</div> : <div className="vb-muted">Guest</div>}
          <div className="vb-sideActions">
            <button
              className="vb-iconBtn"
              onClick={() => {
                const next: Theme = theme === 'dark' ? 'light' : 'dark'
                setTheme(next)
                setThemeState(next)
              }}
              title="Toggle theme"
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </div>
      </aside>

      <div className="vb-consoleMain">
        <header className="vb-consoleTop">
          <Container className="vb-consoleTopInner">
            <div>
              <div className="vb-consoleTitle">Premium Real-Time Object Detection</div>
              <div className="vb-muted">YOLOv8 • SSD300 • Faster R-CNN • Streaming • Benchmarks</div>
            </div>
            <div className="vb-consoleCtas">
              <Link to="/"><Button variant="soft">Back to Home</Button></Link>
            </div>
          </Container>
        </header>

        <main className="vb-consoleContent">
          <Container>
            <Outlet />
          </Container>
        </main>
      </div>
    </div>
  )
}

export function AdminRoute() {
  return (
    <div className="vb-stack">
      <AdminPanel />
    </div>
  )
}

