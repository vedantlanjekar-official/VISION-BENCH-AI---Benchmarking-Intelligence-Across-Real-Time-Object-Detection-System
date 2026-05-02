import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './index.css'
import { Landing } from './pages/Landing'
import { ConsoleLayout, AdminRoute } from './pages/Console'
import { initTheme } from './lib/theme'
import { Dashboard } from './components/Dashboard'
import { WebcamDetect } from './components/WebcamDetect'
import { ImageDetect } from './components/ImageDetect'
import { VideoDetect } from './components/VideoDetect'
import { ComparePage } from './pages/console-routes'

initTheme()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/console" element={<ConsoleLayout />}>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="webcam" element={<WebcamDetect />} />
          <Route path="image" element={<ImageDetect />} />
          <Route path="video" element={<VideoDetect />} />
          <Route path="compare" element={<ComparePage />} />
          <Route path="admin" element={<AdminRoute />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
