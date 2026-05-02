import { Link } from 'react-router-dom'
import { Badge, Button, Card, Container, Section } from '../ui/components'
import heroA from '../assets/ai-hero-1.png'
import heroB from '../assets/ai-hero-4.png'
import heroC from '../assets/ai-hero-5.png'
import heroD from '../assets/ai-hero-2.png'
import heroE from '../assets/ai-hero-3.png'

import problemsA from '../assets/ai-hero-4.png'
import problemsB from '../assets/ai-hero-1.png'
import problemsC from '../assets/ai-hero-5.png'
import howA from '../assets/ai-hero-3.png'
import howB from '../assets/ai-hero-2.png'
import howC from '../assets/ai-hero-4.png'

type Item = { title: string; desc: string; img: string }

const problems: Item[] = [
  {
    title: 'Lack of Real-Time Detection Systems',
    desc: 'Many traditional systems cannot process visual data in real time, leading to delayed decision-making.',
    img: problemsA,
  },
  {
    title: 'Difficulty in Model Selection',
    desc: 'Developers struggle to choose between models like YOLO, SSD, and Faster R-CNN due to lack of comparative platforms.',
    img: problemsB,
  },
  {
    title: 'Fragmented AI Solutions',
    desc: 'Existing solutions often lack full-stack integration (frontend + backend + ML), making them impractical for deployment.',
    img: problemsC,
  },
  {
    title: 'Manual Monitoring Limitations',
    desc: 'Human-based visual monitoring is inefficient, error-prone, and not scalable.',
    img: problemsA,
  },
  {
    title: 'Inconsistent Performance Evaluation',
    desc: 'No standardized system to evaluate models using metrics like mAP, IoU, FPS in a unified environment.',
    img: problemsB,
  },
  {
    title: 'High Complexity of Implementation',
    desc: 'Building and integrating AI systems requires expertise across multiple domains, creating a high entry barrier.',
    img: problemsC,
  },
]

const howItWorks: Item[] = [
  { title: 'User Input Acquisition', desc: 'Users upload images, videos, or enable live webcam streaming through the frontend interface.', img: howA },
  { title: 'Data Transmission to Backend', desc: 'The frontend sends input data to the backend via REST APIs.', img: howB },
  { title: 'Preprocessing Pipeline', desc: 'Input data is resized, normalized, and prepared for model inference.', img: howC },
  { title: 'Model Selection & Inference', desc: 'Selected model (YOLO / SSD / Faster R-CNN) processes the data.', img: howA },
  { title: 'Detection Output Generation', desc: 'System generates bounding boxes, object labels, and confidence scores.', img: howB },
  { title: 'Visualization & Analytics', desc: 'Results are displayed on the frontend with performance metrics and stored for analysis.', img: howC },
]

const usps: Item[] = [
  { title: 'Multi-Model Comparison Platform', desc: 'Enables real-time comparison of multiple object detection models in one system.', img: problemsB },
  { title: 'Real-Time Processing Capability', desc: 'Supports live webcam detection with low latency.', img: problemsC },
  { title: 'Full-Stack Integrated Architecture', desc: 'Combines AI, backend APIs, frontend UI, and database into a unified system.', img: problemsA },
  { title: 'Advanced Performance Analytics', desc: 'Provides detailed metrics like mAP, IoU, FPS with visual dashboards.', img: problemsB },
  { title: 'Scalable & Modular Design', desc: 'Easily extendable to new models, datasets, and use cases.', img: problemsC },
  { title: 'User-Friendly Interactive Interface', desc: 'Simplifies complex AI operations into an intuitive and accessible platform.', img: problemsA },
]

function GridCards(props: { items: Item[] }) {
  return (
    <div className="vb-grid3">
      {props.items.map((it) => (
        <Card key={it.title} className="vb-card--media">
          <div className="vb-media16x9">
            <img src={it.img} alt="" />
          </div>
          <div className="vb-cardBody">
            <div className="vb-cardTitle">{it.title}</div>
            <div className="vb-cardDesc">{it.desc}</div>
          </div>
        </Card>
      ))}
    </div>
  )
}

export function Landing() {
  return (
    <div className="vb-root">
      <header className="vb-topbar">
        <Container className="vb-topbarInner">
          <div className="vb-brand">
            <div className="vb-brandMark">VB</div>
            <div>
              <div className="vb-brandName">VISION BENCH AI</div>
              <div className="vb-brandTag">Benchmarking intelligence across real time object detection</div>
            </div>
          </div>
          <nav className="vb-nav">
            <a href="#problems" className="vb-navLink">Problems</a>
            <a href="#how" className="vb-navLink">How it works</a>
            <a href="#usps" className="vb-navLink">USPs</a>
            <a href="#contact" className="vb-navLink">Contact</a>
            <Link to="/console">
              <Button>Launch Console</Button>
            </Link>
          </nav>
        </Container>
      </header>

      <main>
        <Section className="vb-hero">
          <Container className="vb-heroGrid">
            <div>
              <Badge>VISION BENCH AI</Badge>
              <h1 className="vb-h1">VISION BENCH AI</h1>
              <div className="vb-subtitle">BENCHMARKING INTELLIGENCE ACROSS REAL TIME OBJECT DETECTION SYSTEM</div>
              <p className="vb-lead">
                The platform is a full-stack, AI-powered system that performs real-time object detection on images, videos, and live streams. It integrates multiple deep learning models to analyze and compare performance metrics, providing visual outputs, analytics dashboards, and scalable APIs for efficient deployment and intelligent decision-making across diverse real-world applications.
              </p>
              <div className="vb-cta">
                <Link to="/console"><Button>Get Started</Button></Link>
                <a href="#problems"><Button variant="soft">Explore</Button></a>
              </div>
              <div className="vb-metrics">
                <Card className="vb-mini">
                  <div className="vb-miniNum">3</div>
                  <div className="vb-miniLbl">Models</div>
                </Card>
                <Card className="vb-mini">
                  <div className="vb-miniNum">Real-time</div>
                  <div className="vb-miniLbl">Webcam + Streams</div>
                </Card>
                <Card className="vb-mini">
                  <div className="vb-miniNum">mAP • IoU</div>
                  <div className="vb-miniLbl">Unified metrics</div>
                </Card>
              </div>
            </div>

            <div className="vb-heroArt">
              <div className="vb-heroArtGlow" />
              <div className="vb-heroMosaic" aria-hidden="true">
                <img className="vb-heroImg vb-heroImg--a" src={heroA} alt="" />
                <img className="vb-heroImg vb-heroImg--b" src={heroB} alt="" />
                <img className="vb-heroImg vb-heroImg--c" src={heroC} alt="" />
                <img className="vb-heroImg vb-heroImg--d" src={heroD} alt="" />
                <img className="vb-heroImg vb-heroImg--e" src={heroE} alt="" />
              </div>
              <div className="vb-float vb-float--1">
                <div className="vb-floatTitle">Live Bench</div>
                <div className="vb-floatDesc">YOLO vs SSD vs Faster R-CNN</div>
              </div>
              <div className="vb-float vb-float--2">
                <div className="vb-floatTitle">Latency</div>
                <div className="vb-floatDesc">Optimized inference path</div>
              </div>
            </div>
          </Container>
        </Section>

        <Section id="problems">
          <Container>
            <h2 className="vb-h2">Problems we solve</h2>
            <p className="vb-muted">
              Production teams need speed, comparability, and a deployable full-stack system—not fragmented demos.
            </p>
            <GridCards items={problems} />
          </Container>
        </Section>

        <Section id="how">
          <Container>
            <h2 className="vb-h2">How our system works</h2>
            <p className="vb-muted">From acquisition to visualization, every step is designed for reliability and low latency.</p>
            <GridCards items={howItWorks} />
          </Container>
        </Section>

        <Section id="usps">
          <Container>
            <h2 className="vb-h2">USPs of our system</h2>
            <p className="vb-muted">A premium platform for benchmarking and deploying real-time detection.</p>
            <GridCards items={usps} />
          </Container>
        </Section>

        <Section id="contact" className="vb-contact">
          <Container className="vb-contactGrid">
            <div>
              <h2 className="vb-h2">Contact</h2>
              <p className="vb-muted">
                Want an enterprise deployment, custom dataset evaluation, or dedicated GPU benchmarking?
              </p>
              <div className="vb-contactCard">
                <div className="vb-contactRow"><b>Email</b><span>contact@visionbench.ai</span></div>
                <div className="vb-contactRow"><b>Phone</b><span>+91 00000 00000</span></div>
                <div className="vb-contactRow"><b>Location</b><span>Remote • Worldwide</span></div>
              </div>
            </div>
            <Card className="vb-contactForm">
              <div className="vb-cardTitle">Send a message</div>
              <div className="vb-form">
                <input className="vb-input" placeholder="Name" />
                <input className="vb-input" placeholder="Email" />
                <textarea className="vb-textarea" placeholder="Tell us what you’re building…" />
                <Button>Submit</Button>
                <div className="vb-formHint">Demo form (wire to your CRM/email later).</div>
              </div>
            </Card>
          </Container>
        </Section>
      </main>

      <footer className="vb-footer">
        <Container className="vb-footerInner">
          <div>© {new Date().getFullYear()} VISION BENCH AI</div>
          <div className="vb-muted">Premium benchmarking for real-time object detection.</div>
        </Container>
      </footer>
    </div>
  )
}

