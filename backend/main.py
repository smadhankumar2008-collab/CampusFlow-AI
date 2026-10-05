from __future__ import annotations

import math
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "campusflow.db"

app = FastAPI(title="CampusFlow AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def status_for_risk(score: float) -> str:
    if score >= 71:
        return "CRITICAL"
    if score >= 51:
        return "WARNING"
    if score >= 31:
        return "CAUTION"
    return "SAFE"


def risk_score(occupancy: float, growth: float, queue: float = 0) -> float:
    score = occupancy * 0.62 + min(max(growth * 2.5, 0), 30) + min(queue * 0.4, 20)
    return round(min(max(score, 0), 100), 1)


def init_db() -> None:
    conn = connect()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            venue TEXT NOT NULL,
            event_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            expected_participants INTEGER NOT NULL,
            expected_teams INTEGER NOT NULL,
            registration_counters INTEGER NOT NULL,
            parking_zones INTEGER NOT NULL,
            parking_capacity INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id TEXT UNIQUE NOT NULL,
            team_name TEXT NOT NULL,
            institution TEXT NOT NULL,
            department TEXT NOT NULL,
            leader TEXT NOT NULL,
            phone TEXT NOT NULL,
            members INTEGER NOT NULL,
            category TEXT NOT NULL,
            registration_time TEXT NOT NULL,
            arrival_time TEXT,
            checkin_time TEXT,
            counter TEXT,
            status TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS crowd_zones (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            capacity INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS crowd_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            zone_id TEXT NOT NULL,
            people_count INTEGER NOT NULL,
            capacity INTEGER NOT NULL,
            occupancy REAL NOT NULL,
            entry_rate REAL NOT NULL,
            exit_rate REAL NOT NULL,
            growth_rate REAL NOT NULL,
            risk_score REAL NOT NULL,
            FOREIGN KEY(zone_id) REFERENCES crowd_zones(id)
        );
        CREATE TABLE IF NOT EXISTS parking_zones (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            capacity INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS parking_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            parking_zone TEXT NOT NULL,
            vehicle_count INTEGER NOT NULL,
            capacity INTEGER NOT NULL,
            occupancy REAL NOT NULL,
            entry_rate REAL NOT NULL,
            exit_rate REAL NOT NULL,
            growth_rate REAL NOT NULL,
            predicted_full_time INTEGER,
            risk_level TEXT NOT NULL,
            FOREIGN KEY(parking_zone) REFERENCES parking_zones(id)
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            severity TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            location TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT NOT NULL,
            prediction TEXT,
            recommendation TEXT,
            acknowledged INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            severity TEXT NOT NULL,
            location TEXT NOT NULL,
            problem TEXT NOT NULL,
            evidence TEXT NOT NULL,
            prediction TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN'
        );
        CREATE TABLE IF NOT EXISTS event_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            report_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    existing = conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"]
    if existing == 0:
        seed_db(conn)
    conn.commit()
    conn.close()


def seed_db(conn: sqlite3.Connection) -> None:
    current = datetime.now(timezone.utc)
    conn.execute(
        """INSERT INTO events
        (event_id,name,event_type,venue,event_date,start_time,end_time,expected_participants,expected_teams,registration_counters,parking_zones,parking_capacity,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "CF-KCE-2026",
            "KCE Tech Fest 2026",
            "Technical Symposium",
            "Kumaraguru College of Engineering",
            "2026-10-18",
            "09:00",
            "17:30",
            1500,
            50,
            3,
            4,
            450,
            current.isoformat(),
        ),
    )
    zones = [
        ("main-stage", "Main Stage", 520),
        ("registration", "Registration", 160),
        ("food-court", "Food Court", 260),
        ("activities", "Activities", 330),
        ("entry", "Entry Gate", 180),
        ("exit", "Exit Gate", 140),
    ]
    conn.executemany("INSERT INTO crowd_zones(id,name,capacity) VALUES (?,?,?)", zones)
    parkings = [
        ("parking-a", "Parking A", 180),
        ("parking-b", "Parking B", 120),
        ("two-wheeler", "Two-Wheeler Parking", 300),
        ("vip", "VIP Parking", 45),
    ]
    conn.executemany("INSERT INTO parking_zones(id,name,capacity) VALUES (?,?,?)", parkings)

    institutions = ["KCE", "PSG Tech", "Amrita Vishwa Vidyapeetham", "Sri Krishna College", "CIT Coimbatore", "Rathinam College"]
    departments = ["CSE", "ECE", "AI & DS", "IT", "EEE", "Mechanical"]
    categories = ["Hackathon", "Robo Race", "Paper Presentation", "UI Sprint", "Tech Quiz", "Code Relay"]
    names = [
        "Circuit Breakers", "Binary Brains", "Pixel Pioneers", "Code Catalysts", "The Debuggers",
        "Neural Navigators", "Logic Loop", "Byte Brigade", "Syntax Squad", "The Innovators",
    ]
    for idx in range(1, 51):
        reg_at = current - timedelta(minutes=120 - idx * 2)
        status = "CHECKED-IN" if idx <= 34 else "ARRIVED" if idx <= 41 else "REGISTERED"
        arrival_at = reg_at + timedelta(minutes=18 + (idx % 7)) if status != "REGISTERED" else None
        checkin_at = arrival_at + timedelta(minutes=4 + (idx % 3)) if status == "CHECKED-IN" else None
        conn.execute(
            """INSERT INTO teams(team_id,team_name,institution,department,leader,phone,members,category,registration_time,arrival_time,checkin_time,counter,status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                f"CF26-{idx:03d}",
                f"{names[(idx - 1) % len(names)]} {idx:02d}",
                institutions[(idx - 1) % len(institutions)],
                departments[(idx - 1) % len(departments)],
                f"Team Lead {idx:02d}",
                f"+91 9{idx:09d}",
                3 + ((idx * 3) % 5),
                categories[(idx - 1) % len(categories)],
                reg_at.isoformat(),
                arrival_at.isoformat() if arrival_at else None,
                checkin_at.isoformat() if checkin_at else None,
                f"Counter {(idx - 1) % 3 + 1}" if status != "REGISTERED" else None,
                status,
            ),
        )

    # Seed 30 observations for each event zone with a believable arrival curve.
    for step in range(30):
        stamp = current - timedelta(minutes=(30 - step) * 5)
        phase = step / 29
        for zone_index, (zone_id, _name, capacity) in enumerate(zones):
            base = [260, 70, 125, 160, 88, 48][zone_index]
            wave = math.sin(step / 4 + zone_index) * 13
            surge = phase * [180, 58, 90, 120, 70, 30][zone_index]
            count = int(max(8, min(capacity * 0.98, base + wave + surge)))
            entry = round(max(1.5, 9 + phase * 11 + (zone_index % 3) * 1.8), 1)
            exit_rate = round(max(0.8, 5.5 - phase * 1.3 + (zone_index % 2)), 1)
            growth = round(entry - exit_rate, 1)
            score = risk_score(count / capacity * 100, growth)
            conn.execute(
                """INSERT INTO crowd_readings(timestamp,zone_id,people_count,capacity,occupancy,entry_rate,exit_rate,growth_rate,risk_score)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (stamp.isoformat(), zone_id, count, capacity, round(count / capacity * 100, 1), entry, exit_rate, growth, score),
            )

    for step in range(30):
        stamp = current - timedelta(minutes=(30 - step) * 5)
        phase = step / 29
        for zone_index, (zone_id, _name, capacity) in enumerate(parkings):
            base = [92, 42, 198, 18][zone_index]
            wave = math.sin(step / 3 + zone_index) * 5
            surge = phase * [75, 32, 84, 9][zone_index]
            count = int(max(4, min(capacity * 0.98, base + wave + surge)))
            entry = round(max(1.5, 4.5 + phase * [7, 4, 8, 1.2][zone_index]), 1)
            exit_rate = round(max(0.4, 2.2 - phase * 0.55), 1)
            growth = round(entry - exit_rate, 1)
            occupancy = count / capacity * 100
            full_in = int((capacity - count) / growth) if growth > 0 else None
            conn.execute(
                """INSERT INTO parking_readings(timestamp,parking_zone,vehicle_count,capacity,occupancy,entry_rate,exit_rate,growth_rate,predicted_full_time,risk_level)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (stamp.isoformat(), zone_id, count, capacity, round(occupancy, 1), entry, exit_rate, growth, full_in, status_for_risk(occupancy)),
            )

    # Add a calibrated current snapshot so the opening command center mirrors the intended hackathon demo state.
    current_zone_snapshot = [
        ("main-stage", 438, 84.2, 18.3, 5.2, 13.1, 67.0),
        ("registration", 132, 82.5, 14.2, 4.5, 9.7, 62.0),
        ("food-court", 174, 66.9, 8.4, 4.8, 3.6, 44.0),
        ("activities", 188, 57.0, 7.8, 4.9, 2.9, 37.0),
        ("entry", 78, 43.3, 10.8, 8.2, 2.6, 28.0),
        ("exit", 44, 31.4, 3.7, 6.4, -2.7, 18.0),
    ]
    for zone_id, people_count, occupancy, entry_rate, exit_rate, growth_rate, score in current_zone_snapshot:
        zone = conn.execute("SELECT capacity FROM crowd_zones WHERE id=?", (zone_id,)).fetchone()
        conn.execute("INSERT INTO crowd_readings(timestamp,zone_id,people_count,capacity,occupancy,entry_rate,exit_rate,growth_rate,risk_score) VALUES (?,?,?,?,?,?,?,?,?)", (current.isoformat(), zone_id, people_count, zone["capacity"], occupancy, entry_rate, exit_rate, growth_rate, score))
    current_parking_snapshot = [
        ("parking-a", 169, 93.9, 12.0, 2.7, 9.3, 8),
        ("parking-b", 54, 45.0, 4.4, 2.7, 1.7, 39),
        ("two-wheeler", 278, 92.6, 10.2, 3.3, 6.9, 3),
        ("vip", 25, 55.6, 1.8, 0.9, 0.9, 22),
    ]
    for parking_zone, vehicle_count, occupancy, entry_rate, exit_rate, growth_rate, predicted_full_time in current_parking_snapshot:
        zone = conn.execute("SELECT capacity FROM parking_zones WHERE id=?", (parking_zone,)).fetchone()
        conn.execute("INSERT INTO parking_readings(timestamp,parking_zone,vehicle_count,capacity,occupancy,entry_rate,exit_rate,growth_rate,predicted_full_time,risk_level) VALUES (?,?,?,?,?,?,?,?,?,?)", (current.isoformat(), parking_zone, vehicle_count, zone["capacity"], occupancy, entry_rate, exit_rate, growth_rate, predicted_full_time, status_for_risk(occupancy)))

    alert_rows = [
        (current - timedelta(minutes=2), "CRITICAL", "Parking Alert", "Parking A", "Parking A is nearing capacity", "98% occupancy with arrivals outpacing exits.", "Full in approximately 4 minutes.", "Redirect incoming vehicles to Parking B."),
        (current - timedelta(minutes=7), "WARNING", "Registration Alert", "Counter 1", "Registration queue is growing", "18 teams are waiting; utilization is at 91%.", "Congestion predicted in 3 minutes.", "Open Counter 3 and redirect incoming teams."),
        (current - timedelta(minutes=12), "CAUTION", "Crowd Alert", "Main Stage", "Main Stage density is rising", "Occupancy crossed 78% with +13 people/min growth.", "Peak crowd expected in 18 minutes.", "Use the north route for stage entry."),
        (current - timedelta(minutes=19), "CAUTION", "Bottleneck Alert", "Food Court", "Food Court queue is building", "Queue length increased for 5 consecutive readings.", "Service queue may exceed safe wait time.", "Open the secondary service queue."),
    ]
    for row in alert_rows:
        conn.execute("INSERT INTO alerts(created_at,severity,alert_type,location,title,detail,prediction,recommendation) VALUES (?,?,?,?,?,?,?,?)", tuple(v.isoformat() if isinstance(v, datetime) else v for v in row))
    recommendation_rows = [
        ("WARNING", "Counter 1", "Registration counter 1 queue is growing rapidly.", "18 teams waiting · 91% utilization · +4 teams/min", "Counter 1 may become congested in approximately 3 minutes.", "Open Counter 3 and redirect incoming teams."),
        ("CRITICAL", "Parking A", "Parking A is approaching capacity.", "94% occupied · +12 vehicles/min · 11 spaces remaining", "Parking A may reach full capacity in approximately 8 minutes.", "Redirect incoming vehicles to Parking B."),
        ("CAUTION", "Main Stage", "Main Stage crowd is increasing rapidly.", "82% occupied · +13 people/min · entry flow is concentrated", "Stage zone may become critical during the next arrival wave.", "Redirect participants through the north route."),
    ]
    for severity, location, problem, evidence, prediction, action in recommendation_rows:
        conn.execute("INSERT INTO recommendations(created_at,severity,location,problem,evidence,prediction,action) VALUES (?,?,?,?,?,?,?)", (current.isoformat(), severity, location, problem, evidence, prediction, action))
    conn.execute("INSERT INTO app_state(key,value) VALUES ('simulation_tick','0')")
    conn.execute("INSERT INTO app_state(key,value) VALUES ('simulation_running','0')")


def latest_readings(conn: sqlite3.Connection, table: str, key: str) -> list[sqlite3.Row]:
    return conn.execute(
        f"""SELECT r.* FROM {table} r
        INNER JOIN (SELECT {key}, MAX(id) AS max_id FROM {table} GROUP BY {key}) m
        ON r.id = m.max_id"""
    ).fetchall()


class EventIn(BaseModel):
    name: str
    event_type: str = "Technical Symposium"
    venue: str
    event_date: str
    start_time: str
    end_time: str
    expected_participants: int = Field(ge=1)
    expected_teams: int = Field(ge=1)
    registration_counters: int = Field(ge=1)
    parking_zones: int = Field(ge=1)
    parking_capacity: int = Field(ge=1)


class TeamIn(BaseModel):
    team_name: str
    institution: str
    department: str
    leader: str
    phone: str
    members: int = Field(ge=1, le=50)
    category: str


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "service": "CampusFlow AI API", "mode": "SIMULATION MODE"}


@app.get("/api/events")
def get_events() -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.post("/api/events")
def create_event(payload: EventIn) -> dict[str, Any]:
    conn = connect()
    event_id = f"CF-{datetime.now().strftime('%y%m%d')}-{random.randint(100, 999)}"
    conn.execute(
        """INSERT INTO events(event_id,name,event_type,venue,event_date,start_time,end_time,expected_participants,expected_teams,registration_counters,parking_zones,parking_capacity,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (event_id, payload.name, payload.event_type, payload.venue, payload.event_date, payload.start_time, payload.end_time, payload.expected_participants, payload.expected_teams, payload.registration_counters, payload.parking_zones, payload.parking_capacity, now_iso()),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/teams")
def get_teams() -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute("SELECT * FROM teams ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.post("/api/teams")
def create_team(payload: TeamIn) -> dict[str, Any]:
    conn = connect()
    next_num = conn.execute("SELECT COUNT(*) + 1 AS n FROM teams").fetchone()["n"]
    team_id = f"CF26-{next_num:03d}"
    stamp = now_iso()
    conn.execute(
        """INSERT INTO teams(team_id,team_name,institution,department,leader,phone,members,category,registration_time,status)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (team_id, payload.team_name, payload.institution, payload.department, payload.leader, payload.phone, payload.members, payload.category, stamp, "REGISTERED"),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,)).fetchone()
    conn.close()
    return dict(row)


@app.post("/api/teams/{team_id}/checkin")
def checkin_team(team_id: str) -> dict[str, Any]:
    conn = connect()
    row = conn.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Team not found")
    stamp = now_iso()
    status = row["status"]
    if status == "REGISTERED":
        conn.execute("UPDATE teams SET arrival_time=?, status='ARRIVED', counter='Counter 2' WHERE team_id=?", (stamp, team_id))
    elif status == "ARRIVED":
        conn.execute("UPDATE teams SET checkin_time=?, status='CHECKED-IN' WHERE team_id=?", (stamp, team_id))
    else:
        conn.execute("UPDATE teams SET status='COMPLETED' WHERE team_id=?", (team_id,))
    conn.commit()
    updated = conn.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,)).fetchone()
    conn.close()
    return dict(updated)


@app.get("/api/zones")
def get_zones() -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute(
        """SELECT z.*, r.people_count, r.occupancy, r.entry_rate, r.exit_rate, r.growth_rate, r.risk_score
        FROM crowd_zones z LEFT JOIN crowd_readings r ON r.id = (SELECT MAX(id) FROM crowd_readings WHERE zone_id=z.id)
        ORDER BY z.id"""
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        item["status"] = status_for_risk(item.get("risk_score") or item.get("occupancy") or 0)
        result.append(item)
    return result


@app.get("/api/parking")
def get_parking() -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute(
        """SELECT z.*, r.vehicle_count, r.occupancy, r.entry_rate, r.exit_rate, r.growth_rate, r.predicted_full_time, r.risk_level
        FROM parking_zones z LEFT JOIN parking_readings r ON r.id = (SELECT MAX(id) FROM parking_readings WHERE parking_zone=z.id)
        ORDER BY z.id"""
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/api/alerts")
def get_alerts() -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.patch("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int) -> dict[str, Any]:
    conn = connect()
    conn.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,))
    conn.commit()
    row = conn.execute("SELECT * FROM alerts WHERE id=?", (alert_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")
    return dict(row)


@app.get("/api/recommendations")
def get_recommendations() -> list[dict[str, Any]]:
    conn = connect()
    rows = conn.execute("SELECT * FROM recommendations ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.patch("/api/recommendations/{recommendation_id}")
def update_recommendation(recommendation_id: int, status: str = "IN PROGRESS") -> dict[str, Any]:
    conn = connect()
    conn.execute("UPDATE recommendations SET status=? WHERE id=?", (status, recommendation_id))
    conn.commit()
    row = conn.execute("SELECT * FROM recommendations WHERE id=?", (recommendation_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return dict(row)


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    conn = connect()
    team_counts = conn.execute("SELECT status, COUNT(*) AS count, COALESCE(SUM(members),0) AS members FROM teams GROUP BY status").fetchall()
    counts = {row["status"]: {"count": row["count"], "members": row["members"]} for row in team_counts}
    zones = latest_readings(conn, "crowd_readings", "zone_id")
    parks = latest_readings(conn, "parking_readings", "parking_zone")
    alerts = conn.execute("SELECT COUNT(*) AS count FROM alerts WHERE acknowledged=0").fetchone()["count"]
    recommendations = conn.execute("SELECT COUNT(*) AS count FROM recommendations WHERE status='OPEN'").fetchone()["count"]
    state_row = conn.execute("SELECT value FROM app_state WHERE key='simulation_tick'").fetchone()
    tick = int(state_row["value"] if state_row else 0)
    if tick == 0:
        # Calibrated opening state for the KCE Tech Fest demo sequence.
        participants, queue, parking_occupancy, overall = 1284, 18, 91.0, 68
    else:
        recovery = tick >= 15
        participants = min(2000, 1284 + tick * (18 if not recovery else 4))
        queue = max(5, 18 + (2 * tick if not recovery else 24 - (tick - 15) * 3))
        parking_occupancy = max(70, min(98, 91 + (0.7 * tick if not recovery else 10 - (tick - 15) * 2.2)))
        overall = round(max(42, min(94, 68 + (2.2 * tick if not recovery else 27 - (tick - 15) * 4.5))), 0)
    conn.close()
    return {
        "event": {
            "event_id": "CF-KCE-2026",
            "name": "KCE Tech Fest 2026",
            "venue": "Kumaraguru College of Engineering",
            "date": "18 Oct 2026",
            "status": "LIVE",
        },
        "teams": counts,
        "participants": participants,
        "queue": queue,
        "parking_occupancy": parking_occupancy,
        "overall_risk": overall,
        "risk_label": status_for_risk(overall),
        "active_alerts": alerts,
        "open_recommendations": recommendations,
    }


@app.get("/api/analytics")
def analytics() -> dict[str, Any]:
    conn = connect()
    crowd = conn.execute(
        """SELECT substr(timestamp,12,5) AS time, ROUND(AVG(occupancy),1) AS actual, ROUND(AVG(occupancy) + (ROW_NUMBER() OVER (ORDER BY timestamp)-1)*0.7,1) AS predicted
        FROM crowd_readings GROUP BY timestamp ORDER BY timestamp"""
    ).fetchall()
    parking = conn.execute("SELECT substr(timestamp,12,5) AS time, ROUND(AVG(occupancy),1) AS actual FROM parking_readings GROUP BY timestamp ORDER BY timestamp").fetchall()
    registration = conn.execute("SELECT substr(registration_time,12,5) AS time, COUNT(*) AS teams FROM teams GROUP BY substr(registration_time,12,5) ORDER BY time").fetchall()
    conn.close()
    return {
        "crowd": [dict(row) for row in crowd[-18:]],
        "parking": [dict(row) for row in parking[-18:]],
        "registration": [dict(row) for row in registration[-18:]],
        "metrics": {
            "total_participants": 1284,
            "total_teams": 50,
            "teams_arrived": 41,
            "teams_checked_in": 34,
            "peak_crowd": 1188,
            "peak_parking": 94,
            "avg_registration": 3.8,
            "avg_wait": 4.6,
            "total_alerts": 18,
            "critical_alerts": 3,
        },
    }


def simulate_step(conn: sqlite3.Connection, tick: int) -> dict[str, Any]:
    stamp = datetime.now(timezone.utc)
    phase = min(tick / 12, 1)
    zones = conn.execute("SELECT * FROM crowd_zones").fetchall()
    parks = conn.execute("SELECT * FROM parking_zones").fetchall()
    for index, zone in enumerate(zones):
        latest = conn.execute("SELECT * FROM crowd_readings WHERE zone_id=? ORDER BY id DESC LIMIT 1", (zone["id"],)).fetchone()
        previous = latest["people_count"] if latest else int(zone["capacity"] * 0.45)
        if tick >= 15:
            change = -int(4 + index * 0.4)
        else:
            change = int(7 + phase * 11 + (index % 3))
        count = int(min(zone["capacity"] * 0.99, max(4, previous + change)))
        entry = round(max(2, 12 + phase * 7 - (2 if tick >= 15 else 0)), 1)
        exit_rate = round(max(1.5, 6 - (tick >= 15) * 3), 1)
        growth = round(entry - exit_rate, 1)
        score = risk_score(count / zone["capacity"] * 100, growth)
        conn.execute("INSERT INTO crowd_readings(timestamp,zone_id,people_count,capacity,occupancy,entry_rate,exit_rate,growth_rate,risk_score) VALUES (?,?,?,?,?,?,?,?,?)", (stamp.isoformat(), zone["id"], count, zone["capacity"], round(count / zone["capacity"] * 100, 1), entry, exit_rate, growth, score))
    for index, parking in enumerate(parks):
        latest = conn.execute("SELECT * FROM parking_readings WHERE parking_zone=? ORDER BY id DESC LIMIT 1", (parking["id"],)).fetchone()
        previous = latest["vehicle_count"] if latest else int(parking["capacity"] * 0.5)
        if tick >= 15:
            change = -int(3 + index % 2)
        else:
            change = int(4 + phase * 5 + index)
        count = int(min(parking["capacity"] * 0.995, max(2, previous + change)))
        entry = round(max(1, 8 + phase * 4 - (2 if tick >= 15 else 0)), 1)
        exit_rate = round(max(1, 2.6 + (3 if tick >= 15 else 0)), 1)
        growth = round(entry - exit_rate, 1)
        occupancy = round(count / parking["capacity"] * 100, 1)
        full_in = int((parking["capacity"] - count) / growth) if growth > 0 else None
        conn.execute("INSERT INTO parking_readings(timestamp,parking_zone,vehicle_count,capacity,occupancy,entry_rate,exit_rate,growth_rate,predicted_full_time,risk_level) VALUES (?,?,?,?,?,?,?,?,?,?)", (stamp.isoformat(), parking["id"], count, parking["capacity"], occupancy, entry, exit_rate, growth, full_in, status_for_risk(occupancy)))
    if tick in (4, 8, 12):
        severity = "CAUTION" if tick == 4 else "WARNING" if tick == 8 else "CRITICAL"
        conn.execute("INSERT INTO alerts(created_at,severity,alert_type,location,title,detail,prediction,recommendation) VALUES (?,?,?,?,?,?,?,?)", (stamp.isoformat(), severity, "Prediction Alert", "Event Command Center", "Simulation pressure is increasing", f"Simulation tick {tick}: arrivals are outpacing exits across active zones.", "Congestion probability is rising in the next arrival wave.", "Follow the recommended diversion plan."))
    if tick == 12:
        conn.execute("INSERT INTO recommendations(created_at,severity,location,problem,evidence,prediction,action) VALUES (?,?,?,?,?,?,?)", (stamp.isoformat(), "CRITICAL", "Event Command Center", "Multiple demand signals are converging.", "Parking, queues and Main Stage all crossed warning thresholds.", "Risk may become critical within the next two readings.", "Open Counter 3, redirect vehicles to Parking B, and activate the north route."))
    conn.execute("UPDATE app_state SET value=? WHERE key='simulation_tick'", (str(tick),))
    conn.commit()
    return {"tick": tick, "timestamp": stamp.isoformat(), "mode": "SIMULATION MODE", "phase": "recovery" if tick >= 15 else "arrival wave"}


@app.post("/api/simulation/start")
def simulation_start() -> dict[str, Any]:
    conn = connect()
    conn.execute("UPDATE app_state SET value='1' WHERE key='simulation_running'")
    conn.execute("UPDATE app_state SET value='0' WHERE key='simulation_tick'")
    conn.commit()
    conn.close()
    return {"running": True, "tick": 0, "mode": "SIMULATION MODE"}


@app.post("/api/simulation/stop")
def simulation_stop() -> dict[str, Any]:
    conn = connect()
    conn.execute("UPDATE app_state SET value='0' WHERE key='simulation_running'")
    conn.commit()
    conn.close()
    return {"running": False}


@app.post("/api/simulation/tick")
def simulation_tick() -> dict[str, Any]:
    conn = connect()
    raw = conn.execute("SELECT value FROM app_state WHERE key='simulation_tick'").fetchone()
    tick = int(raw["value"] if raw else 0) + 1
    result = simulate_step(conn, tick)
    conn.close()
    return result


@app.post("/api/reports")
def create_report() -> dict[str, Any]:
    conn = connect()
    report = {
        "report_id": f"RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "event": "KCE Tech Fest 2026",
        "generated_at": now_iso(),
        "summary": "CampusFlow AI connected registration, crowd movement, and parking demand to surface interventions before critical congestion.",
        "metrics": {
            "teams": 50,
            "participants": 1284,
            "checked_in": 34,
            "peak_crowd": 1188,
            "peak_parking": "94%",
            "alerts": 18,
            "critical_alerts": 3,
        },
        "recommendations": [
            "Open Counter 3 and redirect incoming teams.",
            "Redirect vehicles to Parking B.",
            "Use the north route for Main Stage entry.",
        ],
    }
    import json
    conn.execute("INSERT INTO event_reports(event_id,generated_at,report_json) VALUES (?,?,?)", ("CF-KCE-2026", report["generated_at"], json.dumps(report)))
    conn.commit()
    conn.close()
    return report


init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
