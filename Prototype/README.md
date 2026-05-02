# Real-time Object Detection Platform (YOLO / SSD / Faster R-CNN)

End-to-end production-ready reference implementation:

- **Backend**: FastAPI + WebSocket streaming + PyTorch inference
- **Models**: YOLOv8 (Ultralytics), SSD300 (torchvision), Faster R-CNN (torchvision)
- **DB**: PostgreSQL (SQLModel)
- **Frontend**: React (Vite + TS) with image/video upload + live webcam detection
- **Deployment**: Docker + Docker Compose

## Project structure

- `frontend/` React app
- `backend/` FastAPI server
- `models/` (optional) local model assets/cache (ignored)
- `database/` DB notes/migrations (optional)
- `utils/` shared scripts (optional)
- `docker/` container assets

## Quickstart (Docker Compose)

1. Install Docker Desktop.
2. From repo root:

```bash
docker compose up --build
```

3. Open:
- Frontend: `http://localhost:5173`
- Backend API docs (Swagger): `http://localhost:8000/docs`

## Auth (JWT)

This build enables JWT auth by default.

- Register: `POST /auth/register` (JSON `{email,password}`)
- Login: `POST /auth/login` (form fields `username`, `password`)
- Refresh: `POST /auth/refresh` (JSON `{refresh_token}`) (rotates refresh token)
- Logout: `POST /auth/logout` (JSON `{refresh_token}`) (revokes refresh token)

Admin bootstrap: **the first user to register becomes `admin` automatically** (only when the DB has no users yet).

Frontend stores the token in localStorage (`ann_token`) and sends `Authorization: Bearer <token>` to protected endpoints.

## RBAC (roles) + Admin endpoints

- **Roles**: `user` (default) and `admin`
- **Admin-only**:
  - `GET /admin/users`
  - `PATCH /admin/users/{id}/role` with JSON `{ "role": "user" | "admin" }`
  - `GET /admin/audit?page=1&page_size=50` (audit log)
  - `GET /admin/audit/export?limit=10000` (download JSONL)
  - `GET /jobs?mine=false` (list all users’ jobs)
- **Owner or Admin**:
  - `GET /jobs/{job_id}`
  - `GET /runs/{run_id}/download`

Tip: make yourself admin by calling `PATCH /admin/users/{id}/role` from an existing admin account.

## Local dev (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
setx DATABASE_URL "postgresql+psycopg://postgres:postgres@localhost:5432/ann"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Notes

- First run downloads model weights (YOLO via Ultralytics, SSD/FasterRCNN via torchvision).
- For GPU acceleration, use CUDA-enabled PyTorch and the provided Dockerfile as a base to customize.

## API overview

- `POST /detect/image?model=yolo|ssd|fasterrcnn&score_thresh=0.25` (multipart form field `file`)
- `POST /detect/video?model=...&score_thresh=...&max_frames=120` (multipart `file`)
- `GET /jobs/{job_id}` (poll async status)
- `GET /jobs?mine=true&page=1&page_size=20&status=queued` (paginated list)
- `GET /runs/{run_id}/download` (download annotated image/video)
- `WS /detect/webcam`
  - **Client → Server** JSON: `{ "model": "yolo", "score_thresh": 0.25, "frame_b64": "data:image/jpeg;base64,..." }`
  - **Server → Client** JSON: `{ "processing_ms": 12, "detections": [...], "annotated_jpeg_b64": "data:image/jpeg;base64,..." }`
- `GET /models`
- `GET /models/compare`
- `GET /metrics` and `GET /metrics/recent`
- `GET /auth/me` (returns `{id,email,role}`)

## Audit logging (auth + admin actions)

The system records audit events for:
- `auth.register`
- `auth.login` and `auth.login_failed`
- `auth.refresh` and `auth.refresh_failed`
- `auth.logout`
- `user.role_change`
- `auth.rate_limited` (rate limit exceeded)

Audit rows include best-effort:
- `ip`
- `user_agent`
- `fingerprint` (SHA-256 of `ip|user_agent`)

Retention model: **append-only**. There are no API endpoints that delete or mutate audit rows. Use `GET /admin/audit/export` to ship audit logs to an external immutable store if required.

## Rate limiting

- `POST /auth/login`:
  - **10/min/IP**
  - **10/min/email**
  - **5/min/(IP+email)**
- `POST /auth/refresh`:
  - **30/min/IP**
  - **10/min/refresh_token_hash**
  - **30/min/user_id** (after token is resolved)

When exceeded, the API returns **429** and sets `Retry-After` header.

## Proxy-aware client IP (X-Forwarded-For)

By default the backend uses the direct peer IP. If you're behind a reverse proxy/load balancer, enable:
- `TRUST_PROXY_HEADERS=true`
- `TRUSTED_PROXY_CIDRS=<your proxy subnets>`

Only requests coming from a trusted proxy IP will have `X-Forwarded-For` honored (uses the left-most/original address).

## Offline evaluation (mAP / IoU / Precision / Recall / F1)

Use `models/eval_coco.py` against a labeled COCO-format dataset:

```bash
python models/eval_coco.py --model yolo --images_dir path/to/val2017 --ann_json path/to/instances_val2017.json --limit 500
```

## Storage (Local vs S3)

By default artifacts/uploads are stored on the local filesystem under the `backend_data` Docker volume.

To enable S3 (or S3-compatible like MinIO), set backend env:
- `STORAGE_BACKEND=s3`
- `S3_BUCKET=...`
- `S3_REGION=...` (optional)
- `S3_ACCESS_KEY_ID=...`
- `S3_SECRET_ACCESS_KEY=...`
- `S3_ENDPOINT_URL=...` (optional, needed for MinIO)


