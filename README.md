# CampusFlow AI

A polished hackathon-ready event operations command center for KCE Tech Fest 2026.

> **Predict the Crowd. Optimize the Campus. Run Safer Events.**

CampusFlow AI connects digital team registration, QR check-in, crowd monitoring, parking intelligence, prediction, alerts, and recommendations in one responsive workspace.

## Run locally

```bash
npm install
python -m pip install -r backend/requirements.txt

# terminal 1
python backend/main.py

# terminal 2
npm run dev
```

Open `http://localhost:5173`.

The Vite dev server proxies `/api` to the FastAPI service at port `8000`. SQLite is created as `campusflow.db` on first run.

## Demo flow

1. Click **Launch command center** on the landing page.
2. Choose a demo role and enter the command center.
3. Open **Overview** to see the calibrated KCE Tech Fest demo state.
4. Start **Simulation Mode** from the sidebar or overview.
5. Watch queues, crowd zones, parking pressure, risk, alerts, and recommendations update every four seconds.
6. Visit **Team Registration** to create a team and generate a QR pass.
7. Visit **QR Check-in** to move a team through `REGISTERED → ARRIVED → CHECKED-IN`.
8. Visit **Parking**, **Live Monitoring**, **Event Map**, **AI Recommendations**, **Analytics**, and **Reports** to tell the full demo story.

## Architecture

- **Frontend:** React + TypeScript + Vite, Recharts, Lucide React, responsive CSS design system.
- **Backend:** FastAPI with SQLite seed data and simulation endpoints.
- **Vision-ready path:** `Camera / video → OpenCV → YOLO detect → Track + map → Risk engine` is represented in Live Monitoring. The prototype uses clearly labeled simulation data when hardware is not connected.
- **Transparency:** simulated, uploaded-video, and live-camera states are explicitly labeled in the UI; risk scores are presented as prototype decision-support signals.

## API highlights

- `GET /api/dashboard`
- `GET /api/teams`, `POST /api/teams`
- `POST /api/teams/{team_id}/checkin`
- `GET /api/zones`, `GET /api/parking`
- `GET /api/alerts`, `PATCH /api/alerts/{id}/acknowledge`
- `GET /api/recommendations`
- `GET /api/analytics`
- `POST /api/simulation/start`, `/api/simulation/tick`, `/api/simulation/stop`
- `POST /api/reports`

The default demo is deliberately populated with 50 teams, time-series crowd readings, six event zones, four parking zones, alerts, recommendations, and report-ready metrics.
