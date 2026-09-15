from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import os
import html

try:
    import joblib
    import pandas as pd
except ImportError:
    joblib = None
    pd = None

app = Flask(__name__)
app.secret_key = "ev_health_secret_key"

# Original backend database
DB_NAME = os.path.join(
    os.path.dirname(__file__),
    "ev-health-monitoring-system",
    "predictive_maintenance_process.db",
)


# =========================================================
# DATABASE SETUP / SAFE MIGRATIONS
# =========================================================


def initialize_database():
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        temperature FLOAT,
        humidity FLOAT,
        power_consumption FLOAT,
        prediction VARCHAR
    )"""
    )
    cols = {row[1] for row in conn.execute("PRAGMA table_info(predictions)")}
    if "charging_station_id" not in cols:
        conn.execute("ALTER TABLE predictions ADD COLUMN charging_station_id INTEGER")

    conn.execute(
        """CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name VARCHAR,
        comments VARCHAR,
        rating INTEGER
    )"""
    )
    conn.commit()
    conn.close()


initialize_database()


# =========================================================
# DATABASE CONNECTION
# =========================================================


def get_db():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# BATTERY HEALTH CALCULATION
# =========================================================


def calculate_health(temperature, power):

    temperature = temperature or 0
    power = power or 0

    health = 100

    if temperature > 25:
        health -= (temperature - 25) * 2

    if temperature < 15:
        health -= (15 - temperature) * 1.5

    if power > 30:
        health -= (power - 30) * 1.2

    health = max(20, min(100, int(health)))

    return health


# =========================================================
# COMMON CSS
# =========================================================

STYLE = """
<style>
* { box-sizing: border-box; }
:root {
    --bg: #07110D;
    --bg-soft: #0A1511;
    --card: #0D1B15;
    --card-2: #10231A;
    --border: #1A3328;
    --green: #22C55E;
    --green-bright: #34D399;
    --green-soft: rgba(34,197,94,.12);
    --pink: #E879F9;
    --pink-bright: #F0ABFC;
    --pink-soft: rgba(232,121,249,.12);
    --text: #F0FDF4;
    --muted: #94A3A0;
    --warning: #F59E0B;
    --danger: #F43F5E;
}
html { scroll-behavior: smooth; }
body { margin: 0; font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; }

/* LOGIN */
.login-body {
    min-height: 100vh; background: radial-gradient(circle at 20% 20%, rgba(34,197,94,.12), transparent 32%), radial-gradient(circle at 80% 70%, rgba(232,121,249,.10), transparent 30%), var(--bg); color: var(--text); display:flex; flex-direction:column;
}
.login-navbar { width:100%; padding:20px 8%; display:flex; align-items:center; background:rgba(13,27,21,.82); backdrop-filter:blur(14px); border-bottom:1px solid var(--border); }
.login-brand { font-size:22px; font-weight:800; color:var(--green-bright); letter-spacing:.2px; }
.login-brand span { color:var(--text); }
.login-container { min-height:calc(100vh - 73px); display:flex; justify-content:center; align-items:center; padding:30px; }
.login-card { width:100%; max-width:430px; background:rgba(13,27,21,.92); border:1px solid var(--border); border-radius:22px; padding:40px; box-shadow:0 24px 80px rgba(0,0,0,.38), 0 0 45px rgba(34,197,94,.06); }
.login-card h1 { margin:0 auto 24px; color:var(--text); font-size:30px; text-align:center; line-height:1.2; max-width:360px; }
.login-card p { color:var(--muted); margin:0 0 30px; line-height:1.6; }
.login-card label { display:block; margin-bottom:8px; color:#D9EEE0; font-weight:600; }
.login-card input { width:100%; padding:14px 15px; margin-bottom:20px; background:#091711; border:1px solid #244436; border-radius:10px; color:var(--text); font-size:15px; transition:.2s; }
.login-card input:focus { outline:none; border-color:var(--green); box-shadow:0 0 0 3px rgba(34,197,94,.12); }
.login-card input::placeholder { color:#6F8178; }
.login-btn { width:100%; border:none; border-radius:10px; padding:14px; cursor:pointer; font-size:15px; font-weight:800; background:linear-gradient(135deg,var(--green),var(--green-bright)); color:#04100A; transition:.2s; }
.login-btn:hover { transform:translateY(-1px); box-shadow:0 10px 28px rgba(34,197,94,.22); }
.login-link { text-align:center; margin-top:25px; color:var(--muted); line-height:1.7; }
.login-link a { color:var(--pink-bright); text-decoration:none; font-weight:700; }
.login-link a:hover { text-decoration:underline; }
.error { background:rgba(244,63,94,.10); border:1px solid rgba(244,63,94,.55); color:#FDA4AF; padding:12px; border-radius:10px; margin-bottom:20px; }

/* APP SHELL */
.dashboard-body { background:radial-gradient(circle at 75% 0%, rgba(232,121,249,.06), transparent 25%), radial-gradient(circle at 15% 30%, rgba(34,197,94,.05), transparent 30%), var(--bg); color:var(--text); min-height:100vh; }
.sidebar { position:fixed; left:0; top:0; bottom:0; width:250px; background:rgba(9,22,16,.94); backdrop-filter:blur(18px); padding:24px 14px; border-right:1px solid var(--border); overflow-y:auto; z-index:10; }
.sidebar-logo { font-size:20px; font-weight:900; margin-bottom:8px; color:var(--green-bright); letter-spacing:.5px; }
.sidebar-logo span { color:var(--text); }
.sidebar-user { color:var(--muted); font-size:13px; margin-bottom:22px; padding:0 12px 18px; border-bottom:1px solid rgba(26,51,40,.7); }
.nav-section { color:#5F746A; font-size:10px; font-weight:800; letter-spacing:1.2px; padding:14px 12px 7px; }
.nav-link { display:flex; align-items:center; gap:9px; padding:11px 13px; margin-bottom:4px; border-radius:10px; color:#BFD0C7; text-decoration:none; font-size:14px; transition:.18s; }
.nav-link:hover { background:#12261D; color:var(--text); transform:translateX(2px); }
.nav-link.active { background:linear-gradient(90deg,rgba(34,197,94,.16),rgba(34,197,94,.05)); color:#EFFFF4; border:1px solid rgba(34,197,94,.18); box-shadow:inset 3px 0 0 var(--green); }
.logout-link { margin-top:18px; background:rgba(244,63,94,.06); color:#FDA4AF; }
.main-content { margin-left:250px; padding:34px 42px 55px; max-width:1600px; }
.page-top { display:flex; justify-content:space-between; align-items:flex-start; gap:20px; margin-bottom:28px; }
.page-title { font-size:32px; margin:0 0 8px; letter-spacing:-.7px; }
.page-subtitle { color:var(--muted); font-size:14px; line-height:1.6; }
.live-pill { display:inline-flex; align-items:center; gap:8px; padding:9px 12px; border-radius:999px; background:rgba(34,197,94,.08); border:1px solid rgba(34,197,94,.18); color:#A7F3D0; font-size:12px; font-weight:700; white-space:nowrap; }
.live-dot { width:7px; height:7px; border-radius:50%; background:var(--green); box-shadow:0 0 12px var(--green); }

/* METRICS */
.metrics-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:15px; margin-bottom:22px; }
.metric-card { position:relative; background:linear-gradient(145deg,rgba(16,35,26,.94),rgba(13,27,21,.94)); padding:19px; border-radius:16px; border:1px solid var(--border); overflow:hidden; transition:.2s; }
.metric-card:hover { transform:translateY(-3px); border-color:#2B4F3D; box-shadow:0 14px 30px rgba(0,0,0,.18); }
.metric-card::after { content:""; position:absolute; width:70px; height:70px; right:-28px; top:-28px; border-radius:50%; background:var(--green-soft); }
.metric-title { color:#8EA198; font-size:11px; text-transform:uppercase; letter-spacing:.8px; font-weight:800; }
.metric-value { font-size:30px; font-weight:900; margin-top:10px; letter-spacing:-1px; }
.metric-icon { font-size:19px; margin-bottom:8px; }
.blue { color:#67E8F9; } .green { color:var(--green-bright); } .orange { color:#FDBA74; } .red { color:#FB7185; } .yellow { color:#FCD34D; }

/* PANELS */
.chart-grid { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(320px,.75fr); gap:18px; margin-bottom:18px; }
.panel { background:linear-gradient(145deg,rgba(14,30,23,.96),rgba(10,21,16,.96)); border-radius:18px; border:1px solid var(--border); padding:22px; overflow:hidden; box-shadow:0 10px 35px rgba(0,0,0,.10); }
.panel-title { margin:0; font-size:18px; letter-spacing:-.2px; }
.panel-subtitle { color:#82938B; font-size:12px; margin:6px 0 18px; }

/* CHART */
.graph { width:100%; height:280px; background:linear-gradient(180deg,rgba(34,197,94,.035),rgba(0,0,0,.05)); border-radius:13px; border:1px solid #173126; }

/* BATTERY HERO */
.battery-hero { display:flex; align-items:center; gap:22px; min-height:280px; }
.health-ring { width:168px; height:168px; border-radius:50%; display:grid; place-items:center; flex:0 0 auto; background:conic-gradient(var(--green) calc(var(--health) * 1%), #183328 0); box-shadow:0 0 35px rgba(34,197,94,.10); position:relative; }
.health-ring::before { content:""; width:132px; height:132px; border-radius:50%; background:#0B1711; position:absolute; }
.health-ring-content { position:relative; z-index:1; text-align:center; }
.health-ring-value { font-size:34px; font-weight:900; }
.health-ring-label { color:#8EA198; font-size:10px; letter-spacing:1px; font-weight:800; }
.health-details { flex:1; }
.health-status { display:inline-flex; align-items:center; gap:7px; margin-top:14px; padding:7px 11px; border-radius:999px; background:var(--green-soft); color:#86EFAC; font-size:11px; font-weight:800; }
.health-detail-row { display:flex; justify-content:space-between; gap:20px; padding:11px 0; border-bottom:1px solid rgba(26,51,40,.7); color:#91A39A; font-size:12px; }
.health-detail-row strong { color:#E4F3E9; font-size:13px; }
.battery-box { width:100%; height:10px; background:#0A1510; border-radius:999px; overflow:hidden; margin-top:20px; border:1px solid #173126; }
.battery-fill { height:100%; background:linear-gradient(90deg,var(--green),var(--green-bright)); border-radius:999px; box-shadow:0 0 16px rgba(34,197,94,.25); }
.health-text { margin-top:14px; color:#9FB0A7; text-align:center; }

/* AI */
.ai-panel { border-color:rgba(232,121,249,.18); background:radial-gradient(circle at 90% 10%,rgba(232,121,249,.10),transparent 28%),linear-gradient(145deg,#160F19,#0D1B15); }
.ai-panel .panel-title { color:#F5D0FE; }
.ai-badge { display:inline-flex; align-items:center; gap:6px; color:var(--pink-bright); background:var(--pink-soft); border:1px solid rgba(232,121,249,.20); padding:6px 9px; border-radius:999px; font-size:10px; font-weight:800; margin-bottom:15px; }
.ai-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:13px; }
.ai-card { padding:18px; border-radius:14px; background:rgba(255,255,255,.025); border:1px solid rgba(232,121,249,.12); }
.ai-card .metric-value { margin-top:6px; }

/* ALERT / SESSION */
.two-col { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18px; margin-bottom:18px; }
.data-table { width:100%; border-collapse:collapse; margin-top:8px; }
.data-table th { text-align:left; padding:12px; color:#8FA59A; border-bottom:1px solid #20392D; font-size:11px; text-transform:uppercase; letter-spacing:.6px; white-space:nowrap; }
.data-table td { padding:13px 12px; border-bottom:1px solid #172B22; color:#D0DDD5; font-size:12px; white-space:nowrap; }
.data-table tr:hover { background:rgba(34,197,94,.035); }
.action-link { display:inline-flex; margin-top:16px; padding:9px 12px; border-radius:9px; color:#B7F7CF; background:rgba(34,197,94,.07); border:1px solid rgba(34,197,94,.15); text-decoration:none; font-size:12px; font-weight:700; }
.action-link:hover { background:rgba(34,197,94,.13); }
.badge { padding:6px 10px; border-radius:999px; font-size:10px; font-weight:800; }
.badge-good { background:#123823; color:#86EFAC; } .badge-warning { background:#3E3011; color:#FCD34D; } .badge-danger { background:#401722; color:#FDA4AF; }
.empty-state { text-align:center; color:#82938B; padding:35px; }
.section-heading { display:flex; justify-content:space-between; align-items:center; gap:15px; margin-bottom:12px; }

/* GENERIC PAGES */
.generic-page .metrics-grid { grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); }
.generic-page .panel { margin-top:18px; }

/* TOP HEADER */
.topbar {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:20px;
    padding:16px 20px;
    margin-bottom:26px;
    background:rgba(13,27,21,.78);
    border:1px solid rgba(52,211,153,.13);
    border-radius:18px;
    backdrop-filter:blur(14px);
    box-shadow:0 10px 30px rgba(0,0,0,.16);
}
.topbar-title { font-size:14px; font-weight:800; letter-spacing:.05em; text-transform:uppercase; color:#eafff4; }
.topbar-subtitle { color:#81948c; font-size:12px; margin-top:4px; }
.system-status { display:flex; align-items:center; gap:8px; color:#9ee8bd; font-size:12px; font-weight:700; white-space:nowrap; }
.status-dot { width:8px; height:8px; border-radius:50%; background:#22c55e; box-shadow:0 0 12px rgba(34,197,94,.75); }
.user-pill { display:flex; align-items:center; gap:9px; padding:8px 12px; border-radius:999px; background:#111f19; border:1px solid #20392d; color:#d9f8e7; font-size:12px; }
.user-avatar { width:28px; height:28px; border-radius:50%; display:grid; place-items:center; background:linear-gradient(135deg,#22c55e,#e879f9); color:#07110d; font-weight:900; }
.ai-accent { color:#e879f9 !important; }
.ai-panel { border-color:rgba(232,121,249,.28) !important; box-shadow:0 0 28px rgba(232,121,249,.07); }
.battery-dashboard { display:flex; align-items:center; justify-content:center; min-height:220px; }
.battery-ring { --health:80; width:170px; height:170px; border-radius:50%; background:conic-gradient(#22c55e calc(var(--health) * 1%), #16271f 0); display:grid; place-items:center; position:relative; box-shadow:0 0 35px rgba(34,197,94,.13); }
.battery-ring::before { content:""; position:absolute; inset:12px; border-radius:50%; background:#0d1b15; border:1px solid #244235; }
.battery-ring-content { position:relative; text-align:center; z-index:1; }
.battery-ring-value { font-size:38px; font-weight:900; color:#eafff4; }
.battery-ring-label { margin-top:2px; font-size:10px; letter-spacing:.13em; color:#8fa79b; }
.metric-icon { width:38px; height:38px; display:grid; place-items:center; border-radius:12px; background:#12271c; margin-bottom:12px; font-size:18px; }
.metric-card:hover { transform:translateY(-3px); border-color:rgba(52,211,153,.3); box-shadow:0 14px 32px rgba(0,0,0,.18); }
.metric-card { transition:.2s ease; }


.page-top { display:flex; justify-content:space-between; align-items:flex-end; gap:20px; margin-bottom:25px; }
.outline-btn,.ai-btn { display:inline-flex; align-items:center; justify-content:center; text-decoration:none; border-radius:12px; padding:11px 15px; font-size:12px; font-weight:800; }
.outline-btn { color:#b7eacb; border:1px solid #28513d; background:#0d1b15; }
.outline-btn:hover { border-color:#34d399; background:#10271c; }
.ai-btn { margin-top:10px; color:#ffe8ff; border:1px solid rgba(232,121,249,.35); background:rgba(232,121,249,.10); }
.ai-btn:hover { background:rgba(232,121,249,.18); }
.section-kicker { color:#6f8b7d; font-size:10px; font-weight:900; letter-spacing:.15em; margin-bottom:8px; }
.battery-hero { display:grid; grid-template-columns: minmax(280px,.85fr) minmax(320px,1.15fr); gap:20px; margin-bottom:20px; }
.battery-hero-card { min-height:390px; }
.health-good { border-color:rgba(34,197,94,.28); }
.health-warning { border-color:rgba(245,158,11,.28); }
.health-danger { border-color:rgba(239,68,68,.28); }
.metric-list { margin-top:20px; }
.metric-row { display:flex; justify-content:space-between; align-items:center; padding:17px 0; border-bottom:1px solid #1b3227; color:#b7c9c0; }
.metric-row:last-child { border-bottom:0; }
.metric-row div { display:flex; align-items:center; gap:11px; }
.metric-row strong { color:#effff6; font-size:18px; }
.metric-row-icon { width:34px; height:34px; display:grid; place-items:center; border-radius:10px; background:#12271c; }
.trend-panel { margin-bottom:20px; }
.large-graph { height:340px; }
.panel-heading-row { display:flex; justify-content:space-between; align-items:flex-start; gap:20px; }
.trend-legend { color:#91aa9d; font-size:11px; display:flex; gap:7px; align-items:center; }
.trend-legend span { width:9px; height:9px; border-radius:50%; background:#34d399; box-shadow:0 0 9px rgba(52,211,153,.6); }
.insight-text { color:#a8bbb1; line-height:1.75; font-size:14px; }
.insight-text strong { color:#f0fff6; }
.thresholds { margin-top:15px; }
.thresholds > div { display:grid; grid-template-columns:14px 85px 1fr; align-items:center; gap:10px; padding:12px 0; border-bottom:1px solid #1b3227; color:#9db0a6; font-size:12px; }
.thresholds > div:last-child { border-bottom:0; }
.thresholds b { color:#eafff2; }
.threshold-dot { width:9px; height:9px; border-radius:50%; }
.threshold-dot.good { background:#22c55e; }
.threshold-dot.warning { background:#f59e0b; }
.threshold-dot.danger { background:#ef4444; }
.two-col { display:grid; grid-template-columns:1fr 1fr; gap:20px; }

/* =========================================================
   FINAL POLISH - BATTERY HEALTH + CLEAN HEADINGS
   ========================================================= */

/* Remove secondary copy below the main page headings. */
.analytics-heading p,
.modern-page-heading p { display:none !important; }

/* Battery Performance: clean light metric rows with varied accents. */
.battery-hero-card + .panel {
    background:linear-gradient(145deg,#FFFFFF,#F9FCFA) !important;
    border:1px solid #E2EEE8 !important;
    box-shadow:0 12px 32px rgba(23,53,43,.08) !important;
}
.battery-hero-card + .panel .panel-title {
    color:#17352B !important;
    font-size:22px !important;
    margin-top:2px !important;
}
.battery-hero-card + .panel .section-kicker {
    color:#168553 !important;
}
.metric-list {
    display:grid !important;
    gap:10px !important;
    margin-top:18px !important;
}
.metric-row {
    position:relative !important;
    display:flex !important;
    align-items:center !important;
    justify-content:space-between !important;
    min-height:64px !important;
    padding:13px 16px 13px 18px !important;
    border:1px solid #E4EEE9 !important;
    border-bottom:1px solid #E4EEE9 !important;
    border-radius:14px !important;
    background:#F8FBF9 !important;
    color:#61786E !important;
    overflow:hidden !important;
    transition:transform .18s ease, box-shadow .18s ease !important;
}
.metric-row:hover {
    transform:translateX(3px) !important;
    box-shadow:0 8px 20px rgba(23,53,43,.07) !important;
}
.metric-row::before {
    content:"" !important;
    position:absolute !important;
    left:0 !important;
    top:0 !important;
    bottom:0 !important;
    width:4px !important;
    background:#168553 !important;
}
.metric-row:nth-child(2)::before { background:#D83F83 !important; }
.metric-row:nth-child(3)::before { background:#E49A18 !important; }
.metric-row:nth-child(4)::before { background:#168553 !important; }
.metric-row div {
    display:flex !important;
    align-items:center !important;
    gap:12px !important;
    color:#587067 !important;
    font-size:14px !important;
    font-weight:700 !important;
}
.metric-row strong {
    color:#17352B !important;
    font-size:19px !important;
    font-weight:900 !important;
}
.metric-row:nth-child(2) strong { color:#D83F83 !important; }
.metric-row:nth-child(3) strong { color:#C67A18 !important; }
.metric-row-icon {
    width:11px !important;
    height:11px !important;
    flex:0 0 11px !important;
    border-radius:50% !important;
    background:#168553 !important;
    box-shadow:0 0 0 5px #E4F5EC !important;
}
.metric-row-icon.metric-power {
    background:#D83F83 !important;
    box-shadow:0 0 0 5px #FBEAF2 !important;
}
.metric-row-icon.metric-health {
    background:#E49A18 !important;
    box-shadow:0 0 0 5px #FFF4DF !important;
}
.metric-row-icon.metric-samples {
    background:#168553 !important;
    box-shadow:0 0 0 5px #E4F5EC !important;
}

/* Predictive Battery Insight - dark pink heading and stronger AI treatment. */
.ai-panel .panel-title {
    color:#C52F72 !important;
    font-weight:900 !important;
}
.ai-panel .section-kicker.ai-accent {
    color:#C52F72 !important;
}
.ai-panel .insight-text {
    color:#61786E !important;
}
.ai-panel .insight-text strong {
    color:#C52F72 !important;
}
.ai-btn {
    color:#C52F72 !important;
    background:#FFF1F7 !important;
    border:1px solid #EFC2D8 !important;
    box-shadow:none !important;
}
.ai-btn:hover {
    background:#FCE4EF !important;
}

/* Status Guide - use a deeper green for Healthy. */
.threshold-dot.good {
    background:#168553 !important;
    box-shadow:0 0 0 4px #E2F3EA !important;
}
.thresholds b { color:#17352B !important; }
.thresholds > div { color:#61786E !important; }

/* Keep analytics and prediction headings clean and centered. */
.analytics-heading,
.modern-page-heading {
    margin-bottom:22px !important;
}

/* RESPONSIVE */
@media(max-width:1150px) { .metrics-grid { grid-template-columns:repeat(3,1fr); } .chart-grid { grid-template-columns:1fr; } }
@media(max-width:850px) { .sidebar { width:72px; padding:20px 9px; } .sidebar-logo { text-align:center; font-size:0; }  .sidebar-logo span,.sidebar-user,.nav-section { display:none; } .nav-link { font-size:0; justify-content:center; padding:12px; }  .main-content { margin-left:72px; padding:25px 18px 40px; } .two-col { grid-template-columns:1fr; } .metrics-grid { grid-template-columns:repeat(2,1fr); } .battery-hero { flex-direction:column; text-align:center; } }
@media(max-width:520px) { .metrics-grid { grid-template-columns:1fr; } .page-top { flex-direction:column; } .page-title { font-size:30px !important; } .main-content { padding:22px 13px 35px; } }

/* CLEAN LIGHT INTERFACE OVERRIDES */
html, body { background:#F6FAF8; }
.dashboard-body { background:#F6FAF8 !important; color:#17352B !important; }
.sidebar { background:#FFFFFF !important; border-right:1px solid #D9E5DF !important; box-shadow:8px 0 28px rgba(23,53,43,.06); backdrop-filter:none !important; }
.sidebar-logo { color:#17352B !important; }
.sidebar-logo span { color:#17352B !important; }
.sidebar-user { display:none !important; }
.nav-section { color:#789087 !important; }
.nav-link { color:#4F6B61 !important; }
.nav-link:hover { background:#F0F7F3 !important; color:#17352B !important; }
.nav-link.active { background:#EFFAF4 !important; color:#17352B !important; border:1px solid #BFE6D1 !important; box-shadow:inset 3px 0 0 #16A36A !important; }
.logout-link { background:#FFF4F5 !important; color:#C43B55 !important; }
.main-content { background:#F6FAF8 !important; }
.page-top { position:relative; justify-content:center !important; }
.page-top > div:first-child { width:100%; text-align:center; }
.page-title { color:#17352B !important; text-align:center !important; }
.page-subtitle { color:#6C8278 !important; text-align:center !important; }
.topbar { background:#FFFFFF !important; border:1px solid #D9E5DF !important; box-shadow:0 8px 24px rgba(23,53,43,.06) !important; backdrop-filter:none !important; }
.topbar-title { color:#17352B !important; }
.topbar-subtitle { color:#71877D !important; }
.user-pill { background:#F3F8F5 !important; border:1px solid #D7E5DE !important; color:#355349 !important; }
.user-avatar { color:#FFFFFF !important; }
.system-status { color:#168553 !important; }
.live-pill { background:#EFFAF4 !important; border-color:#BFE6D1 !important; color:#168553 !important; }
.metric-card, .panel { border-color:#FFFFFF !important; }
.metric-card { box-shadow:0 8px 24px rgba(23,53,43,.08); }
.graph { border-color:#FFFFFF !important; }
.data-table-wrap, .table-panel, .generic-page .panel { border-color:#FFFFFF !important; }
.failure-page-header { position:relative; justify-content:center !important; align-items:center !important; }
.failure-page-header > div:first-child { width:100%; text-align:center; }
.failure-page-header h1 { color:#17352B !important; text-align:center !important; }
.failure-page-header p { color:#6C8278 !important; text-align:center !important; }
.failure-eyebrow { text-align:center !important; }
.failure-page-header .history-live { position:absolute; right:0; top:50%; transform:translateY(-50%); }
.failure-stat, .failure-panel, .failure-card { border-color:#FFFFFF !important; box-shadow:0 8px 24px rgba(23,53,43,.08); }
.failure-card { background:rgba(255,255,255,.035); }


/* FINAL PAGE-HEADING CLEANUP */
.page-subtitle { display:none !important; }
.page-top {
    display:flex !important;
    justify-content:center !important;
    align-items:center !important;
    width:100% !important;
    margin:0 0 30px !important;
    text-align:center !important;
}
.page-top > div:first-child {
    width:100% !important;
    text-align:center !important;
}
.page-top > .outline-btn { display:none !important; }
.page-title,
.stations-page-head h1,
.alert-page-head h1,
.telemetry-page-head h1,
.failure-page-header h1 {
    display:block !important;
    width:100% !important;
    margin:0 !important;
    text-align:center !important;
    color:#123F34 !important;
    font-size:38px !important;
    font-weight:900 !important;
    letter-spacing:-1.2px !important;
    line-height:1.12 !important;
    text-shadow:0 2px 0 rgba(255,255,255,.98), 0 8px 22px rgba(18,63,52,.14) !important;
}
.page-title::after,
.stations-page-head h1::after,
.alert-page-head h1::after,
.telemetry-page-head h1::after,
.failure-page-header h1::after {
    content:"" !important;
    display:block !important;
    width:72px !important;
    height:4px !important;
    margin:12px auto 0 !important;
    border-radius:99px !important;
    background:linear-gradient(90deg,#16A36A,#E05A9D) !important;
    box-shadow:0 4px 12px rgba(22,163,106,.16) !important;
}
.stations-page-head,
.alert-page-head,
.telemetry-page-head,
.failure-page-header {
    display:flex !important;
    justify-content:center !important;
    align-items:center !important;
    width:100% !important;
    margin:0 0 30px !important;
    text-align:center !important;
}
.stations-page-head > div:first-child,
.alert-page-head > div:first-child,
.telemetry-page-head > div:first-child,
.failure-page-header > div:first-child {
    width:100% !important;
    text-align:center !important;
}
.stations-eyebrow,
.alert-eyebrow,
.telemetry-eyebrow,
.failure-eyebrow,
.stations-page-head p,
.alert-page-head p,
.telemetry-page-head p,
.failure-page-header p,
.network-status,
.monitor-pill,
.telemetry-live,
.failure-page-header .history-live {
    display:none !important;
}

/* Unified network-page light cards */
.stations-page-head h1,.telemetry-page-head h1,.alert-page-head h1{color:#17352B!important;font-size:38px!important;font-weight:900!important;letter-spacing:-.8px!important;text-align:center!important;text-shadow:0 2px 12px rgba(22,163,106,.10)!important}
.stations-page-head p,.telemetry-page-head p,.alert-page-head p{color:#5F766B!important;text-align:center!important}
.station-metric,.stations-panel,.station-card,.telemetry-stat,.telemetry-panel,.alert-stat,.alerts-panel,.alert-card{background:#FFF!important;border:2px solid #FFF!important;box-shadow:0 10px 28px rgba(23,53,43,.09)!important;color:#17352B!important}
.station-metric-label,.telemetry-stat-label,.alert-stat span,.station-info-label,.telemetry-panel p,.stations-panel p,.alert-meta,.record-count{color:#61786E!important}
.station-metric-value,.telemetry-stat-value,.alert-stat strong,.station-card-title,.stations-panel h2,.telemetry-panel h2,.alerts-panel h2,.alert-message,.station-card-info strong,.station-card-location,.station-cell strong{color:#17352B!important}
.station-metric-value.green,.telemetry-stat-value.green,.reading.power,.telemetry-status.good{color:#168553!important}
.station-metric-value.pink,.telemetry-stat-value.pink,.reading.humidity{color:#D83F83!important}
.telemetry-stat-value.orange,.reading.temp{color:#C67A18!important}
.station-card-divider{background:#E7F0EB!important}
.station-card-icon,.alert-icon,.empty-icon,.empty-alerts .empty-icon,.stations-empty-icon{background:#F0F8F4!important;border-color:#CBE7D8!important}
.charger-tag.fast,.charger-tag.ac,.charger-tag.standard{background:#EFFAF4!important;border:1px solid #BFE6D1!important;color:#168553!important}
.type-summary-row{border-bottom:1px solid #E7F0EB!important;color:#17352B!important}.type-summary-row strong{color:#D83F83!important}
.telemetry-table,.telemetry-table th,.telemetry-table td,.dash-table{color:#17352B!important}.telemetry-table th{background:#F3F8F5!important;color:#587067!important}.telemetry-table tr:hover td{background:#F7FBF9!important}.telemetry-id{color:#168553!important}
.telemetry-status.good{background:#EFFAF4!important;border-color:#BFE6D1!important}.telemetry-status.warning{background:#FFF7E8!important;color:#A96812!important;border-color:#F2D49B!important}.telemetry-status.danger{background:#FFF1F3!important;color:#C43B55!important;border-color:#F0C5CD!important}
.alert-stat.critical-box{border-left:5px solid #D83F83!important}.alert-stat.warning-box{border-left:5px solid #C67A18!important}.alert-stat.resolved-box{border-left:5px solid #168553!important}.alert-card.critical{border-left:5px solid #D83F83!important}.alert-card.warning{border-left:5px solid #C67A18!important}
.severity.critical,.alert-status.active{color:#C43B55!important;background:#FFF1F3!important}.severity.warning{color:#A96812!important;background:#FFF7E8!important}.alert-status.resolved{color:#168553!important;background:#EFFAF4!important}.view-alert{color:#D83F83!important;background:#FFF4F8!important;border-color:#F1C7DA!important}
.stations-page-head,.telemetry-page-head,.alert-page-head{display:block!important;text-align:center!important;margin-bottom:28px!important}



/* Modern light theme overrides */
.dashboard-body{background:#F4FAF7!important;color:#17352B!important}.main-content{background:#F4FAF7!important}.sidebar{background:#FFF!important;border-right:1px solid #DCE8E2!important;box-shadow:8px 0 28px rgba(23,53,43,.06)!important}.sidebar-logo,.sidebar-logo span{color:#17352B!important}.nav-section{color:#789087!important}.nav-link{color:#4F6B61!important}.nav-link:hover{background:#F4F9F6!important;color:#17352B!important}.nav-link.active{background:linear-gradient(90deg,#EEF9F4,#FFF5FA)!important;color:#17352B!important;border:1px solid #C9E8DA!important;box-shadow:inset 3px 0 0 #16A36A!important}.logout-link{background:#FFF4F5!important;color:#C43B55!important}.panel,.metric-card,.table-panel,.data-table-wrap{background:#FFF!important;border-color:#FFF!important;box-shadow:0 10px 28px rgba(23,53,43,.08)!important}.metric-card:nth-child(3n+1){border-top:4px solid #16A36A!important}.metric-card:nth-child(3n+2){border-top:4px solid #D83F83!important}.metric-card:nth-child(3n){border-top:4px solid #E49A18!important}.metric-title,.section-kicker{color:#6D8379!important}.metric-value{color:#17352B!important}.metric-value.green{color:#16A36A!important}.metric-value.pink{color:#D83F83!important}.metric-value.orange{color:#C77B0B!important}.graph{border-color:#FFF!important}


/* =========================================================
   UI POLISH PACK — DEMO / PRESENTATION PASS
   Keeps the existing backend and page structure intact.
   ========================================================= */

/* Sidebar: stronger hierarchy and cleaner active state */
.sidebar {
    width: 258px !important;
    padding: 26px 15px !important;
    background: rgba(255,255,255,.97) !important;
    border-right: 1px solid #DCE8E2 !important;
    box-shadow: 10px 0 30px rgba(23,53,43,.055) !important;
}
.sidebar-logo {
    padding: 2px 12px 18px !important;
    margin-bottom: 6px !important;
    font-size: 18px !important;
    line-height: 1.25 !important;
    letter-spacing: .8px !important;
    border-bottom: 1px solid #E4EEE9 !important;
}
.sidebar-user {
    color: #789087 !important;
    padding: 12px 12px 17px !important;
}
.nav-section {
    padding: 16px 12px 8px !important;
    color: #8A9B94 !important;
}
.nav-link {
    position: relative !important;
    min-height: 43px !important;
    margin-bottom: 5px !important;
    padding: 11px 13px 11px 15px !important;
    border: 1px solid transparent !important;
    color: #4F6B61 !important;
    font-weight: 650 !important;
}
.nav-link:hover {
    transform: translateX(2px) !important;
    background: #F5FAF7 !important;
    border-color: #E0ECE6 !important;
    color: #17352B !important;
}
.nav-link.active {
    background: linear-gradient(90deg,#EEF9F4 0%,#FFF7FB 100%) !important;
    border-color: #CBE7D9 !important;
    color: #17352B !important;
    box-shadow: inset 4px 0 0 #168553, 0 4px 12px rgba(23,53,43,.045) !important;
    font-weight: 800 !important;
}
.nav-link.active::after {
    content:"" !important;
    position:absolute !important;
    right:10px !important;
    width:6px !important;
    height:6px !important;
    border-radius:50% !important;
    background:#D83F83 !important;
}
.logout-link {
    margin-top: 24px !important;
    padding-top: 13px !important;
    border-top: 1px solid #E4EEE9 !important;
    border-radius: 10px !important;
    background: #FFF7F8 !important;
    color: #C43B55 !important;
}

/* Main content: slightly more breathing room */
.main-content {
    margin-left: 258px !important;
    padding: 38px 44px 60px !important;
}

/* Dashboard / overview metric cards: intentional accent rotation */
.metrics-grid .metric-card {
    background: #FFFFFF !important;
    border: 1px solid #E3EEE8 !important;
    border-top-width: 4px !important;
    box-shadow: 0 10px 26px rgba(23,53,43,.075) !important;
}
.metrics-grid .metric-card:nth-child(1) { border-top-color:#168553 !important; }
.metrics-grid .metric-card:nth-child(2) { border-top-color:#D83F83 !important; }
.metrics-grid .metric-card:nth-child(3) { border-top-color:#E49A18 !important; }
.metrics-grid .metric-card:nth-child(4) { border-top-color:#C43B55 !important; }
.metrics-grid .metric-card:nth-child(5) { border-top-color:#16A36A !important; }
.metrics-grid .metric-card:hover {
    transform: translateY(-4px) !important;
    border-color: #D6E7DF !important;
    box-shadow: 0 16px 32px rgba(23,53,43,.11) !important;
}
.metrics-grid .metric-card::after {
    background: rgba(22,163,106,.055) !important;
}
.metrics-grid .metric-title { color:#71877D !important; }
.metrics-grid .metric-value { color:#17352B !important; }
.metrics-grid .metric-card:nth-child(2) .metric-value { color:#D83F83 !important; }
.metrics-grid .metric-card:nth-child(3) .metric-value { color:#C77B0B !important; }
.metrics-grid .metric-card:nth-child(4) .metric-value { color:#C43B55 !important; }

/* Dashboard panels and tables */
.panel,
.metric-card,
.table-panel,
.data-table-wrap {
    border-radius: 20px !important;
}
.panel:hover {
    box-shadow: 0 14px 32px rgba(23,53,43,.09) !important;
}
.data-table-wrap,
.table-panel {
    overflow: hidden !important;
}
.data-table th,
.data-table td {
    padding: 14px 13px !important;
}
.data-table tbody tr:nth-child(even) {
    background: #FBFDFC !important;
}
.data-table tbody tr:hover {
    background: #F5FAF7 !important;
}
.badge,
.telemetry-status,
.modern-status,
.maintenance-status,
.alert-status,
.severity {
    letter-spacing: .5px !important;
}

/* Analytics: make the health result the visual anchor */
.analytics-metrics .analytics-metric {
    background:#FFFFFF !important;
    border:1px solid #E2EEE8 !important;
    border-top:4px solid #16A36A !important;
    box-shadow:0 9px 25px rgba(23,53,43,.07) !important;
}
.analytics-metrics .analytics-metric:nth-child(2) { border-top-color:#D83F83 !important; }
.analytics-metrics .analytics-metric:nth-child(3) { border-top-color:#E49A18 !important; }
.analytics-metrics .analytics-metric:nth-child(4) { border-top-color:#D83F83 !important; }
.analytics-metrics .analytics-metric:nth-child(5) { border-top-color:#C43B55 !important; }
.analytics-metrics .analytics-metric:nth-child(6) { border-top-color:#168553 !important; }
.analytics-two .analytics-panel,
.analytics-table {
    background:#FFFFFF !important;
    border:1px solid #E2EEE8 !important;
    box-shadow:0 10px 28px rgba(23,53,43,.075) !important;
}
.analytics-panel h2,
.analytics-table h2 { color:#17352B !important; }
.analytics-row {
    padding:14px 0 !important;
    border-bottom:1px solid #E7F0EB !important;
}
.analytics-row strong { color:#17352B !important; }
.health-donut {
    box-shadow:0 14px 30px rgba(22,163,106,.10) !important;
}
.status-strip {
    border-radius:12px !important;
    font-weight:800 !important;
}

/* Predictions: stronger assessment hierarchy */
.prediction-form-card,
.prediction-list-panel {
    border:1px solid #E2EEE8 !important;
}
.prediction-form-card {
    position:relative !important;
    overflow:hidden !important;
}
.prediction-form-card::before {
    content:"" !important;
    position:absolute !important;
    left:0 !important;
    top:0 !important;
    width:100% !important;
    height:4px !important;
    background:linear-gradient(90deg,#168553,#D83F83,#E49A18) !important;
}
.modern-prediction-card {
    border-left:4px solid #168553 !important;
    box-shadow:0 6px 18px rgba(23,53,43,.045) !important;
    transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease !important;
}
.modern-prediction-card:has(.prediction-danger) { border-left-color:#C43B55 !important; }
.modern-prediction-card:has(.prediction-other) { border-left-color:#D83F83 !important; }
.modern-prediction-card:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 12px 24px rgba(23,53,43,.08) !important;
}
.prediction-readings div {
    background:#FBFDFC !important;
}

/* Maintenance: turn records into a clearer status timeline */
.maintenance-card {
    position:relative !important;
    border-left:4px solid #D7E5DE !important;
}
.maintenance-card:has(.maintenance-completed) { border-left-color:#168553 !important; }
.maintenance-card:has(.maintenance-pending) { border-left-color:#E49A18 !important; }
.maintenance-card:has(.maintenance-scheduled) { border-left-color:#D83F83 !important; }
.component-stat {
    border:1px solid #E2EEE8 !important;
    border-top-width:4px !important;
}
.component-stat.total { border-top-color:#168553 !important; }
.component-stat.completed { border-top-color:#16A36A !important; }
.component-stat.pending { border-top-color:#E49A18 !important; }
.component-stat.scheduled { border-top-color:#D83F83 !important; }

/* Alerts: severity should be instantly readable */
.alert-card {
    position:relative !important;
    overflow:hidden !important;
    box-shadow:0 7px 20px rgba(23,53,43,.055) !important;
}
.alert-card.critical { border-left-width:5px !important; border-left-color:#C43B55 !important; }
.alert-card.warning { border-left-width:5px !important; border-left-color:#E49A18 !important; }
.alert-card:hover { box-shadow:0 12px 26px rgba(23,53,43,.09) !important; }
.alert-stat {
    border:1px solid #E2EEE8 !important;
    box-shadow:0 9px 24px rgba(23,53,43,.07) !important;
}

/* Battery: cleaner visual balance */
.battery-hero {
    gap:20px !important;
    align-items:stretch !important;
}
.battery-hero > .panel {
    flex:1 1 0 !important;
}
.metric-list {
    display:grid !important;
    gap:10px !important;
    margin-top:16px !important;
}
.metric-row {
    min-height:54px !important;
    padding:11px 13px !important;
    background:#F8FCFA !important;
    border:1px solid #E1ECE7 !important;
    border-radius:12px !important;
    box-shadow:none !important;
}
.metric-row strong { color:#17352B !important; }
.ai-panel {
    border:1px solid #E9B9D1 !important;
    background:linear-gradient(145deg,#FFF5FA,#FFFFFF) !important;
}
.ai-panel .panel-title,
.ai-panel .insight-text strong { color:#B62F6D !important; }
.ai-accent { color:#B62F6D !important; }
.ai-btn {
    background:#B62F6D !important;
    border-color:#B62F6D !important;
}
.threshold-dot.good {
    background:#168553 !important;
    box-shadow:0 0 0 4px rgba(22,133,83,.10) !important;
}

/* Forms / buttons */
.outline-btn,
.analytics-load {
    border-radius:11px !important;
    font-weight:800 !important;
}
.analytics-load {
    background:#17352B !important;
    border-color:#17352B !important;
    color:#FFFFFF !important;
}
.analytics-load:hover {
    background:#123F34 !important;
}

/* Mobile / smaller laptop layouts */
@media(max-width:1100px) {
    .metrics-grid { grid-template-columns:repeat(3,minmax(0,1fr)) !important; }
    .main-content { padding:32px 28px 50px !important; }
}
@media(max-width:900px) {
    .sidebar { width:220px !important; }
    .main-content { margin-left:220px !important; }
    .metrics-grid { grid-template-columns:repeat(2,minmax(0,1fr)) !important; }
    .battery-hero { flex-direction:column !important; }
}
@media(max-width:650px) {
    .sidebar { position:relative !important; width:100% !important; height:auto !important; max-height:none !important; }
    .main-content { margin-left:0 !important; padding:24px 16px 40px !important; }
    .metrics-grid { grid-template-columns:1fr !important; }
    .page-title { font-size:30px !important; }
    .page-top { margin-bottom:22px !important; }
}

/* ===== COMPLETE PRESENTATION UI PASS ===== */
:root{--g:#168553;--g2:#16A36A;--p:#D83F83;--p2:#E05A9D;--o:#E49A18;--r:#C43B55;--ink:#17352B;--muted:#71877D;--line:#DFECE6}
body.dashboard-body{background:linear-gradient(180deg,#F3F9F6,#FAFCFB 55%,#F2F8F5)!important;color:var(--ink)!important}
.sidebar{width:258px!important;background:linear-gradient(180deg,#FFFFFF 0%,#FBFDFC 58%,#F6FAF8 100%)!important;border-right:1px solid #DCE8E2!important;border-top:0!important;border-bottom:0!important;border-left:0!important;box-shadow:10px 0 30px rgba(23,53,43,.07)!important;backdrop-filter:none!important}
.sidebar-logo{margin:2px 8px 24px!important;padding:16px 15px!important;border:1px solid #DCE8E2!important;border-radius:16px!important;background:linear-gradient(135deg,#F1FAF5,#FFF4F8)!important;box-shadow:0 8px 22px rgba(23,53,43,.055)!important;color:#17352B!important}
.sidebar-logo span{color:#17352B!important}
.nav-section{margin:20px 12px 7px!important;color:#8A9B94!important;font-size:10px!important;font-weight:900!important;letter-spacing:1.5px!important}
.sidebar a,.sidebar .nav-link{margin:4px 10px!important;padding:11px 14px!important;border-radius:12px!important;border:1px solid transparent!important;color:#526A61!important;font-weight:700!important;transition:all .2s ease!important}
.sidebar a:hover,.sidebar .nav-link:hover{background:#F1F7F4!important;color:#17352B!important;border-color:#E0ECE7!important;transform:translateX(3px)!important}
.sidebar a.active,.sidebar .nav-link.active{background:linear-gradient(90deg,#ECF8F2,#FFF4F8)!important;color:#17352B!important;border:1px solid #D5E9DF!important;box-shadow:inset 4px 0 #168553,0 5px 14px rgba(23,53,43,.055)!important}
.sidebar a.active:after,.sidebar .nav-link.active:after{content:"";float:right;width:6px;height:6px;margin-top:6px;border-radius:50%;background:#D83F83!important;box-shadow:0 0 0 4px rgba(216,63,131,.09)!important}
.logout-link{margin-top:24px!important;background:#FFF4F5!important;color:#B83B55!important;border-color:#F3D7DD!important;border-top:1px solid #F3D7DD!important}
.logout-link:hover{background:#FFECEF!important;color:#A92F49!important;border-color:#EDC6CF!important}
.page-title{font-weight:900!important;letter-spacing:-1px!important;color:var(--ink)!important}.page-subtitle{color:var(--muted)!important;font-weight:600!important}.section-kicker{color:var(--p)!important;font-weight:900!important;letter-spacing:1.4px!important}
.panel,.func-panel,.stations-panel,.alerts-panel,.maintenance-panel,.analytics-panel,.analytics-table,.prediction-list-panel,.prediction-form-card{background:#fff!important;border:1px solid var(--line)!important;border-radius:20px!important;box-shadow:0 12px 30px rgba(23,53,43,.065)!important}
/* dashboard */
.dashboard-page{max-width:1280px!important;padding:34px!important}.dashboard-hero{padding-bottom:34px!important}.dashboard-hero h1{font-size:46px!important;color:var(--ink)!important}.dashboard-metrics{gap:18px!important;margin-bottom:22px!important}.dash-metric{min-height:136px!important;border:1px solid var(--line)!important;border-top:4px solid var(--g)!important;border-radius:20px!important;box-shadow:0 12px 30px rgba(23,53,43,.06)!important;transition:.2s!important}.dash-metric:hover,.station-card:hover,.component-stat:hover,.modern-prediction-card:hover{transform:translateY(-4px)!important;box-shadow:0 17px 34px rgba(23,53,43,.10)!important}.dash-metric:nth-child(2),.dash-metric:nth-child(6){border-top-color:var(--p)!important}.dash-metric:nth-child(3),.dash-metric:nth-child(7){border-top-color:var(--o)!important}.dash-metric:nth-child(4){border-top-color:var(--r)!important}.dash-metric:nth-child(5),.dash-metric:nth-child(8){border-top-color:var(--g2)!important}.dash-metric:nth-child(2) .dash-metric-value,.dash-metric:nth-child(6) .dash-metric-value{color:var(--p)!important}.dash-metric:nth-child(3) .dash-metric-value,.dash-metric:nth-child(7) .dash-metric-value{color:#B8750B!important}.dash-metric:nth-child(4) .dash-metric-value{color:var(--r)!important}.dash-panel{border:1px solid var(--line)!important;border-radius:22px!important;box-shadow:0 12px 30px rgba(23,53,43,.065)!important}.dash-chart{height:285px!important}.dash-ring{width:182px!important;height:182px!important;box-shadow:0 10px 28px rgba(22,163,106,.10)!important}.dash-table td{transition:.15s!important}.dash-table tr:hover td{background:#EFF8F3!important}.dash-insight{background:linear-gradient(105deg,#F0FAF5,#FFF2F8)!important;border:1px solid #F0D0DF!important}.dash-insight-action{background:var(--p)!important;color:#fff!important;border-color:var(--p)!important}
/* stations */
.stations-layout{grid-template-columns:minmax(0,1fr) 300px!important;gap:22px!important}.station-metric{background:#fff!important;border:1px solid var(--line)!important;border-top:4px solid var(--g)!important;box-shadow:0 11px 28px rgba(23,53,43,.06)!important}.station-metric:nth-child(2){border-top-color:var(--p)!important}.station-metric:nth-child(3){border-top-color:var(--o)!important}.station-card{background:#fff!important;border:1px solid var(--line)!important;border-left:4px solid var(--g)!important;border-radius:19px!important;box-shadow:0 8px 24px rgba(23,53,43,.05)!important;transition:.2s!important}.station-card:nth-child(2n){border-left-color:var(--p)!important}.station-card:nth-child(3n){border-left-color:var(--o)!important}.station-card-title{font-size:20px!important;font-weight:900!important}.station-card-location{font-size:12px!important}
/* alerts */
.alert-stat{background:#fff!important;border:1px solid var(--line)!important;border-radius:19px!important;box-shadow:0 11px 28px rgba(23,53,43,.06)!important}.alert-card{background:#fff!important;border:1px solid var(--line)!important;border-left:5px solid var(--o)!important;border-radius:17px!important;box-shadow:0 8px 22px rgba(23,53,43,.05)!important;transition:.2s!important}.alert-card.critical{border-left-color:var(--r)!important;background:linear-gradient(90deg,#FFF7F8,#fff 38%)!important}.alert-card.warning{border-left-color:var(--o)!important;background:linear-gradient(90deg,#FFFBF2,#fff 38%)!important}.alert-card:hover{transform:translateX(3px)!important}.view-alert{background:var(--p)!important;color:#fff!important;border:0!important;border-radius:10px!important}
/* maintenance */
.component-stat{background:#fff!important;border:1px solid var(--line)!important;border-radius:19px!important;box-shadow:0 10px 26px rgba(23,53,43,.06)!important;transition:.2s!important}.maintenance-card{background:#fff!important;border:1px solid var(--line)!important;border-left:5px solid var(--g)!important;border-radius:18px!important;box-shadow:0 8px 23px rgba(23,53,43,.05)!important;transition:.2s!important;position:relative!important;overflow:hidden!important}.maintenance-card:has(.maintenance-pending){border-left-color:var(--o)!important}.maintenance-card:has(.maintenance-scheduled){border-left-color:var(--p)!important}.maintenance-card:after{content:"";position:absolute;left:0;bottom:0;height:3px;width:100%;background:linear-gradient(90deg,var(--g),transparent);opacity:.35}
/* prediction */
.prediction-form-card{position:relative!important;overflow:hidden!important}.prediction-form-card:before{content:"";position:absolute;left:0;top:0;width:100%;height:5px;background:linear-gradient(90deg,var(--g),var(--o),var(--p))}.prediction-stat{border:1px solid var(--line)!important;box-shadow:0 10px 26px rgba(23,53,43,.06)!important}.modern-prediction-card{background:#fff!important;border:1px solid var(--line)!important;border-left:5px solid var(--g)!important;box-shadow:0 8px 22px rgba(23,53,43,.05)!important}.modern-prediction-card:has(.prediction-danger){border-left-color:var(--r)!important;background:linear-gradient(90deg,#FFF7F8,#fff 35%)!important}.modern-prediction-card:has(.prediction-other){border-left-color:var(--o)!important;background:linear-gradient(90deg,#FFFCF5,#fff 35%)!important}
/* analytics */
.analytics-selector{border:1px solid var(--line)!important;box-shadow:0 11px 28px rgba(23,53,43,.06)!important}.analytics-load{background:linear-gradient(135deg,var(--g),#2BAA78)!important}.analytics-metric{border:1px solid var(--line)!important;box-shadow:0 9px 25px rgba(23,53,43,.055)!important;transition:.2s!important}.analytics-metric:hover{transform:translateY(-3px)!important}.analytics-panel,.analytics-table{border:1px solid var(--line)!important;box-shadow:0 11px 28px rgba(23,53,43,.06)!important}.analytics-table tbody tr:hover td{background:#F3F9F6!important}
/* generic tables / topbar */
table tbody tr{transition:.15s!important}.topbar{background:rgba(255,255,255,.88)!important;border-bottom:1px solid var(--line)!important;backdrop-filter:blur(10px)!important}
@media(max-width:1100px){.dashboard-metrics{grid-template-columns:repeat(2,1fr)!important}.stations-layout{grid-template-columns:1fr!important}}@media(max-width:700px){.dashboard-metrics,.stations-metrics,.alert-stats,.prediction-stats{grid-template-columns:1fr!important}.dashboard-grid,.dashboard-lists,.analytics-two{grid-template-columns:1fr!important}.dashboard-page{padding:24px 15px!important}.dashboard-hero h1{font-size:36px!important}}

</style>
"""


# =========================================================
# SIDEBAR
# =========================================================


def sidebar(active):
    return f"""
    <div class="sidebar">
        <div class="sidebar-logo"><span>EV CHARGING STATION<br>HEALTH CARE</span></div>

        <div class="nav-section">OVERVIEW</div>
        <a href="/dashboard" class="nav-link {'active' if active == 'dashboard' else ''}"><span>Dashboard</span></a>

        <div class="nav-section">MONITORING</div>
        <a href="/stations" class="nav-link {'active' if active == 'stations' else ''}"><span>Charging Stations</span></a>
        <a href="/analytics" class="nav-link {'active' if active == 'analytics' else ''}"><span>Station Analytics</span></a>
        <a href="/telemetry" class="nav-link {'active' if active == 'telemetry' else ''}"><span>Telemetry</span></a>
        <a href="/battery-health" class="nav-link {'active' if active == 'battery' else ''}"><span>Battery Health</span></a>

        <div class="nav-section">INTELLIGENCE</div>
        <a href="/predictions" class="nav-link {'active' if active == 'predictions' else ''}"><span>Predictions</span></a>
        <a href="/maintenance" class="nav-link {'active' if active == 'maintenance' else ''}"><span>Maintenance</span></a>

        <div class="nav-section">INCIDENTS</div>
        <a href="/alerts" class="nav-link {'active' if active == 'alerts' else ''}"><span>Alerts</span></a>
        <a href="/failure-history" class="nav-link {'active' if active == 'failure' else ''}"><span>Failure History</span></a>

        <div class="nav-section">OPERATIONS</div>
        <a href="/charging-sessions" class="nav-link {'active' if active == 'sessions' else ''}"><span>Charging Sessions</span></a>
        <a href="/operators" class="nav-link {'active' if active == 'operators' else ''}"><span>Operators</span></a>
        <a href="/feedback" class="nav-link {'active' if active == 'feedback' else ''}"><span>Feedback</span></a>
        <a href="/logout" class="nav-link logout-link"><span>Logout</span></a>
    </div>
    """


# =========================================================
# TOP HEADER
# =========================================================


def topbar(page_title, page_subtitle="Network monitoring and health intelligence"):
    # The page-level heading is the single source of page identity.
    # Keep this helper for compatibility with existing templates, but
    # intentionally render no duplicate header, system status, or user pill.
    return ""


# =========================================================
# GENERIC TABLE PAGE
# Automatically displays actual database table data
# =========================================================


def show_table_page(table_name, title, subtitle, active):
    if "user" not in session:
        return redirect("/")

    conn = get_db()
    try:
        records = conn.execute(
            f"SELECT * FROM {table_name} ORDER BY rowid DESC"
        ).fetchall()
    except sqlite3.Error:
        records = []
    finally:
        conn.close()

    columns = list(records[0].keys()) if records else []

    def label(column):
        return column.replace("_", " ").title()

    def value_text(record, column):
        value = record[column]
        return "-" if value is None or str(value).strip() == "" else str(value)

    def find_column(names):
        lowered = {c.lower(): c for c in columns}
        for name in names:
            if name.lower() in lowered:
                return lowered[name.lower()]
        return None

    def esc(value):
        return html.escape(str(value))

    primary_col = find_column(
        ["station_name", "operator_name", "name", "session_id", "id"]
    )
    secondary_col = find_column(
        ["location", "email", "station_id", "charging_station_id", "charger_type"]
    )
    status_col = find_column(["status", "session_status", "rating", "resolved"])
    date_col = find_column(
        ["session_date", "date", "created_at", "feedback_date", "maintenance_date"]
    )
    if not primary_col and columns:
        primary_col = columns[0]

    total = len(records)
    status_counts = {}
    if status_col:
        for record in records:
            key = value_text(record, status_col).strip().lower()
            status_counts[key] = status_counts.get(key, 0) + 1

    def count_matching(*terms):
        return sum(
            count
            for key, count in status_counts.items()
            if any(term in key for term in terms)
        )

    if table_name == "charging_sessions":
        stat_items = [
            ("Total Sessions", total, "green"),
            ("Completed", count_matching("completed", "complete", "finished"), "green"),
            ("Active", count_matching("active", "charging", "in progress"), "pink"),
            ("Pending", count_matching("pending", "scheduled", "waiting"), "gold"),
        ]
        kicker, panel_title, empty_text, record_kicker = (
            "SESSION ACTIVITY",
            "Charging Session Records",
            "No charging session records are available.",
            "CHARGING SESSION",
        )
    elif table_name == "operators":
        stat_items = [
            ("Total Operators", total, "green"),
            ("Active", count_matching("active", "approved", "verified"), "green"),
            ("Pending", count_matching("pending", "inactive", "review"), "gold"),
            ("Registered", total, "pink"),
        ]
        kicker, panel_title, empty_text, record_kicker = (
            "NETWORK OPERATIONS",
            "Operator Records",
            "No operator records are available.",
            "OPERATOR RECORD",
        )
    else:
        stat_items = [
            ("Total Feedback", total, "green"),
            (
                "Positive",
                count_matching("positive", "good", "excellent", "5", "4"),
                "green",
            ),
            (
                "Needs Review",
                count_matching(
                    "negative", "poor", "bad", "issue", "complaint", "1", "2"
                ),
                "pink",
            ),
            ("Responses", count_matching("responded", "resolved", "closed"), "gold"),
        ]
        kicker, panel_title, empty_text, record_kicker = (
            "USER EXPERIENCE",
            "Feedback Records",
            "No feedback records are available.",
            "FEEDBACK RECORD",
        )

    cards = []
    for record in records:
        primary = value_text(record, primary_col) if primary_col else "Record"
        secondary = value_text(record, secondary_col) if secondary_col else ""
        status = value_text(record, status_col) if status_col else ""
        date_value = value_text(record, date_col) if date_col else ""

        status_lower = status.lower()
        if any(
            x in status_lower
            for x in (
                "complete",
                "completed",
                "active",
                "approved",
                "verified",
                "positive",
                "excellent",
            )
        ):
            status_class = "ops-status-green"
        elif any(
            x in status_lower for x in ("pending", "scheduled", "waiting", "review")
        ):
            status_class = "ops-status-gold"
        elif any(
            x in status_lower
            for x in ("negative", "failed", "issue", "complaint", "inactive")
        ):
            status_class = "ops-status-pink"
        else:
            status_class = "ops-status-neutral"

        excluded = {c for c in (primary_col, status_col, date_col) if c}
        detail_columns = [c for c in columns if c not in excluded][:4]
        details = []
        for col in detail_columns:
            details.append(
                f'<div class="ops-detail"><span>{esc(label(col))}</span><strong>{esc(value_text(record, col))}</strong></div>'
            )

        status_html = (
            f'<span class="ops-status {status_class}">{esc(status)}</span>'
            if status
            else ""
        )
        secondary_html = f"<p>{esc(secondary)}</p>" if secondary else ""
        date_html = (
            f'<div class="ops-date"><span>{esc(label(date_col))}</span><strong>{esc(date_value)}</strong></div>'
            if date_col and date_value
            else ""
        )
        cards.append(
            f'<article class="ops-record-card"><div class="ops-record-top"><div><div class="ops-kicker">{esc(record_kicker)}</div><h3>{esc(primary)}</h3>{secondary_html}</div>{status_html}</div>{date_html}<div class="ops-details">{"".join(details)}</div></article>'
        )

    stats_html = "".join(
        f'<div class="ops-stat {tone}"><span>{esc(name)}</span><strong>{number}</strong></div>'
        for name, number, tone in stat_items
    )
    records_html = (
        "".join(cards)
        if cards
        else f'<div class="ops-empty"><strong>{esc(empty_text)}</strong><span>Records will appear here when the database contains data.</span></div>'
    )

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>{esc(title)}</title>
    {STYLE}
    <style>
        .ops-page {{ max-width:1180px; margin:0 auto; padding:42px 28px 60px; }}
        .ops-title-wrap {{ text-align:center; margin:8px 0 30px; }}
        .ops-title {{ margin:0; color:#17352B; font-size:40px; line-height:1.1; font-weight:900; letter-spacing:-1.4px; }}
        .ops-title::after {{ content:""; display:block; width:92px; height:5px; margin:14px auto 0; border-radius:99px; background:linear-gradient(90deg,#16A36A,#D95B9D); }}
        .ops-subtitle {{ margin:13px auto 0; color:#71877D; font-size:15px; max-width:620px; line-height:1.6; }}
        .ops-stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:18px; margin-bottom:28px; }}
        .ops-stat {{ background:#fff; border:1px solid #fff; border-top:4px solid #16A36A; border-radius:18px; padding:22px; box-shadow:0 10px 28px rgba(23,53,43,.08); min-height:104px; }}
        .ops-stat.pink {{ border-top-color:#D95B9D; }} .ops-stat.gold {{ border-top-color:#E7A52B; }}
        .ops-stat span {{ display:block; color:#70857C; font-size:11px; font-weight:800; letter-spacing:1.2px; text-transform:uppercase; }}
        .ops-stat strong {{ display:block; margin-top:9px; color:#17352B; font-size:32px; line-height:1; font-weight:900; }}
        .ops-panel {{ background:#fff; border:1px solid #fff; border-radius:22px; padding:28px 24px; box-shadow:0 10px 28px rgba(23,53,43,.07); }}
        .ops-panel-head {{ display:flex; align-items:end; justify-content:space-between; gap:20px; margin-bottom:18px; }}
        .ops-panel-kicker {{ color:#168553; font-size:10px; font-weight:900; letter-spacing:1.6px; margin-bottom:7px; }}
        .ops-panel-title {{ margin:0; color:#17352B; font-size:22px; font-weight:850; }}
        .ops-count {{ color:#6F847B; font-size:13px; font-weight:700; white-space:nowrap; }}
        .ops-records {{ display:grid; gap:16px; }}
        .ops-record-card {{ background:#F7FBF9; border:1px solid #DDEBE4; border-radius:18px; padding:21px; }}
        .ops-record-top {{ display:flex; justify-content:space-between; gap:20px; align-items:flex-start; }}
        .ops-kicker {{ color:#168553; font-size:9px; font-weight:900; letter-spacing:1.5px; margin-bottom:6px; }}
        .ops-record-card h3 {{ margin:0; color:#17352B; font-size:19px; font-weight:850; }}
        .ops-record-card p {{ margin:5px 0 0; color:#71877D; font-size:13px; }}
        .ops-status {{ display:inline-flex; align-items:center; justify-content:center; min-width:92px; padding:7px 11px; border-radius:999px; font-size:10px; font-weight:900; letter-spacing:1px; text-transform:uppercase; border:1px solid; }}
        .ops-status-green {{ color:#168553; background:#EFFAF4; border-color:#BFE6D1; }} .ops-status-gold {{ color:#A66A00; background:#FFF8E8; border-color:#F2D99D; }} .ops-status-pink {{ color:#B13B76; background:#FFF0F7; border-color:#F2C5DC; }} .ops-status-neutral {{ color:#61766D; background:#F1F5F3; border-color:#D8E3DE; }}
        .ops-date {{ margin-top:16px; background:#fff; border:1px solid #DFEAE5; border-radius:12px; padding:11px 14px; display:flex; justify-content:space-between; gap:16px; }}
        .ops-date span, .ops-detail span {{ color:#7A8E86; font-size:9px; font-weight:900; letter-spacing:1.2px; text-transform:uppercase; }}
        .ops-date strong, .ops-detail strong {{ color:#355349; font-size:12px; font-weight:800; }}
        .ops-details {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:10px; }}
        .ops-detail {{ background:#fff; border:1px solid #DFEAE5; border-radius:12px; padding:11px 13px; min-width:0; }}
        .ops-detail span {{ display:block; margin-bottom:5px; }} .ops-detail strong {{ display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
        .ops-empty {{ padding:46px 20px; text-align:center; background:#F7FBF9; border:1px dashed #CFE0D8; border-radius:16px; }}
        .ops-empty strong {{ display:block; color:#355349; font-size:16px; }} .ops-empty span {{ display:block; margin-top:7px; color:#7A8E86; font-size:13px; }}
        @media (max-width:900px) {{ .ops-stats {{ grid-template-columns:repeat(2,1fr); }} .ops-details {{ grid-template-columns:repeat(2,1fr); }} }}
        @media (max-width:600px) {{ .ops-page {{ padding:28px 16px 45px; }} .ops-title {{ font-size:32px; }} .ops-stats {{ grid-template-columns:1fr; }} .ops-panel {{ padding:21px 15px; }} .ops-record-top {{ flex-direction:column; }} .ops-details {{ grid-template-columns:1fr; }} .ops-date {{ flex-direction:column; gap:4px; }} }}
    </style>
</head>
<body class="dashboard-body">
    {sidebar(active)}
    <main class="main-content"><div class="ops-page">
        <section class="ops-title-wrap"><h1 class="ops-title">{esc(title)}</h1></section>
        <section class="ops-stats">{stats_html}</section>
        <section class="ops-panel"><div class="ops-panel-head"><div><div class="ops-panel-kicker">{esc(kicker)}</div><h2 class="ops-panel-title">{esc(panel_title)}</h2></div><div class="ops-count">{total} records</div></div><div class="ops-records">{records_html}</div></section>
    </div></main>
</body>
</html>"""


# =========================================================
# LOGIN
# =========================================================


@app.route("/", methods=["GET", "POST"])
def login():

    message = ""

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        try:
            user = conn.execute(
                "SELECT * FROM users WHERE email=? AND password=?",
                (email, password),
            ).fetchone()
        except sqlite3.Error:
            user = None

        conn.close()

        if user:
            session["user"] = email
            session["name"] = user["name"] if "name" in user.keys() else email
            return redirect("/dashboard")

        message = "Invalid email or password"

    return render_template_string(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login</title>
            {STYLE}
        </head>

        <body class="login-body">

            <div class="login-navbar">
                <div class="login-brand">
                    <span>EV CHARGING STATION HEALTH CARE</span>
                </div>
            </div>

            <div class="login-container">

                <div class="login-card">

                    <h1>EV Charging Station Health Care</h1>

                    {{% if message %}}
                    <div class="error">
                        {{{{ message }}}}
                    </div>
                    {{% endif %}}

                    <form method="POST">

                        <label>Email</label>
                        <input
                            type="email"
                            name="email"
                            placeholder="Enter your email"
                            required
                        >

                        <label>Password</label>
                        <input
                            type="password"
                            name="password"
                            placeholder="Enter your password"
                            required
                        >

                        <button type="submit" class="login-btn">
                            Sign In
                        </button>

                    </form>

                    <div class="login-link">
                        Don't have an account?<br>
                        <a href="/register">Create Account</a>
                    </div>

                </div>

            </div>

        </body>
        </html>
        """,
        message=message,
    )


# =========================================================
# REGISTER
# =========================================================


@app.route("/register", methods=["GET", "POST"])
def register():

    message = ""

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        try:
            existing = conn.execute(
                "SELECT * FROM users WHERE email=?",
                (email,),
            ).fetchone()

            if existing:
                message = "Email already exists"

            else:
                conn.execute(
                    """
                    INSERT INTO users (name, email, password)
                    VALUES (?, ?, ?)
                    """,
                    (name, email, password),
                )
                conn.commit()
                conn.close()
                return redirect("/")

        except sqlite3.Error as e:
            message = f"Registration error: {e}"

        conn.close()

    return render_template_string(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Create Account</title>
            {STYLE}
        </head>

        <body class="login-body">

            <div class="login-navbar">
                <div class="login-brand">
                    <span>EV CHARGING STATION HEALTH CARE</span>
                </div>
            </div>

            <div class="login-container">

                <div class="login-card">

                    <h1>Create Account</h1>

                    <p>
                        Create an account to access the EV monitoring dashboard.
                    </p>

                    {{% if message %}}
                    <div class="error">
                        {{{{ message }}}}
                    </div>
                    {{% endif %}}

                    <form method="POST">

                        <label>Full Name</label>
                        <input
                            type="text"
                            name="name"
                            placeholder="Enter your name"
                            required
                        >

                        <label>Email</label>
                        <input
                            type="email"
                            name="email"
                            placeholder="Enter your email"
                            required
                        >

                        <label>Password</label>
                        <input
                            type="password"
                            name="password"
                            placeholder="Create a password"
                            required
                        >

                        <button type="submit" class="login-btn">
                            Create Account
                        </button>

                    </form>

                    <div class="login-link">
                        Already have an account?<br>
                        <a href="/">Back to Login</a>
                    </div>

                </div>

            </div>

        </body>
        </html>
        """,
        message=message,
    )


# =========================================================
# DASHBOARD
# =========================================================


@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    # -----------------------------------------------------
    # BASIC COUNTS
    # -----------------------------------------------------

    stations = conn.execute("SELECT COUNT(*) FROM charging_stations").fetchone()[0]

    telemetry_count = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]

    maintenance_count = conn.execute("SELECT COUNT(*) FROM maintenance").fetchone()[0]

    alerts_count = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]

    # -----------------------------------------------------
    # TELEMETRY DATA
    # -----------------------------------------------------

    recent = conn.execute(
        """
        SELECT temperature, humidity, power_consumption
        FROM telemetry
        ORDER BY id DESC
        LIMIT 15
        """
    ).fetchall()

    # -----------------------------------------------------
    # RECENT ALERTS
    # -----------------------------------------------------

    recent_alerts = conn.execute(
        """
        SELECT *
        FROM alerts
        ORDER BY id DESC
        LIMIT 5
        """
    ).fetchall()

    # -----------------------------------------------------
    # RECENT FAILURES
    # -----------------------------------------------------

    recent_failures = conn.execute(
        """
        SELECT *
        FROM failure_history
        ORDER BY id DESC
        LIMIT 5
        """
    ).fetchall()

    # -----------------------------------------------------
    # PREDICTIONS
    # -----------------------------------------------------

    prediction_records = conn.execute(
        """
        SELECT *
        FROM predictions
        """
    ).fetchall()

    # -----------------------------------------------------
    # RECENT CHARGING SESSIONS
    # -----------------------------------------------------

    recent_sessions = conn.execute(
        """
        SELECT *
        FROM charging_sessions
        ORDER BY id DESC
        LIMIT 5
        """
    ).fetchall()

    conn.close()

    # -----------------------------------------------------
    # BATTERY HEALTH
    # -----------------------------------------------------

    if recent:

        latest = recent[0]

        latest_temp = latest["temperature"] or 0
        latest_power = latest["power_consumption"] or 0

        battery = calculate_health(latest_temp, latest_power)

    else:

        battery = 0

    # -----------------------------------------------------
    # TELEMETRY GRAPH
    # -----------------------------------------------------

    reversed_data = list(reversed(recent))

    points = []

    if reversed_data:

        values = [item["temperature"] or 0 for item in reversed_data]

        maximum = max(values) if max(values) else 1

        total = len(values)

        for i, value in enumerate(values):

            x = 20 + (i * 400 / max(1, total - 1))

            y = 220 - (value / maximum * 180)

            points.append(f"{x},{y}")

    graph_points = " ".join(points)

    # -----------------------------------------------------
    # PREDICTION SUMMARY
    # -----------------------------------------------------

    healthy_predictions = 0
    warning_predictions = 0
    critical_predictions = 0

    for prediction in prediction_records:

        prediction_text = " ".join(
            str(prediction[column])
            for column in prediction.keys()
            if prediction[column] is not None
        ).lower()

        if "critical" in prediction_text or "failure" in prediction_text:

            critical_predictions += 1

        elif (
            "warning" in prediction_text
            or "maintenance" in prediction_text
            or "moderate" in prediction_text
        ):

            warning_predictions += 1

        else:

            healthy_predictions += 1

    # -----------------------------------------------------
    # ALERT HTML
    # -----------------------------------------------------

    alerts_html = ""

    if recent_alerts:

        for alert in recent_alerts:

            alert_text = " | ".join(
                str(alert[column])
                for column in alert.keys()
                if alert[column] is not None
            )

            alerts_html += f"""
            <tr>
                <td>{alert_text}</td>
            </tr>
            """

    else:

        alerts_html = """
        <tr>
            <td>No recent alerts.</td>
        </tr>
        """

    # -----------------------------------------------------
    # FAILURE HTML
    # -----------------------------------------------------

    failures_html = ""

    if recent_failures:

        for failure in recent_failures:

            failure_text = " | ".join(
                str(failure[column])
                for column in failure.keys()
                if failure[column] is not None
            )

            failures_html += f"""
            <tr>
                <td>{failure_text}</td>
            </tr>
            """

    else:

        failures_html = """
        <tr>
            <td>No failure history available.</td>
        </tr>
        """

    # -----------------------------------------------------
    # SESSION HTML
    # -----------------------------------------------------

    sessions_html = ""

    if recent_sessions:

        for charging_session in recent_sessions:

            session_text = " | ".join(
                str(charging_session[column])
                for column in charging_session.keys()
                if charging_session[column] is not None
            )

            sessions_html += f"""
            <tr>
                <td>{session_text}</td>
            </tr>
            """

    else:

        sessions_html = """
        <tr>
            <td>No charging sessions available.</td>
        </tr>
        """

    # =====================================================
    # DASHBOARD HTML
    # =====================================================

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EV Health Dashboard</title>
        {STYLE}
        <style>
            .dashboard-page {{
                max-width: 1220px;
                margin: 0 auto;
                padding: 28px 30px 42px;
            }}
            .dashboard-hero {{
                text-align: center;
                padding: 8px 0 28px;
            }}
            .dashboard-hero h1 {{
                margin: 0;
                color: #17352B;
                font-size: 42px;
                line-height: 1.05;
                font-weight: 900;
                letter-spacing: -1.4px;
                text-shadow: 0 2px 10px rgba(23,53,43,.08);
            }}
            .dashboard-hero h1::after {{
                content: "";
                display: block;
                width: 235px;
                height: 5px;
                margin: 13px auto 0;
                border-radius: 99px;
                background: linear-gradient(90deg,#16A36A 0%,#8CCF73 48%,#D9579B 100%);
                box-shadow: 0 4px 12px rgba(217,87,155,.16);
            }}
            .dashboard-hero p {{
                margin: 14px auto 0;
                color: #71877D;
                font-size: 15px;
                font-weight: 600;
                letter-spacing: .15px;
            }}
            .dashboard-metrics {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0,1fr));
                gap: 16px;
                margin-bottom: 18px;
            }}
            .dash-metric {{
                position: relative;
                min-height: 126px;
                padding: 22px 22px 18px;
                border: 1px solid #FFFFFF;
                border-top: 4px solid #16A36A;
                border-radius: 18px;
                background: #FFFFFF;
                box-shadow: 0 10px 26px rgba(23,53,43,.075);
                overflow: hidden;
            }}
            .dash-metric::after {{
                content: "";
                position: absolute;
                width: 86px;
                height: 86px;
                right: -30px;
                top: -34px;
                border-radius: 50%;
                background: rgba(22,163,106,.08);
            }}
            .dash-metric.pink {{ border-top-color:#D9579B; }}
            .dash-metric.pink::after {{ background:rgba(217,87,155,.09); }}
            .dash-metric.orange {{ border-top-color:#E9A52B; }}
            .dash-metric.orange::after {{ background:rgba(233,165,43,.10); }}
            .dash-metric-label {{
                color:#71877D;
                font-size:11px;
                font-weight:800;
                letter-spacing:1.25px;
                text-transform:uppercase;
            }}
            .dash-metric-value {{
                margin-top:9px;
                color:#17352B;
                font-size:32px;
                line-height:1;
                font-weight:900;
                letter-spacing:-.7px;
            }}
            .dash-metric-note {{
                margin-top:9px;
                color:#80948C;
                font-size:12px;
                font-weight:600;
            }}
            .dashboard-grid {{
                display:grid;
                grid-template-columns:minmax(0,1.45fr) minmax(320px,.85fr);
                gap:18px;
                margin-bottom:18px;
            }}
            .dash-panel {{
                background:#FFFFFF;
                border:1px solid #FFFFFF;
                border-radius:20px;
                padding:22px;
                box-shadow:0 10px 26px rgba(23,53,43,.075);
                min-width:0;
            }}
            .dash-panel-head {{
                display:flex;
                align-items:flex-start;
                justify-content:space-between;
                gap:14px;
                margin-bottom:17px;
            }}
            .dash-panel-title {{
                margin:0;
                color:#17352B;
                font-size:18px;
                font-weight:850;
            }}
            .dash-panel-subtitle {{
                margin-top:5px;
                color:#81958D;
                font-size:12px;
                font-weight:600;
            }}
            .dash-pill {{
                flex:none;
                padding:7px 11px;
                border-radius:999px;
                border:1px solid #BFE6D1;
                background:#EFFAF4;
                color:#168553;
                font-size:10px;
                font-weight:850;
                letter-spacing:.8px;
            }}
            .dash-pill.pink {{
                border-color:#F2C4DA;
                background:#FFF2F8;
                color:#C33D78;
            }}
            .dash-chart {{
                width:100%;
                height:270px;
                display:block;
                border:1px solid #E5EEE9;
                border-radius:14px;
                background:#FBFDFC;
            }}
            .health-summary {{
                display:flex;
                align-items:center;
                justify-content:center;
                gap:24px;
                min-height:270px;
            }}
            .dash-ring {{
                width:170px;
                height:170px;
                border-radius:50%;
                display:grid;
                place-items:center;
                background:conic-gradient(#16A36A 0deg 270deg,#D9579B 270deg 324deg,#E9A52B 324deg 360deg);
                position:relative;
                flex:none;
            }}
            .dash-ring::before {{
                content:"";
                width:124px;
                height:124px;
                border-radius:50%;
                background:#FFFFFF;
                position:absolute;
            }}
            .dash-ring-center {{
                position:relative;
                z-index:1;
                text-align:center;
            }}
            .dash-ring-value {{
                color:#17352B;
                font-size:28px;
                font-weight:900;
            }}
            .dash-ring-label {{
                color:#71877D;
                font-size:10px;
                font-weight:850;
                letter-spacing:1px;
                text-transform:uppercase;
            }}
            .health-legend {{ display:grid; gap:14px; min-width:125px; }}
            .health-legend-row {{ display:flex; align-items:center; justify-content:space-between; gap:14px; color:#536A61; font-size:12px; font-weight:700; }}
            .health-legend-name {{ display:flex; align-items:center; gap:8px; }}
            .legend-dot {{ width:10px; height:10px; border-radius:50%; background:#16A36A; }}
            .legend-dot.pink {{ background:#D9579B; }}
            .legend-dot.orange {{ background:#E9A52B; }}
            .dashboard-lists {{
                display:grid;
                grid-template-columns:repeat(2,minmax(0,1fr));
                gap:18px;
                margin-bottom:18px;
            }}
            .dash-table {{ width:100%; border-collapse:separate; border-spacing:0 8px; }}
            .dash-table th {{
                padding:0 12px 6px;
                text-align:left;
                color:#84978F;
                font-size:10px;
                font-weight:850;
                letter-spacing:1px;
                text-transform:uppercase;
            }}
            .dash-table td {{
                padding:12px;
                background:#F7FBF9;
                border-top:1px solid #E3EEE8;
                border-bottom:1px solid #E3EEE8;
                color:#355349;
                font-size:12px;
                font-weight:650;
            }}
            .dash-table td:first-child {{ border-left:1px solid #E3EEE8; border-radius:11px 0 0 11px; }}
            .dash-table td:last-child {{ border-right:1px solid #E3EEE8; border-radius:0 11px 11px 0; }}
            .dash-action {{
                display:inline-flex;
                align-items:center;
                justify-content:center;
                margin-top:8px;
                padding:9px 13px;
                border-radius:10px;
                text-decoration:none;
                background:#EFFAF4;
                border:1px solid #BFE6D1;
                color:#168553;
                font-size:11px;
                font-weight:850;
            }}
            .dash-insight {{
                display:flex;
                align-items:center;
                justify-content:space-between;
                gap:20px;
                background:linear-gradient(100deg,#F1FBF6,#FFF5FA);
                border:1px solid #FFFFFF;
                border-radius:20px;
                padding:22px 24px;
                box-shadow:0 10px 26px rgba(23,53,43,.065);
            }}
            .dash-insight-title {{ color:#17352B; font-size:17px; font-weight:850; }}
            .dash-insight-text {{ margin-top:5px; color:#71877D; font-size:12px; font-weight:600; }}
            .dash-insight-action {{
                flex:none;
                padding:11px 16px;
                border-radius:999px;
                background:#F9D8E9;
                border:1px solid #F2BDD7;
                color:#A83269;
                text-decoration:none;
                font-size:11px;
                font-weight:850;
            }}
            @media (max-width:1050px) {{
                .dashboard-metrics {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
                .dashboard-grid {{ grid-template-columns:1fr; }}
            }}
            @media (max-width:720px) {{
                .dashboard-page {{ padding:22px 14px 30px; }}
                .dashboard-metrics,.dashboard-lists {{ grid-template-columns:1fr; }}
                .dashboard-hero h1 {{ font-size:34px; }}
                .health-summary {{ flex-direction:column; padding:12px 0 18px; }}
                .dash-insight {{ align-items:flex-start; flex-direction:column; }}
            }}
        </style>
    </head>
    <body class="dashboard-body">
        {sidebar("dashboard")}
        <div class="main-content">
            <div class="dashboard-page">
                <div class="dashboard-hero">
                    <h1>Dashboard</h1>
                    <p>Overview of your EV charging network</p>
                </div>

                <div class="dashboard-metrics">
                    <div class="dash-metric"><div class="dash-metric-label">Charging Stations</div><div class="dash-metric-value">{stations}</div><div class="dash-metric-note">Registered across the network</div></div>
                    <div class="dash-metric pink"><div class="dash-metric-label">Telemetry Records</div><div class="dash-metric-value">{telemetry_count}</div><div class="dash-metric-note">Sensor readings available</div></div>
                    <div class="dash-metric orange"><div class="dash-metric-label">Active Alerts</div><div class="dash-metric-value">{alerts_count}</div><div class="dash-metric-note">Require attention</div></div>
                    <div class="dash-metric pink"><div class="dash-metric-label">Charging Sessions</div><div class="dash-metric-value">{len(recent_sessions)}</div><div class="dash-metric-note">Latest records displayed below</div></div>
                    <div class="dash-metric"><div class="dash-metric-label">Battery Health</div><div class="dash-metric-value">{battery}%</div><div class="dash-metric-note">Calculated from latest telemetry</div></div>
                    <div class="dash-metric pink"><div class="dash-metric-label">Predictions</div><div class="dash-metric-value">{len(prediction_records)}</div><div class="dash-metric-note">Model records available</div></div>
                    <div class="dash-metric orange"><div class="dash-metric-label">Maintenance Records</div><div class="dash-metric-value">{maintenance_count}</div><div class="dash-metric-note">Scheduled and completed work</div></div>
                    <div class="dash-metric"><div class="dash-metric-label">Failure Records</div><div class="dash-metric-value">{len(recent_failures)}</div><div class="dash-metric-note">Latest records displayed below</div></div>
                </div>

                <div class="dashboard-grid">
                    <div class="dash-panel">
                        <div class="dash-panel-head">
                            <div><h2 class="dash-panel-title">Telemetry Trend</h2><div class="dash-panel-subtitle">Recent temperature readings from the monitoring system</div></div>
                            <span class="dash-pill">LIVE DATA</span>
                        </div>
                        <svg class="dash-chart" viewBox="0 0 520 270" preserveAspectRatio="none">
                            <defs>
                                <linearGradient id="dashTelemetryFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#16A36A" stop-opacity=".20"/><stop offset="100%" stop-color="#16A36A" stop-opacity="0"/></linearGradient>
                            </defs>
                            <line x1="35" y1="235" x2="495" y2="235" stroke="#DDE9E3" />
                            <line x1="35" y1="35" x2="35" y2="235" stroke="#DDE9E3" />
                            <line x1="35" y1="85" x2="495" y2="85" stroke="#EAF1ED" />
                            <line x1="35" y1="135" x2="495" y2="135" stroke="#EAF1ED" />
                            <line x1="35" y1="185" x2="495" y2="185" stroke="#EAF1ED" />
                            <polyline points="35,235 35,235 {graph_points} 495,235" fill="url(#dashTelemetryFill)" stroke="none" />
                            <polyline points="{graph_points}" fill="none" stroke="#16A36A" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
                        </svg>
                    </div>

                    <div class="dash-panel">
                        <div class="dash-panel-head">
                            <div><h2 class="dash-panel-title">Station Health Status</h2><div class="dash-panel-subtitle">Current battery condition summary</div></div>
                            <span class="dash-pill">MONITORED</span>
                        </div>
                        <div class="health-summary">
                            <div class="dash-ring">
                                <div class="dash-ring-center"><div class="dash-ring-value">{battery}%</div><div class="dash-ring-label">Healthy</div></div>
                            </div>
                            <div class="health-legend">
                                <div class="health-legend-row"><span class="health-legend-name"><span class="legend-dot"></span>Healthy</span><strong>{healthy_predictions}</strong></div>
                                <div class="health-legend-row"><span class="health-legend-name"><span class="legend-dot pink"></span>Warning</span><strong>{warning_predictions}</strong></div>
                                <div class="health-legend-row"><span class="health-legend-name"><span class="legend-dot orange"></span>Critical</span><strong>{critical_predictions}</strong></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="dashboard-lists">
                    <div class="dash-panel">
                        <div class="dash-panel-head">
                            <div><h2 class="dash-panel-title">Recent Alerts</h2><div class="dash-panel-subtitle">Latest issues detected by the system</div></div>
                        </div>
                        <table class="dash-table"><tr><th>Alert Details</th></tr>{alerts_html}</table>
                        <a href="/alerts" class="dash-action">View All Alerts</a>
                    </div>
                    <div class="dash-panel">
                        <div class="dash-panel-head">
                            <div><h2 class="dash-panel-title">Recent Failures</h2><div class="dash-panel-subtitle">Latest failure history records</div></div>
                        </div>
                        <table class="dash-table"><tr><th>Failure Details</th></tr>{failures_html}</table>
                        <a href="/failure-history" class="dash-action">View Failure History</a>
                    </div>
                </div>

                <div class="dash-panel" style="margin-bottom:18px;">
                    <div class="dash-panel-head">
                        <div><h2 class="dash-panel-title">Recent Charging Sessions</h2><div class="dash-panel-subtitle">Latest charging activity from backend records</div></div>
                        <a href="/charging-sessions" class="dash-action" style="margin-top:0;">View All Sessions</a>
                    </div>
                    <table class="dash-table">{sessions_html}</table>
                </div>

                <div class="dash-insight">
                    <div>
                        <div class="dash-insight-title">System Insights</div>
                        <div class="dash-insight-text">Battery health is currently {battery}%. Use Telemetry, Predictions and Maintenance to investigate changes across the network.</div>
                    </div>
                    <a href="/battery-health" class="dash-insight-action">View Battery Analysis</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


# =========================================================
# MAIN DATABASE PAGES
# =========================================================


@app.route("/stations")
def stations():

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    try:
        stations_data = conn.execute(
            """
            SELECT id, station_name, charger_type, location
            FROM charging_stations
            ORDER BY id ASC
        """
        ).fetchall()

        total_stations = len(stations_data)

        charger_types = {}
        for station in stations_data:
            charger = station["charger_type"] or "Unknown"
            charger_types[charger] = charger_types.get(charger, 0) + 1

        locations_count = len(
            set((station["location"] or "Unknown").strip() for station in stations_data)
        )

    except sqlite3.Error:
        stations_data = []
        total_stations = 0
        charger_types = {}
        locations_count = 0

    conn.close()

    station_cards = ""

    for station in stations_data:

        station_id = station["id"]
        station_name = station["station_name"] or f"Charging Station #{station_id}"
        charger_type = station["charger_type"] or "Charger"
        location = station["location"] or "Location unavailable"

        charger_lower = charger_type.lower()

        if "dc" in charger_lower or "fast" in charger_lower:
            charger_class = "fast"
            charger_icon = ""
            charger_label = "FAST CHARGING"
        elif "ac" in charger_lower:
            charger_class = "ac"
            charger_icon = ""
            charger_label = "AC CHARGING"
        else:
            charger_class = "standard"
            charger_icon = "️"
            charger_label = "CHARGING POINT"

        station_cards += f"""
        <div class="station-card">

            <div class="station-card-head">

                <div class="station-number">
                    #{station_id}
                </div>

                <div class="station-status">
                    <span></span>
                    REGISTERED
                </div>

            </div>

            <div class="station-card-icon {charger_class}"></div>

            <div class="station-card-title">
                {station_name}
            </div>

            <div class="station-card-location">
                {location}
            </div>

            <div class="station-card-divider"></div>

            <div class="station-card-info">

                <div>
                    <span class="station-info-label">CHARGER TYPE</span>
                    <strong>{charger_type}</strong>
                </div>

                <div class="charger-tag {charger_class}">
                    {charger_label}
                </div>

            </div>

        </div>
        """

    if not station_cards:
        station_cards = """
        <div class="stations-empty">
            <div class="stations-empty-icon"></div>
            <h3>No Charging Stations</h3>
            <p>No registered charging stations were found in the database.</p>
        </div>
        """

    type_summary = ""

    for charger, count in sorted(charger_types.items(), key=lambda x: x[0]):
        type_summary += f"""
        <div class="type-summary-row">
            <span>{charger}</span>
            <strong>{count}</strong>
        </div>
        """

    if not type_summary:
        type_summary = """
        <div class="type-summary-row">
            <span>No charger data</span>
            <strong>0</strong>
        </div>
        """

    stations_css = r"""
    <style>

        .stations-page-head {
            display:flex;
            justify-content:space-between;
            align-items:flex-end;
            gap:20px;
            margin-bottom:24px;
        }

        .stations-eyebrow {
            color:#E879F9;
            font-size:11px;
            font-weight:900;
            letter-spacing:1.8px;
            margin-bottom:7px;
        }

        .stations-page-head h1 {
            margin:0 0 6px;
            font-size:32px;
        }

        .stations-page-head p {
            margin:0;
            color:#8FA39D;
            font-size:14px;
        }

        .network-status {
            display:flex;
            align-items:center;
            gap:8px;
            padding:9px 13px;
            border-radius:999px;
            color:#8CE9C6;
            background:rgba(75,216,166,.07);
            border:1px solid rgba(75,216,166,.23);
            font-size:10px;
            font-weight:900;
            letter-spacing:1px;
            white-space:nowrap;
        }

        .network-status i {
            width:7px;
            height:7px;
            border-radius:50%;
            background:#4BD8A6;
            box-shadow:0 0 10px rgba(75,216,166,.8);
        }

        .stations-metrics {
            display:grid;
            grid-template-columns:repeat(3,minmax(0,1fr));
            gap:15px;
            margin-bottom:21px;
        }

        .station-metric {
            position:relative;
            overflow:hidden;
            min-height:112px;
            padding:19px;
            border-radius:17px;
            background:linear-gradient(145deg,#0E211E,#0A1716);
            border:1px solid rgba(255,255,255,.07);
        }

        .station-metric:after {
            content:"";
            position:absolute;
            width:80px;
            height:80px;
            right:-32px;
            top:-32px;
            border-radius:50%;
            background:rgba(232,121,249,.07);
        }

        .station-metric-label {
            color:#81958E;
            font-size:10px;
            font-weight:800;
            letter-spacing:.9px;
            text-transform:uppercase;
        }

        .station-metric-value {
            margin-top:9px;
            color:#F0FDF4;
            font-size:29px;
            font-weight:900;
        }

        .station-metric-value.pink {
            color:#F0ABFC;
        }

        .station-metric-value.green {
            color:#4BD8A6;
        }

        .stations-layout {
            display:grid;
            grid-template-columns:minmax(0,1fr) 280px;
            gap:18px;
            align-items:start;
        }

        .stations-panel {
            min-width:0;
            padding:21px;
            border-radius:20px;
            background:linear-gradient(145deg,#0D201D,#091513);
            border:1px solid rgba(255,255,255,.07);
        }

        .stations-panel-head {
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            gap:15px;
            margin-bottom:18px;
        }

        .stations-kicker {
            color:#E879F9;
            font-size:10px;
            font-weight:900;
            letter-spacing:1.5px;
            margin-bottom:5px;
        }

        .stations-panel h2 {
            margin:0;
            font-size:20px;
            color:#EDF7F3;
        }

        .stations-panel-subtitle {
            margin-top:5px;
            color:#80938D;
            font-size:12px;
        }

        .station-count-pill {
            color:#F0ABFC;
            background:rgba(232,121,249,.07);
            border:1px solid rgba(232,121,249,.18);
            border-radius:999px;
            padding:7px 10px;
            font-size:9px;
            font-weight:900;
            letter-spacing:.7px;
            white-space:nowrap;
        }

        .stations-grid {
            display:grid;
            grid-template-columns:repeat(2,minmax(0,1fr));
            gap:13px;
        }

        .station-card {
            position:relative;
            overflow:hidden;
            padding:18px;
            border-radius:16px;
            background:rgba(255,255,255,.025);
            border:1px solid rgba(255,255,255,.065);
            transition:transform .2s ease,border-color .2s ease;
        }

        .station-card:hover {
            transform:translateY(-2px);
            border-color:rgba(232,121,249,.28);
        }

        .station-card-head {
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:10px;
        }

        .station-number {
            color:#697D76;
            font-size:10px;
            font-weight:900;
            letter-spacing:.8px;
        }

        .station-status {
            display:flex;
            align-items:center;
            gap:5px;
            padding:5px 7px;
            border-radius:999px;
            color:#73E2B7;
            background:rgba(75,216,166,.07);
            font-size:8px;
            font-weight:900;
            letter-spacing:.6px;
        }

        .station-status span {
            width:5px;
            height:5px;
            border-radius:50%;
            background:#4BD8A6;
        }

        .station-card-icon {
            width:46px;
            height:46px;
            display:grid;
            place-items:center;
            margin:18px 0 12px;
            border-radius:13px;
            font-size:20px;
        }

        .station-card-icon.fast {
            color:#F0ABFC;
            background:rgba(232,121,249,.10);
            border:1px solid rgba(232,121,249,.18);
        }

        .station-card-icon.ac {
            color:#8FD7FF;
            background:rgba(56,189,248,.08);
            border:1px solid rgba(56,189,248,.16);
        }

        .station-card-icon.standard {
            color:#73E2B7;
            background:rgba(75,216,166,.08);
            border:1px solid rgba(75,216,166,.16);
        }

        .station-card-title {
            color:#E4EFEB;
            font-size:16px;
            font-weight:850;
            line-height:1.3;
            min-height:21px;
        }

        .station-card-location {
            display:flex;
            align-items:flex-start;
            gap:6px;
            margin-top:7px;
            color:#849790;
            font-size:11px;
            line-height:1.45;
        }

        .station-card-location span {
            color:#E879F9;
            flex-shrink:0;
        }

        .station-card-divider {
            height:1px;
            margin:15px 0;
            background:rgba(255,255,255,.06);
        }

        .station-card-info {
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:10px;
        }

        .station-info-label {
            display:block;
            color:#61746E;
            font-size:8px;
            font-weight:900;
            letter-spacing:1px;
            margin-bottom:4px;
        }

        .station-card-info strong {
            color:#C7D7D2;
            font-size:11px;
        }

        .charger-tag {
            padding:5px 7px;
            border-radius:7px;
            font-size:7px;
            font-weight:900;
            letter-spacing:.5px;
            white-space:nowrap;
        }

        .charger-tag.fast {
            color:#F0ABFC;
            background:rgba(232,121,249,.07);
        }

        .charger-tag.ac {
            color:#8FD7FF;
            background:rgba(56,189,248,.07);
        }

        .charger-tag.standard {
            color:#73E2B7;
            background:rgba(75,216,166,.07);
        }

        .type-panel {
            position:sticky;
            top:20px;
        }

        .type-summary {
            display:grid;
            gap:8px;
            margin-top:17px;
        }

        .type-summary-row {
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:10px;
            padding:12px;
            border-radius:10px;
            background:rgba(255,255,255,.025);
            border:1px solid rgba(255,255,255,.045);
        }

        .type-summary-row span {
            color:#91A49E;
            font-size:10px;
            overflow:hidden;
            text-overflow:ellipsis;
            white-space:nowrap;
        }

        .type-summary-row strong {
            color:#F0ABFC;
            font-size:12px;
        }

        .station-tip {
            margin-top:15px;
            padding:14px;
            border-radius:12px;
            background:rgba(232,121,249,.045);
            border:1px solid rgba(232,121,249,.10);
        }

        .station-tip-title {
            color:#F0ABFC;
            font-size:9px;
            font-weight:900;
            letter-spacing:.8px;
            margin-bottom:6px;
        }

        .station-tip p {
            margin:0;
            color:#81958E;
            font-size:10px;
            line-height:1.5;
        }

        .stations-empty {
            grid-column:1/-1;
            text-align:center;
            padding:55px 20px;
            color:#71857E;
        }

        .stations-empty-icon {
            width:58px;
            height:58px;
            display:grid;
            place-items:center;
            margin:0 auto 14px;
            border-radius:50%;
            color:#F0ABFC;
            background:rgba(232,121,249,.07);
            border:1px solid rgba(232,121,249,.16);
            font-size:25px;
        }

        .stations-empty h3 {
            margin:0 0 6px;
            color:#DCE9E5;
        }

        .stations-empty p {
            margin:0;
            font-size:12px;
        }

        @media(max-width:950px) {
            .stations-layout {
                grid-template-columns:1fr;
            }

            .type-panel {
                position:static;
            }
        }

        @media(max-width:700px) {
            .stations-metrics {
                grid-template-columns:1fr;
            }

            .stations-grid {
                grid-template-columns:1fr;
            }

            .stations-page-head {
                align-items:flex-start;
                flex-direction:column;
            }
        }

        /* Clean light theme for Charging Stations */
        .stations-page-head {
            display:block;
            text-align:center;
            margin-bottom:28px;
        }
        .stations-page-head h1 {
            color:#123C30;
            font-size:38px;
            font-weight:900;
            letter-spacing:-.9px;
            text-shadow:0 2px 10px rgba(22,163,106,.12);
            position:relative;
            display:inline-block;
            padding-bottom:12px;
        }
        .stations-page-head h1:after {
            content:"";
            position:absolute;
            left:50%;
            bottom:0;
            width:78px;
            height:4px;
            border-radius:99px;
            transform:translateX(-50%);
            background:linear-gradient(90deg,#16A36A,#E85B8A);
        }
        .station-metric {
            background:#FFFFFF;
            border:2px solid #FFFFFF;
            box-shadow:0 10px 28px rgba(23,53,43,.08);
        }
        .station-metric-label { color:#71877D; }
        .station-metric-value { color:#17352B; }
        .station-metric-value.pink { color:#D94D78; }
        .station-metric-value.green { color:#168553; }
        .stations-panel {
            background:#FFFFFF;
            border:2px solid #FFFFFF;
            box-shadow:0 10px 28px rgba(23,53,43,.08);
        }
        .stations-panel h2 { color:#17352B; }
        .station-card {
            background:#F8FCFA;
            border:1px solid #E2ECE7;
        }
        .station-card:hover { border-color:#BFE6D1; }
        .station-number { color:#71877D; }
        .station-status { color:#168553; background:#EFFAF4; }
        .station-status span { background:#16A36A; }
        .station-card-icon {
            position:relative;
            width:46px; height:46px;
        }
        .station-card-icon:after {
            content:"";
            width:13px; height:13px;
            border-radius:4px;
            border:3px solid currentColor;
            display:block;
        }
        .station-card-icon.fast { color:#D94D78; background:#FFF1F5; border-color:#F4C5D3; }
        .station-card-icon.ac { color:#168553; background:#EFFAF4; border-color:#BFE6D1; }
        .station-card-icon.standard { color:#168553; background:#F2FAF6; border-color:#CBE9D9; }
        .station-card-title { color:#17352B; }
        .station-card-location { color:#71877D; }
        .station-card-divider { background:#E4ECE8; }
        .station-info-label { color:#84978F; }
        .station-card-info strong { color:#355349; }
        .charger-tag.fast { color:#C43B64; background:#FFF1F5; }
        .charger-tag.ac, .charger-tag.standard { color:#168553; background:#EFFAF4; }
        .type-summary-row { background:#F8FCFA; border-color:#E2ECE7; }
        .type-summary-row span { color:#71877D; }
        .type-summary-row strong { color:#D94D78; }
        .station-tip { background:#FFF5F8; border-color:#F2CBD8; }
        .station-tip-title { color:#C43B64; }
        .station-tip p { color:#71877D; }
        .stations-empty { color:#71877D; }
        .stations-empty h3 { color:#17352B; }

    </style>
    """

    return f"""
    <!DOCTYPE html>
    <html>

    <head>
        <title>Charging Stations | EV Charging Station Health Care</title>
        {STYLE}
        {stations_css}
    </head>

    <body class="dashboard-body">

        {sidebar("stations")}

        <div class="main-content">

            <div class="stations-page-head">

                <div>

                    <h1>
                        Charging Stations
                    </h1>
                </div>

            </div>

            <div class="stations-metrics">

                <div class="station-metric">
                    <div class="station-metric-label">
                        Registered Stations
                    </div>
                    <div class="station-metric-value pink">
                        {total_stations}
                    </div>
                </div>

                <div class="station-metric">
                    <div class="station-metric-label">
                        Locations
                    </div>
                    <div class="station-metric-value">
                        {locations_count}
                    </div>
                </div>

                <div class="station-metric">
                    <div class="station-metric-label">
                        Charger Types
                    </div>
                    <div class="station-metric-value green">
                        {len(charger_types)}
                    </div>
                </div>

            </div>

            <div class="stations-layout">

                <div class="stations-panel">

                    <div class="stations-panel-head">

                        <div>
                            <h2>
                                Registered Charging Stations
                            </h2>

                        </div>

                        <div class="station-count-pill">
                            {total_stations} STATIONS
                        </div>

                    </div>

                    <div class="stations-grid">
                        {station_cards}
                    </div>

                </div>

                <div class="stations-panel type-panel">

                    <h2>
                        Charger Types
                    </h2>

                    <div class="type-summary">
                        {type_summary}
                    </div>

                    <div class="station-tip">

                        <div class="station-tip-title">
                            STATION HEALTH CARE
                        </div>

                        <p>
                            Use Telemetry and Battery Health to investigate
                            temperature, power and battery-condition changes
                            for individual charging infrastructure.
                        </p>

                    </div>

                </div>

            </div>

        </div>

    </body>

    </html>
    """


@app.route("/alerts")
def alerts():

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    try:
        records = conn.execute("SELECT * FROM alerts ORDER BY id DESC").fetchall()
    except sqlite3.Error:
        records = []

    conn.close()

    critical = 0
    warning = 0
    resolved = 0
    cards = []

    for record in records:
        keys = record.keys()

        def rv(*names, default="-"):
            for name in names:
                if name in keys and record[name] not in (None, ""):
                    return record[name]
            return default

        severity = str(rv("severity", "level", default="Warning"))
        status = str(rv("status", default="Active"))
        station = rv("station_id", "station", "charger_id", default="Station")
        message = rv(
            "message",
            "description",
            "alert_type",
            "type",
            default="Sensor anomaly detected",
        )
        value = rv("value", "sensor_value", "reading", default="-")
        timestamp = rv("timestamp", "created_at", "detected_at", "time", default="-")

        sev = severity.lower()
        stat = status.lower()

        if stat in ("resolved", "closed", "fixed"):
            resolved += 1

        if "critical" in sev or "high" in sev:
            critical += 1
            icon = ""
            severity_class = "critical"
            severity_label = "CRITICAL"
        else:
            warning += 1
            icon = ""
            severity_class = "warning"
            severity_label = "WARNING"

        status_class = (
            "resolved" if stat in ("resolved", "closed", "fixed") else "active"
        )

        cards.append(
            f"""
        <div class="alert-card {severity_class}">
            <div class="alert-left">
                <div class="alert-icon">{icon}</div>
                <div class="alert-info">
                    <div class="alert-tags">
                        <span class="severity {severity_class}">{severity_label}</span>
                        <span class="alert-status {status_class}">{status}</span>
                    </div>
                    <div class="alert-message">{message}</div>
                    <div class="alert-meta">
                        <span> {station}</span>
                        <span>◷ {timestamp}</span>
                        <span>◉ Reading: <b>{value}</b></span>
                    </div>
                </div>
            </div>
            <button class="view-alert">VIEW</button>
        </div>
        """
        )

    if not cards:
        cards.append(
            """
        <div class="empty-alerts">
            <div class="empty-icon"></div>
            <h3>No active alerts</h3>
            <p>Your charging network is currently looking good.</p>
        </div>
        """
        )

    alert_css = """
    <style>
        .alert-page-head{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;margin-bottom:24px}
        .alert-eyebrow,.panel-kicker{color:#ff4f9a;font-size:11px;font-weight:800;letter-spacing:1.8px;margin-bottom:7px}
        .alert-page-head h1{margin:0 0 6px;font-size:32px}
        .alert-page-head p{margin:0;color:#8fa39d}
        .monitor-pill{color:#8ce9c6;background:rgba(75,216,166,.07);border:1px solid rgba(75,216,166,.25);border-radius:999px;padding:9px 13px;font-size:10px;font-weight:900;letter-spacing:1px;white-space:nowrap}
        .monitor-pill i{display:inline-block;width:7px;height:7px;border-radius:50%;background:#4bd8a6;margin-right:7px;box-shadow:0 0 10px rgba(75,216,166,.7)}
        .alert-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-bottom:20px}
        .alert-stat{display:flex;align-items:center;gap:14px;padding:20px;border-radius:18px;background:linear-gradient(145deg,#0e211e,#0a1716);border:1px solid rgba(255,255,255,.07)}
        .alert-stat-icon{font-size:25px}.alert-stat strong{display:block;font-size:28px;line-height:1;color:#edf7f3}.alert-stat span{display:block;margin-top:5px;color:#81958e;font-size:12px}
        .alert-stat.critical-box{border-color:rgba(255,83,105,.22)}.alert-stat.warning-box{border-color:rgba(255,190,76,.20)}.alert-stat.resolved-box{border-color:rgba(75,216,166,.20)}
        .alerts-panel{background:linear-gradient(145deg,#0d201d,#091513);border:1px solid rgba(255,255,255,.07);border-radius:20px;padding:22px}
        .alerts-panel-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}.alerts-panel-head h2{margin:0;font-size:20px}
        .record-count{color:#91a7a1;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.07);border-radius:999px;padding:7px 10px;font-size:10px}
        .alert-list{display:grid;gap:12px}.alert-card{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:17px;border-radius:15px;background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.06)}
        .alert-card.critical{border-left:3px solid #ff5369}.alert-card.warning{border-left:3px solid #ffbe4c}
        .alert-left{display:flex;align-items:flex-start;gap:13px;min-width:0}.alert-icon{font-size:20px;margin-top:2px}.alert-info{min-width:0}
        .alert-tags{display:flex;align-items:center;gap:8px;margin-bottom:7px}.severity,.alert-status{font-size:9px;font-weight:900;letter-spacing:1px;border-radius:999px;padding:4px 7px}
        .severity.critical{color:#ff8392;background:rgba(255,83,105,.10)}.severity.warning{color:#ffd27a;background:rgba(255,190,76,.10)}
        .alert-status.active{color:#ff8392;background:rgba(255,83,105,.08)}.alert-status.resolved{color:#73e2b7;background:rgba(75,216,166,.08)}
        .alert-message{color:#e8f2ee;font-size:15px;font-weight:700;margin-bottom:8px}.alert-meta{display:flex;flex-wrap:wrap;gap:13px;color:#70847d;font-size:11px}.alert-meta b{color:#b9c9c5}
        .view-alert{flex:0 0 auto;border:1px solid rgba(255,79,154,.28);background:rgba(255,79,154,.06);color:#ff75ad;border-radius:9px;padding:8px 12px;font-size:10px;font-weight:900;letter-spacing:1px;cursor:pointer}
        .view-alert:hover{background:rgba(255,79,154,.15);border-color:rgba(255,79,154,.5)}
        .empty-alerts{text-align:center;padding:55px 20px;color:#81958e}.empty-icon{width:55px;height:55px;margin:0 auto 14px;display:grid;place-items:center;border-radius:50%;background:rgba(75,216,166,.08);border:1px solid rgba(75,216,166,.18);color:#4bd8a6;font-size:25px}
        .empty-alerts h3{color:#dce9e5;margin:0 0 5px}.empty-alerts p{margin:0;font-size:13px}
        @media(max-width:800px){.alert-stats{grid-template-columns:1fr}.alert-page-head{align-items:flex-start;flex-direction:column}.alert-card{align-items:flex-start;flex-direction:column}.view-alert{width:100%}}
    </style>
    """

    cards_html = "".join(cards)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Alert Center</title>
        {STYLE}
        {alert_css}
    </head>
    <body class="dashboard-body">
        {sidebar("alerts")}
        <div class="main-content">
            {topbar("Alert Center", "Monitor warnings and abnormal charging-station conditions.")}

            <div class="alert-page-head">
                <div>
                    <h1>Alert Center</h1>
                </div>
            </div>

            <div class="alert-stats">
                <div class="alert-stat critical-box"><div class="alert-stat-icon"></div><div><strong>{critical}</strong><span>Critical</span></div></div>
                <div class="alert-stat warning-box"><div class="alert-stat-icon"></div><div><strong>{warning}</strong><span>Warnings</span></div></div>
                <div class="alert-stat resolved-box"><div class="alert-stat-icon"></div><div><strong>{resolved}</strong><span>Resolved</span></div></div>
            </div>

            <div class="alerts-panel">
                <div class="alerts-panel-head">
                    <div><div class="panel-kicker">LIVE FEED</div><h2>Recent Alerts</h2></div>
                    <div class="record-count">{len(records)} records</div>
                </div>
                <div class="alert-list">{cards_html}</div>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/telemetry")
def telemetry():

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    try:
        total_records = conn.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]

        data = conn.execute(
            """
            SELECT
                t.id,
                t.charging_station_id,
                t.temperature,
                t.humidity,
                t.power_consumption,
                c.station_name,
                c.location,
                c.charger_type
            FROM telemetry t
            LEFT JOIN charging_stations c
                ON t.charging_station_id = c.id
            ORDER BY t.id DESC
            LIMIT 20
        """
        ).fetchall()

    except sqlite3.Error:
        total_records = 0
        data = []

    conn.close()

    latest = data[0] if data else None

    latest_temp = float(latest["temperature"] or 0) if latest else 0
    latest_humidity = float(latest["humidity"] or 0) if latest else 0
    latest_power = float(latest["power_consumption"] or 0) if latest else 0

    health = calculate_health(latest_temp, latest_power) if latest else 0

    if health >= 80:
        health_status = "HEALTHY"
        health_class = "good"
    elif health >= 60:
        health_status = "MODERATE"
        health_class = "warning"
    else:
        health_status = "CRITICAL"
        health_class = "danger"

    temps = []
    powers = []

    for item in reversed(data):
        temps.append(float(item["temperature"] or 0))
        powers.append(float(item["power_consumption"] or 0))

    if temps:
        min_temp = min(temps)
        max_temp = max(temps)
        avg_power = sum(powers) / len(powers)
    else:
        min_temp = max_temp = avg_power = 0

    # Build a clean temperature trend SVG from the real telemetry data.
    graph_points = ""

    if temps:
        graph = []
        min_y = min(temps)
        max_y = max(temps)
        spread = max(max_y - min_y, 1)

        for i, value in enumerate(temps):
            x = 30 + (i * 380 / max(1, len(temps) - 1))
            y = 205 - ((value - min_y) / spread) * 160
            graph.append(f"{x:.1f},{y:.1f}")

        graph_points = " ".join(graph)

    telemetry_rows = ""

    for item in data:

        station_name = (
            item["station_name"]
            if item["station_name"]
            else f"Station #{item['charging_station_id']}"
        )

        location = item["location"] or "—"
        charger_type = item["charger_type"] or "—"

        temperature = float(item["temperature"] or 0)
        humidity = float(item["humidity"] or 0)
        power = float(item["power_consumption"] or 0)

        row_health = calculate_health(temperature, power)

        if row_health >= 80:
            row_status = "Healthy"
            row_class = "good"
        elif row_health >= 60:
            row_status = "Moderate"
            row_class = "warning"
        else:
            row_status = "Critical"
            row_class = "danger"

        telemetry_rows += f"""
        <tr>
            <td><span class="telemetry-id">#{item["id"]}</span></td>
            <td>
                <div class="station-cell">
                    <strong>{station_name}</strong>
                    <span>{location}</span>
                </div>
            </td>
            <td><span class="reading temp">{temperature:.2f}°C</span></td>
            <td><span class="reading humidity">{humidity:.2f}%</span></td>
            <td><span class="reading power">{power:.2f} kW</span></td>
            <td>
                <span class="telemetry-status {row_class}">
                    <i></i>{row_status}
                </span>
            </td>
        </tr>
        """

    if not telemetry_rows:
        telemetry_rows = """
        <tr>
            <td colspan="6">
                <div class="telemetry-empty">
                    No telemetry records available.
                </div>
            </td>
        </tr>
        """

    telemetry_css = r"""
    <style>

        .telemetry-page-head {
            display:flex;
            justify-content:space-between;
            align-items:flex-end;
            gap:20px;
            margin-bottom:24px;
        }

        .telemetry-eyebrow {
            color:#E879F9;
            font-size:11px;
            font-weight:900;
            letter-spacing:1.8px;
            margin-bottom:7px;
        }

        .telemetry-page-head h1 {
            margin:0 0 6px;
            font-size:32px;
        }

        .telemetry-page-head p {
            margin:0;
            color:#8FA39D;
            font-size:14px;
        }

        .telemetry-live {
            display:flex;
            align-items:center;
            gap:8px;
            color:#8CE9C6;
            background:rgba(75,216,166,.07);
            border:1px solid rgba(75,216,166,.25);
            border-radius:999px;
            padding:9px 13px;
            font-size:10px;
            font-weight:900;
            letter-spacing:1px;
            white-space:nowrap;
        }

        .telemetry-live i {
            width:7px;
            height:7px;
            border-radius:50%;
            background:#4BD8A6;
            box-shadow:0 0 10px rgba(75,216,166,.8);
        }

        .telemetry-stats {
            display:grid;
            grid-template-columns:repeat(4,minmax(0,1fr));
            gap:15px;
            margin-bottom:20px;
        }

        .telemetry-stat {
            position:relative;
            overflow:hidden;
            min-height:112px;
            padding:18px;
            border-radius:17px;
            background:linear-gradient(145deg,#0E211E,#0A1716);
            border:1px solid rgba(255,255,255,.07);
        }

        .telemetry-stat:after {
            content:"";
            position:absolute;
            width:72px;
            height:72px;
            right:-28px;
            top:-28px;
            border-radius:50%;
            background:rgba(232,121,249,.08);
        }

        .telemetry-stat-label {
            color:#81958E;
            font-size:10px;
            font-weight:800;
            letter-spacing:.9px;
            text-transform:uppercase;
        }

        .telemetry-stat-value {
            margin-top:9px;
            color:#F0FDF4;
            font-size:27px;
            font-weight:850;
        }

        .telemetry-stat-value.pink {
            color:#F0ABFC;
        }

        .telemetry-stat-value.green {
            color:#4BD8A6;
        }

        .telemetry-stat-value.orange {
            color:#FFC978;
        }

        .telemetry-main-grid {
            display:grid;
            grid-template-columns:minmax(0,1.7fr) minmax(280px,.8fr);
            gap:18px;
            margin-bottom:20px;
        }

        .telemetry-panel {
            background:linear-gradient(145deg,#0D201D,#091513);
            border:1px solid rgba(255,255,255,.07);
            border-radius:20px;
            padding:22px;
            min-width:0;
        }

        .telemetry-panel-head {
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            gap:15px;
            margin-bottom:15px;
        }

        .telemetry-kicker {
            color:#E879F9;
            font-size:10px;
            font-weight:900;
            letter-spacing:1.5px;
            margin-bottom:5px;
        }

        .telemetry-panel h2 {
            margin:0;
            font-size:20px;
            color:#EDF7F3;
        }

        .telemetry-panel-subtitle {
            margin-top:5px;
            color:#80938D;
            font-size:12px;
        }

        .telemetry-chart {
            width:100%;
            height:245px;
            display:block;
            margin-top:8px;
        }

        .chart-line {
            fill:none;
            stroke:#E879F9;
            stroke-width:4;
            stroke-linecap:round;
            stroke-linejoin:round;
        }

        .chart-grid {
            stroke:#1A3328;
            stroke-width:1;
        }

        .chart-label {
            fill:#63766F;
            font-size:9px;
        }

        .health-summary {
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
            min-height:300px;
        }

        .health-ring {
            width:158px;
            height:158px;
            border-radius:50%;
            display:grid;
            place-items:center;
            position:relative;
            background:
                conic-gradient(
                    #E879F9 {health}%,
                    rgba(255,255,255,.06) {health}% 100%
                );
            box-shadow:0 0 35px rgba(232,121,249,.08);
        }

        .health-ring:before {
            content:"";
            position:absolute;
            inset:10px;
            border-radius:50%;
            background:#0A1716;
        }

        .health-ring-content {
            position:relative;
            text-align:center;
        }

        .health-number {
            color:#F0FDF4;
            font-size:32px;
            font-weight:900;
        }

        .health-label {
            color:#81958E;
            font-size:9px;
            font-weight:900;
            letter-spacing:1.2px;
        }

        .health-badge {
            margin-top:17px;
            border-radius:999px;
            padding:7px 11px;
            font-size:9px;
            font-weight:900;
            letter-spacing:1px;
        }

        .health-badge.good {
            color:#73E2B7;
            background:rgba(75,216,166,.09);
            border:1px solid rgba(75,216,166,.18);
        }

        .health-badge.warning {
            color:#FFD27A;
            background:rgba(245,158,11,.09);
            border:1px solid rgba(245,158,11,.18);
        }

        .health-badge.danger {
            color:#FF8392;
            background:rgba(244,63,94,.09);
            border:1px solid rgba(244,63,94,.18);
        }

        .health-details {
            width:100%;
            margin-top:20px;
            display:grid;
            gap:9px;
        }

        .health-detail {
            display:flex;
            justify-content:space-between;
            gap:10px;
            padding:9px 11px;
            border-radius:9px;
            background:rgba(255,255,255,.025);
        }

        .health-detail span {
            color:#758A83;
            font-size:10px;
        }

        .health-detail strong {
            color:#C9D8D4;
            font-size:10px;
        }

        .telemetry-table-panel {
            overflow:hidden;
        }

        .telemetry-table-wrap {
            overflow-x:auto;
        }

        .telemetry-table {
            width:100%;
            border-collapse:collapse;
            min-width:760px;
        }

        .telemetry-table th {
            padding:12px 13px;
            text-align:left;
            color:#71857E;
            font-size:9px;
            font-weight:900;
            letter-spacing:1px;
            text-transform:uppercase;
            border-bottom:1px solid #1A3328;
        }

        .telemetry-table td {
            padding:14px 13px;
            color:#C4D2CE;
            font-size:11px;
            border-bottom:1px solid rgba(26,51,40,.65);
        }

        .telemetry-table tbody tr:hover {
            background:rgba(232,121,249,.025);
        }

        .telemetry-id {
            color:#899B95;
            font-weight:800;
        }

        .station-cell {
            display:flex;
            flex-direction:column;
            gap:4px;
        }

        .station-cell strong {
            color:#DDE9E5;
            font-size:11px;
        }

        .station-cell span {
            color:#687C75;
            font-size:9px;
        }

        .reading {
            font-weight:800;
        }

        .reading.temp {
            color:#FFB86B;
        }

        .reading.humidity {
            color:#8FD7FF;
        }

        .reading.power {
            color:#F0ABFC;
        }

        .telemetry-status {
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding:5px 8px;
            border-radius:999px;
            font-size:8px;
            font-weight:900;
            letter-spacing:.7px;
        }

        .telemetry-status i {
            width:5px;
            height:5px;
            border-radius:50%;
        }

        .telemetry-status.good {
            color:#73E2B7;
            background:rgba(75,216,166,.08);
        }

        .telemetry-status.good i {
            background:#4BD8A6;
        }

        .telemetry-status.warning {
            color:#FFD27A;
            background:rgba(245,158,11,.08);
        }

        .telemetry-status.warning i {
            background:#F59E0B;
        }

        .telemetry-status.danger {
            color:#FF8392;
            background:rgba(244,63,94,.08);
        }

        .telemetry-status.danger i {
            background:#F43F5E;
        }

        .telemetry-empty {
            padding:45px 20px;
            text-align:center;
            color:#71857E;
        }

        @media(max-width:1000px) {
            .telemetry-stats {
                grid-template-columns:repeat(2,minmax(0,1fr));
            }

            .telemetry-main-grid {
                grid-template-columns:1fr;
            }
        }

        @media(max-width:650px) {
            .telemetry-stats {
                grid-template-columns:1fr;
            }

            .telemetry-page-head {
                align-items:flex-start;
                flex-direction:column;
            }
        }

    </style>
    """

    return f"""
    <!DOCTYPE html>
    <html>

    <head>
        <title>Telemetry Monitoring | EV Charging Station Health Care</title>
        {STYLE}
        {telemetry_css}
    </head>

    <body class="dashboard-body">

        {sidebar("telemetry")}

        <div class="main-content">

            {topbar(
                "Telemetry Monitoring",
                "Live and historical sensor readings from charging stations."
            )}

            <div class="telemetry-page-head">

                <div>

                    <h1>
                        Telemetry Monitoring
                    </h1>
                </div>

            </div>

            <div class="telemetry-stats">

                <div class="telemetry-stat">
                    <div class="telemetry-stat-label">Total Records</div>
                    <div class="telemetry-stat-value pink">{total_records}</div>
                </div>

                <div class="telemetry-stat">
                    <div class="telemetry-stat-label">Latest Temperature</div>
                    <div class="telemetry-stat-value orange">{latest_temp:.1f}°C</div>
                </div>

                <div class="telemetry-stat">
                    <div class="telemetry-stat-label">Latest Power</div>
                    <div class="telemetry-stat-value pink">{latest_power:.1f} kW</div>
                </div>

                <div class="telemetry-stat">
                    <div class="telemetry-stat-label">Battery Health</div>
                    <div class="telemetry-stat-value green">{health}%</div>
                </div>

            </div>

            <div class="telemetry-main-grid">

                <div class="telemetry-panel">

                    <div class="telemetry-panel-head">
                        <div>
                            <div class="telemetry-kicker">SENSOR TREND</div>
                            <h2>Temperature Trend</h2>
                            <div class="telemetry-panel-subtitle">
                                Latest {len(data)} telemetry readings
                            </div>
                        </div>
                    </div>

                    <svg
                        class="telemetry-chart"
                        viewBox="0 0 440 245"
                        preserveAspectRatio="none"
                    >
                        <line class="chart-grid" x1="30" y1="45" x2="410" y2="45"/>
                        <line class="chart-grid" x1="30" y1="125" x2="410" y2="125"/>
                        <line class="chart-grid" x1="30" y1="205" x2="410" y2="205"/>

                        <text class="chart-label" x="3" y="49">HIGH</text>
                        <text class="chart-label" x="7" y="129">AVG</text>
                        <text class="chart-label" x="3" y="209">LOW</text>

                        <polyline
                            class="chart-line"
                            points="{graph_points}"
                        />
                    </svg>

                </div>

                <div class="telemetry-panel health-summary">

                    <div class="telemetry-kicker">
                        CURRENT CONDITION
                    </div>

                    <div class="health-ring">

                        <div class="health-ring-content">
                            <div class="health-number">{health}%</div>
                            <div class="health-label">HEALTH</div>
                        </div>

                    </div>

                    <div class="health-badge {health_class}">
                        {health_status}
                    </div>

                    <div class="health-details">

                        <div class="health-detail">
                            <span>Temperature</span>
                            <strong>{latest_temp:.1f}°C</strong>
                        </div>

                        <div class="health-detail">
                            <span>Humidity</span>
                            <strong>{latest_humidity:.1f}%</strong>
                        </div>

                        <div class="health-detail">
                            <span>Average Power</span>
                            <strong>{avg_power:.1f} kW</strong>
                        </div>

                    </div>

                </div>

            </div>

            <div class="telemetry-panel telemetry-table-panel">

                <div class="telemetry-panel-head">

                    <div>
                        <div class="telemetry-kicker">RECENT READINGS</div>
                        <h2>Telemetry Monitoring Data</h2>
                        <div class="telemetry-panel-subtitle">
                            Real sensor measurements received from charging stations.
                        </div>
                    </div>

                </div>

                <div class="telemetry-table-wrap">

                    <table class="telemetry-table">

                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Charging Station</th>
                                <th>Temperature</th>
                                <th>Humidity</th>
                                <th>Power Consumption</th>
                                <th>Condition</th>
                            </tr>
                        </thead>

                        <tbody>
                            {telemetry_rows}
                        </tbody>

                    </table>

                </div>

            </div>

        </div>

    </body>

    </html>
    """


@app.route("/maintenance")
def maintenance():
    if "user" not in session:
        return redirect("/")

    conn = get_db()
    try:
        records = conn.execute(
            """
            SELECT
                m.id,
                m.charging_station_id,
                m.maintenance_date,
                m.status,
                c.station_name,
                c.location,
                c.charger_type
            FROM maintenance m
            LEFT JOIN charging_stations c
                ON m.charging_station_id = c.id
            ORDER BY m.maintenance_date DESC, m.id DESC
            """
        ).fetchall()
    except sqlite3.Error:
        records = []
    conn.close()

    total = len(records)
    completed = 0
    pending = 0
    scheduled = 0

    for record in records:
        status = str(record["status"] or "").strip().lower()
        if status == "completed":
            completed += 1
        elif status == "pending":
            pending += 1
        elif status == "scheduled":
            scheduled += 1

    cards = []
    for record in records:
        status_raw = str(record["status"] or "Not specified").strip()
        status_key = status_raw.lower()
        if status_key == "completed":
            status_class = "maintenance-completed"
        elif status_key == "pending":
            status_class = "maintenance-pending"
        elif status_key == "scheduled":
            status_class = "maintenance-scheduled"
        else:
            status_class = "maintenance-other"

        station_name = (
            record["station_name"] or f"Station #{record['charging_station_id']}"
        )
        location = record["location"] or "Location unavailable"
        charger_type = record["charger_type"] or "Charger type unavailable"
        maintenance_date = record["maintenance_date"] or "Date unavailable"

        cards.append(
            f"""
        <div class="maintenance-card">
            <div class="maintenance-card-top">
                <div>
                    <div class="maintenance-kicker">MAINTENANCE RECORD</div>
                    <div class="maintenance-title">{station_name}</div>
                    <div class="maintenance-id">Station ID: {record['charging_station_id']}</div>
                </div>
                <span class="maintenance-status {status_class}">{status_raw.upper()}</span>
            </div>
            <div class="maintenance-details">
                <div class="maintenance-detail">
                    <span>MAINTENANCE DATE</span>
                    <strong>{maintenance_date}</strong>
                </div>
                <div class="maintenance-detail">
                    <span>CHARGER TYPE</span>
                    <strong>{charger_type}</strong>
                </div>
                <div class="maintenance-detail">
                    <span>LOCATION</span>
                    <strong>{location}</strong>
                </div>
                <div class="maintenance-detail">
                    <span>RECORD ID</span>
                    <strong>#{record['id']}</strong>
                </div>
            </div>
        </div>
        """
        )

    if not cards:
        cards.append(
            """
        <div class="component-empty">
            <h3>No maintenance records</h3>
            <p>No maintenance activity is available in the database yet.</p>
        </div>
        """
        )

    component_css = """
    <style>
        .component-stats { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; margin-bottom:22px; }
        .component-stat { background:#FFFFFF; border:1px solid #FFFFFF; border-radius:18px; padding:20px; box-shadow:0 8px 24px rgba(23,53,43,.08); }
        .component-stat-label { color:#71877D; font-size:11px; font-weight:800; letter-spacing:.8px; text-transform:uppercase; }
        .component-stat-number { margin-top:8px; font-size:30px; font-weight:900; color:#17352B; }
        .component-stat.total { border-top:4px solid #16A36A; }
        .component-stat.completed { border-top:4px solid #16A36A; }
        .component-stat.pending { border-top:4px solid #E6A23C; }
        .component-stat.scheduled { border-top:4px solid #D65C9E; }
        .maintenance-panel { background:#FFFFFF; border:1px solid #FFFFFF; border-radius:20px; padding:22px; box-shadow:0 8px 24px rgba(23,53,43,.08); }
        .maintenance-list { display:grid; gap:14px; }
        .maintenance-card { background:#F8FCFA; border:1px solid #E2EEE8; border-radius:16px; padding:19px; transition:.2s ease; }
        .maintenance-card:hover { transform:translateY(-2px); box-shadow:0 10px 24px rgba(23,53,43,.07); }
        .maintenance-card-top { display:flex; justify-content:space-between; align-items:flex-start; gap:15px; }
        .maintenance-kicker { color:#168553; font-size:9px; font-weight:900; letter-spacing:1.4px; margin-bottom:6px; }
        .maintenance-title { color:#17352B; font-size:17px; font-weight:850; }
        .maintenance-id { color:#789087; font-size:11px; margin-top:4px; }
        .maintenance-status { padding:7px 10px; border-radius:999px; font-size:9px; font-weight:900; letter-spacing:.8px; white-space:nowrap; }
        .maintenance-completed { color:#168553; background:#EAF8F0; border:1px solid #BFE6D1; }
        .maintenance-pending { color:#9A6813; background:#FFF7E6; border:1px solid #F2D79C; }
        .maintenance-scheduled { color:#A44379; background:#FCECF6; border:1px solid #EFC6DD; }
        .maintenance-other { color:#5B7067; background:#F0F5F2; border:1px solid #D7E5DE; }
        .maintenance-details { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-top:17px; }
        .maintenance-detail { background:#FFFFFF; border:1px solid #E4EEE9; border-radius:11px; padding:12px; min-width:0; }
        .maintenance-detail span { display:block; color:#789087; font-size:8px; font-weight:900; letter-spacing:.9px; margin-bottom:5px; }
        .maintenance-detail strong { display:block; color:#355349; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .component-empty { text-align:center; padding:55px 20px; color:#71877D; }
        .component-empty h3 { color:#355349; margin:0 0 7px; }
        .component-empty p { margin:0; font-size:13px; }
        @media(max-width:900px) { .component-stats { grid-template-columns:repeat(2,1fr); } .maintenance-details { grid-template-columns:repeat(2,1fr); } }
        @media(max-width:600px) { .component-stats { grid-template-columns:1fr; } .maintenance-card-top { flex-direction:column; } .maintenance-details { grid-template-columns:1fr; } }
    </style>
    """

    return f"""
    <!DOCTYPE html>
    <html><head><title>Maintenance | EV Charging Station Health Care</title>{STYLE}{component_css}</head>
    <body class="dashboard-body">
        {sidebar("maintenance")}
        <div class="main-content">
            {topbar("Maintenance", "Track completed, scheduled and pending maintenance activity")}
            <div class="page-top"><div><h1 class="page-title">Maintenance Management</h1><div class="page-subtitle">Monitor maintenance activity across the charging network.</div></div></div>
            <div class="component-stats">
                <div class="component-stat total"><div class="component-stat-label">Total Records</div><div class="component-stat-number">{total}</div></div>
                <div class="component-stat completed"><div class="component-stat-label">Completed</div><div class="component-stat-number">{completed}</div></div>
                <div class="component-stat pending"><div class="component-stat-label">Pending</div><div class="component-stat-number">{pending}</div></div>
                <div class="component-stat scheduled"><div class="component-stat-label">Scheduled</div><div class="component-stat-number">{scheduled}</div></div>
            </div>
            <div class="maintenance-panel">
                <div class="panel-heading-row"><div><div class="section-kicker">MAINTENANCE LOG</div><h2 class="panel-title">Maintenance Records</h2><div class="panel-subtitle">Latest maintenance activity from the database</div></div></div>
                <div class="maintenance-list">{"".join(cards)}</div>
            </div>
        </div>
    </body></html>
    """


@app.route("/predictions", methods=["GET", "POST"])
def predictions():
    if "user" not in session:
        return redirect("/")

    message = ""
    message_class = ""
    conn = get_db()
    try:
        stations_data = conn.execute(
            "SELECT id, station_name FROM charging_stations ORDER BY station_name"
        ).fetchall()
    except sqlite3.Error:
        stations_data = []

    if request.method == "POST":
        try:
            station_id = int(request.form.get("charging_station_id", "0"))
            temperature = float(request.form.get("temperature", "0"))
            humidity = float(request.form.get("humidity", "0"))
            power = float(request.form.get("power_consumption", "0"))
            if not station_id:
                raise ValueError("Please select a charging station.")

            model_path = os.path.join(
                os.path.dirname(__file__),
                "ev-health-monitoring-system",
                "backend",
                "ml",
                "model.pkl",
            )
            if joblib is not None and pd is not None and os.path.exists(model_path):
                model = joblib.load(model_path)
                sample = pd.DataFrame(
                    [[temperature, humidity, power]],
                    columns=["temperature", "humidity", "power_consumption"],
                )
                result = int(model.predict(sample)[0])
            else:
                result = (
                    1 if sum([temperature > 45, humidity > 75, power > 25]) >= 2 else 0
                )

            prediction_text = (
                "Failure Expected" if result == 1 else "Charging Station Healthy"
            )
            conn.execute(
                "INSERT INTO predictions (charging_station_id, temperature, humidity, power_consumption, prediction) VALUES (?, ?, ?, ?, ?)",
                (station_id, temperature, humidity, power, prediction_text),
            )
            conn.commit()
            message = f"Prediction completed: {prediction_text}"
            message_class = "success-message" if result == 0 else "warning-message"
        except Exception as exc:
            message = str(exc)
            message_class = "error-message"

    try:
        records = conn.execute(
            "SELECT p.id,p.charging_station_id,p.temperature,p.humidity,p.power_consumption,p.prediction,s.station_name FROM predictions p LEFT JOIN charging_stations s ON s.id=p.charging_station_id ORDER BY p.id DESC"
        ).fetchall()
    except sqlite3.Error:
        records = []
    conn.close()

    total = len(records)
    healthy = sum("healthy" in str(r["prediction"] or "").lower() for r in records)
    failure_expected = sum(
        any(x in str(r["prediction"] or "").lower() for x in ["failure", "critical"])
        for r in records
    )
    other = max(0, total - healthy - failure_expected)

    cards = []
    for record in records:
        text = str(record["prediction"] or "Prediction unavailable")
        low = text.lower()
        if "failure" in low or "critical" in low:
            cls, label = "prediction-danger", "ATTENTION"
        elif "healthy" in low:
            cls, label = "prediction-good", "HEALTHY"
        else:
            cls, label = "prediction-other", "REVIEW"
        cards.append(
            f"""
        <article class="modern-prediction-card">
            <div class="modern-prediction-main">
                <div><div class="prediction-kicker">PREDICTION #{record['id']}</div><h3>{html.escape(text)}</h3><div class="prediction-station">{html.escape(record['station_name'] or 'Charging station unavailable')}</div></div>
                <span class="modern-status {cls}">{label}</span>
            </div>
            <div class="prediction-readings">
                <div><span>Temperature</span><strong>{float(record['temperature'] or 0):.1f} °C</strong></div>
                <div><span>Humidity</span><strong>{float(record['humidity'] or 0):.1f} %</strong></div>
                <div><span>Power</span><strong>{float(record['power_consumption'] or 0):.1f} kW</strong></div>
            </div>
        </article>"""
        )

    station_options = "".join(
        f'<option value="{s["id"]}">{html.escape(s["station_name"] or "Charging Station " + str(s["id"]))}</option>'
        for s in stations_data
    )

    css = """
    <style>
    .modern-page-heading{text-align:center;margin:4px 0 24px}.modern-page-heading h1{margin:0;color:#17352B;font-size:38px;font-weight:900;letter-spacing:-1.2px}.modern-page-heading p{margin:9px 0 0;color:#6C8278}.heading-line{width:72px;height:4px;border-radius:99px;margin:12px auto 0;background:linear-gradient(90deg,#16A36A,#E49A18,#D83F83)}
    .prediction-form-card{background:#FFF;border-radius:22px;padding:24px;box-shadow:0 10px 28px rgba(23,53,43,.08);margin-bottom:20px}.prediction-form-title{color:#17352B;font-size:19px;font-weight:850;margin:0 0 4px}.prediction-form-subtitle{color:#71877D;font-size:13px;margin-bottom:18px}.prediction-form-grid{display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr auto;gap:14px;align-items:end}.prediction-field label{display:block;color:#61786E;font-size:11px;font-weight:800;letter-spacing:.6px;margin-bottom:7px}.prediction-field input,.prediction-field select{width:100%;height:48px;border-radius:12px;padding:0 13px;font-size:14px}.prediction-run{height:48px;padding:0 22px;border:0;border-radius:12px;font-weight:850;cursor:pointer;background:linear-gradient(135deg,#D83F83,#E05A9D)!important;color:#FFF!important;box-shadow:0 9px 22px rgba(216,63,131,.18);white-space:nowrap}.prediction-message{padding:13px 15px;border-radius:12px;margin-top:16px;font-weight:750}.success-message{background:#EAF8F1;color:#168553;border:1px solid #BFE6D1}.warning-message{background:#FFF5E4;color:#A96812;border:1px solid #F1D29B}.error-message{background:#FFF0F2;color:#C43B55;border:1px solid #F2C4CC}
    .prediction-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}.prediction-stat{background:#FFF;border-radius:18px;padding:19px;box-shadow:0 9px 25px rgba(23,53,43,.07)}.prediction-stat:nth-child(1){border-top:4px solid #16A36A}.prediction-stat:nth-child(2){border-top:4px solid #D83F83}.prediction-stat:nth-child(3){border-top:4px solid #E49A18}.prediction-stat:nth-child(4){border-top:4px solid #16A36A}.prediction-stat-label{color:#71877D;font-size:10px;font-weight:850;letter-spacing:.8px;text-transform:uppercase}.prediction-stat-number{margin-top:6px;color:#17352B;font-size:30px;font-weight:900}.prediction-stat:nth-child(2) .prediction-stat-number{color:#D83F83}.prediction-stat:nth-child(3) .prediction-stat-number{color:#C77B0B}
    .prediction-list-panel{background:#FFF;border-radius:22px;padding:22px;box-shadow:0 10px 28px rgba(23,53,43,.08)}.prediction-list-title{margin:0;color:#17352B;font-size:21px}.prediction-list-subtitle{color:#71877D;font-size:13px;margin:5px 0 18px}.modern-prediction-card{background:#FAFDFC;border:1px solid #E2EEE8;border-radius:17px;padding:19px;margin-bottom:13px}.modern-prediction-main{display:flex;justify-content:space-between;gap:18px;align-items:flex-start}.modern-prediction-card h3{margin:3px 0 4px;color:#17352B;font-size:19px}.prediction-kicker{color:#168553;font-size:9px;font-weight:900;letter-spacing:1.3px}.prediction-station{color:#71877D;font-size:13px}.modern-status{padding:8px 13px;border-radius:999px;font-size:10px;font-weight:900;letter-spacing:.7px}.prediction-good{color:#168553!important;background:#EAF8F1!important;border:1px solid #BFE6D1!important}.prediction-danger{color:#C43B55!important;background:#FFF0F2!important;border:1px solid #F2C4CC!important}.prediction-other{color:#A44379!important;background:#FCECF5!important;border:1px solid #EFC6DD!important}.prediction-readings{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:17px}.prediction-readings div{background:#FFF;border:1px solid #E4EEE9;border-radius:11px;padding:12px}.prediction-readings span{display:block;color:#789087;font-size:9px;font-weight:850;text-transform:uppercase;margin-bottom:4px}.prediction-readings strong{color:#355349;font-size:13px}
    @media(max-width:1000px){.prediction-form-grid{grid-template-columns:repeat(2,1fr)}.prediction-run{width:100%}.prediction-stats{grid-template-columns:repeat(2,1fr)}}@media(max-width:600px){.prediction-form-grid,.prediction-stats,.prediction-readings{grid-template-columns:1fr}.modern-prediction-main{flex-direction:column}}
    </style>"""

    message_html = (
        f'<div class="prediction-message {message_class}">{html.escape(message)}</div>'
        if message
        else ""
    )
    cards_html = (
        "".join(cards)
        or '<div class="component-empty"><h3>No predictions yet</h3><p>Run the model above to create the first prediction record.</p></div>'
    )

    return f"""
    <!DOCTYPE html><html><head><title>Predictions | EV Charging Station Health Care</title>{STYLE}{css}</head>
    <body class="dashboard-body">{sidebar("predictions")}
        <main class="main-content">
            <div class="modern-page-heading"><h1>Predictive Intelligence</h1><div class="heading-line"></div></div>
            <section class="prediction-form-card">
                <div class="section-kicker">RUN MODEL</div><h2 class="prediction-form-title">Predict Charging Station Health</h2><div class="prediction-form-subtitle">Enter the latest operating readings and run the prediction.</div>
                <form method="POST" class="prediction-form-grid">
                    <div class="prediction-field"><label>Charging Station</label><select name="charging_station_id" required>{station_options}</select></div>
                    <div class="prediction-field"><label>Temperature (°C)</label><input type="number" name="temperature" step="0.1" value="25" required></div>
                    <div class="prediction-field"><label>Humidity (%)</label><input type="number" name="humidity" step="0.1" value="50" required></div>
                    <div class="prediction-field"><label>Power Consumption (kW)</label><input type="number" name="power_consumption" step="0.1" value="15" required></div>
                    <button type="submit" class="prediction-run">Run Prediction</button>
                </form>{message_html}
            </section>
            <section class="prediction-stats"><div class="prediction-stat"><div class="prediction-stat-label">Total Predictions</div><div class="prediction-stat-number">{total}</div></div><div class="prediction-stat"><div class="prediction-stat-label">Healthy</div><div class="prediction-stat-number">{healthy}</div></div><div class="prediction-stat"><div class="prediction-stat-label">Failure Expected</div><div class="prediction-stat-number">{failure_expected}</div></div><div class="prediction-stat"><div class="prediction-stat-label">Other Results</div><div class="prediction-stat-number">{other}</div></div></section>
            <section class="prediction-list-panel"><div class="section-kicker">RECENT RESULTS</div><h2 class="prediction-list-title">Prediction History</h2><div class="prediction-list-subtitle">Latest model outputs with the readings used for each prediction.</div>{cards_html}</section>
        </main>
    </body></html>"""


@app.route("/failure-history")
def failure_history():

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    try:
        failures = conn.execute(
            """
            SELECT
                f.id,
                f.charging_station_id,
                f.failure_type,
                f.description,
                f.failure_date,
                f.resolved,
                c.station_name,
                c.location,
                c.charger_type
            FROM failure_history f
            LEFT JOIN charging_stations c
                ON f.charging_station_id = c.id
            ORDER BY f.failure_date DESC
        """
        ).fetchall()

    except sqlite3.Error:
        failures = []

    conn.close()

    total_failures = len(failures)
    resolved_count = 0
    unresolved_count = 0

    for failure in failures:
        value = str(failure["resolved"]).strip().lower()

        if value in ("yes", "true", "1", "resolved"):
            resolved_count += 1
        else:
            unresolved_count += 1

    failure_cards = []

    for failure in failures:

        failure_type = failure["failure_type"] or "Unknown Failure"
        description = failure["description"] or "No description available."

        station_name = (
            failure["station_name"]
            if failure["station_name"]
            else f"Station #{failure['charging_station_id']}"
        )

        location = failure["location"] or "Location unavailable"
        charger_type = failure["charger_type"] or "Charger"
        failure_date = failure["failure_date"] or "Date unavailable"

        resolved_value = str(failure["resolved"]).strip().lower()

        if resolved_value in ("yes", "true", "1", "resolved"):
            status_text = "RESOLVED"
            status_class = "resolved"
            status_icon = ""
        else:
            status_text = "UNRESOLVED"
            status_class = "unresolved"
            status_icon = "!"

        failure_cards.append(
            f"""
        <div class="failure-card">

            <div class="failure-card-top">

                <div class="failure-main">

                    <div class="failure-icon {status_class}">
                        {status_icon}
                    </div>

                    <div class="failure-title-area">

                        <div class="failure-type">
                            {failure_type}
                        </div>

                        <div class="failure-station">
                            {station_name}
                        </div>

                    </div>

                </div>

                <div class="failure-status {status_class}">
                    {status_text}
                </div>

            </div>

            <div class="failure-description">
                {description}
            </div>

            <div class="failure-details">

                <div class="failure-detail">
                    <span class="detail-label">STATION</span>
                    <span class="detail-value">{station_name}</span>
                </div>

                <div class="failure-detail">
                    <span class="detail-label">LOCATION</span>
                    <span class="detail-value">{location}</span>
                </div>

                <div class="failure-detail">
                    <span class="detail-label">CHARGER</span>
                    <span class="detail-value">{charger_type}</span>
                </div>

                <div class="failure-detail">
                    <span class="detail-label">FAILURE DATE</span>
                    <span class="detail-value">{failure_date}</span>
                </div>

            </div>

        </div>
        """
        )

    if not failure_cards:
        failure_cards.append(
            """
        <div class="failure-empty">
            <div class="failure-empty-icon"></div>
            <h3>No Failure History</h3>
            <p>No charging station failures have been recorded yet.</p>
        </div>
        """
        )

    failure_css = r"""
    <style>

        .failure-page-header {
            display:flex;
            justify-content:space-between;
            align-items:flex-end;
            gap:20px;
            margin-bottom:25px;
        }

        .failure-eyebrow {
            color:#E879F9;
            font-size:11px;
            font-weight:800;
            letter-spacing:1.8px;
            margin-bottom:7px;
        }

        .failure-page-header h1 {
            margin:0 0 6px;
            font-size:32px;
            color:#F0FDF4;
        }

        .failure-page-header p {
            margin:0;
            color:#94A3A0;
            font-size:14px;
        }

        .history-live {
            display:flex;
            align-items:center;
            gap:8px;
            padding:9px 13px;
            border-radius:999px;
            border:1px solid rgba(232,121,249,.25);
            background:rgba(232,121,249,.07);
            color:#F0ABFC;
            font-size:10px;
            font-weight:900;
            letter-spacing:1px;
        }

        .history-live-dot {
            width:7px;
            height:7px;
            border-radius:50%;
            background:#E879F9;
            box-shadow:0 0 10px rgba(232,121,249,.8);
        }

        .failure-stats {
            display:grid;
            grid-template-columns:repeat(3,minmax(0,1fr));
            gap:16px;
            margin-bottom:22px;
        }

        .failure-stat {
            position:relative;
            overflow:hidden;
            padding:20px;
            border-radius:18px;
            background:linear-gradient(145deg,#0E211E,#0A1716);
            border:1px solid rgba(255,255,255,.07);
        }

        .failure-stat.total {
            border-color:rgba(232,121,249,.20);
        }

        .failure-stat.resolved {
            border-color:rgba(75,216,166,.20);
        }

        .failure-stat.unresolved {
            border-color:rgba(244,63,94,.22);
        }

        .failure-stat-label {
            color:#81958E;
            font-size:11px;
            font-weight:700;
            letter-spacing:.7px;
            text-transform:uppercase;
        }

        .failure-stat-number {
            margin-top:8px;
            font-size:30px;
            font-weight:800;
            color:#F0FDF4;
        }

        .failure-panel {
            background:linear-gradient(145deg,#0D201D,#091513);
            border:1px solid rgba(255,255,255,.07);
            border-radius:20px;
            padding:22px;
        }

        .failure-panel-header {
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:18px;
        }

        .failure-panel-header h2 {
            margin:0;
            font-size:20px;
            color:#EDF7F3;
        }

        .failure-panel-kicker {
            color:#E879F9;
            font-size:10px;
            font-weight:900;
            letter-spacing:1.6px;
            margin-bottom:5px;
        }

        .failure-count {
            color:#91A7A1;
            background:rgba(255,255,255,.05);
            border:1px solid rgba(255,255,255,.07);
            border-radius:999px;
            padding:7px 11px;
            font-size:10px;
        }

        .failure-list {
            display:grid;
            gap:13px;
        }

        .failure-card {
            padding:19px;
            border-radius:16px;
            background:rgba(255,255,255,.025);
            border:1px solid rgba(255,255,255,.065);
            transition:transform .2s ease,border-color .2s ease;
        }

        .failure-card:hover {
            transform:translateY(-2px);
            border-color:rgba(232,121,249,.25);
        }

        .failure-card-top {
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            gap:15px;
        }

        .failure-main {
            display:flex;
            align-items:center;
            gap:13px;
            min-width:0;
        }

        .failure-icon {
            width:42px;
            height:42px;
            display:grid;
            place-items:center;
            border-radius:12px;
            font-size:18px;
            font-weight:900;
            flex-shrink:0;
        }

        .failure-icon.resolved {
            color:#73E2B7;
            background:rgba(75,216,166,.10);
            border:1px solid rgba(75,216,166,.20);
        }

        .failure-icon.unresolved {
            color:#FF8392;
            background:rgba(244,63,94,.10);
            border:1px solid rgba(244,63,94,.20);
        }

        .failure-type {
            color:#EDF7F3;
            font-size:16px;
            font-weight:800;
            margin-bottom:5px;
        }

        .failure-station {
            color:#82958F;
            font-size:11px;
        }

        .failure-status {
            flex-shrink:0;
            border-radius:999px;
            padding:6px 9px;
            font-size:9px;
            font-weight:900;
            letter-spacing:1px;
        }

        .failure-status.resolved {
            color:#73E2B7;
            background:rgba(75,216,166,.08);
            border:1px solid rgba(75,216,166,.16);
        }

        .failure-status.unresolved {
            color:#FF8392;
            background:rgba(244,63,94,.08);
            border:1px solid rgba(244,63,94,.16);
        }

        .failure-description {
            margin:15px 0 17px 55px;
            color:#9BAEA8;
            font-size:13px;
            line-height:1.6;
        }

        .failure-details {
            display:grid;
            grid-template-columns:repeat(4,minmax(0,1fr));
            gap:10px;
            margin-left:55px;
        }

        .failure-detail {
            padding:11px 12px;
            border-radius:10px;
            background:rgba(255,255,255,.025);
            min-width:0;
        }

        .detail-label {
            display:block;
            color:#647873;
            font-size:8px;
            font-weight:900;
            letter-spacing:1px;
            margin-bottom:5px;
        }

        .detail-value {
            display:block;
            color:#C7D5D1;
            font-size:11px;
            overflow:hidden;
            text-overflow:ellipsis;
            white-space:nowrap;
        }

        .failure-empty {
            text-align:center;
            padding:60px 20px;
            color:#81958E;
        }

        .failure-empty-icon {
            width:58px;
            height:58px;
            display:grid;
            place-items:center;
            margin:0 auto 14px;
            border-radius:50%;
            color:#4BD8A6;
            background:rgba(75,216,166,.08);
            border:1px solid rgba(75,216,166,.18);
            font-size:26px;
        }

        .failure-empty h3 {
            margin:0 0 6px;
            color:#DCE9E5;
        }

        .failure-empty p {
            margin:0;
            font-size:13px;
        }

        @media (max-width:900px) {
            .failure-details {
                grid-template-columns:repeat(2,minmax(0,1fr));
            }
        }

        @media (max-width:700px) {
            .failure-stats {
                grid-template-columns:1fr;
            }

            .failure-page-header {
                align-items:flex-start;
                flex-direction:column;
            }

            .failure-card-top {
                flex-direction:column;
            }

            .failure-description {
                margin-left:0;
            }

            .failure-details {
                margin-left:0;
                grid-template-columns:1fr;
            }
        }

    </style>
    """

    return f"""
    <!DOCTYPE html>
    <html>

    <head>
        <title>Failure History</title>
        {STYLE}
        {failure_css}
    </head>

    <body class="dashboard-body">

        {sidebar("failure")}

        <div class="main-content">

            {topbar(
                "Failure History",
                "Review historical charging station failures and resolutions."
            )}

            <div class="failure-page-header">

                <div>

                    <h1>
                        Failure History
                    </h1>

                </div>

            </div>

            <div class="failure-stats">

                <div class="failure-stat total">
                    <div class="failure-stat-label">
                        Total Failures
                    </div>
                    <div class="failure-stat-number">
                        {total_failures}
                    </div>
                </div>

                <div class="failure-stat resolved">
                    <div class="failure-stat-label">
                        Resolved
                    </div>
                    <div class="failure-stat-number">
                        {resolved_count}
                    </div>
                </div>

                <div class="failure-stat unresolved">
                    <div class="failure-stat-label">
                        Unresolved
                    </div>
                    <div class="failure-stat-number">
                        {unresolved_count}
                    </div>
                </div>

            </div>

            <div class="failure-panel">

                <div class="failure-panel-header">

                    <div>
                        <div class="failure-panel-kicker">
                            MAINTENANCE LOG
                        </div>

                        <h2>
                            Recent Failures
                        </h2>
                    </div>

                    <div class="failure-count">
                        {total_failures} records
                    </div>

                </div>

                <div class="failure-list">
                    {"".join(failure_cards)}
                </div>

            </div>

        </div>

    </body>
    </html>
    """


@app.route("/charging-sessions")
def charging_sessions():
    return show_table_page(
        "charging_sessions",
        "Charging Sessions",
        "Review charging activity and session usage across the network.",
        "sessions",
    )


@app.route("/operators")
def operators():
    return show_table_page(
        "operators",
        "Operators",
        "Review the people and teams responsible for charging operations.",
        "operators",
    )


@app.route("/feedback")
def feedback():
    return show_table_page(
        "feedback",
        "Feedback",
        "Review user feedback and service experience across the network.",
        "feedback",
    )


# =========================================================
# BATTERY HEALTH
# =========================================================


@app.route("/analytics")
def analytics():
    if "user" not in session:
        return redirect("/")
    station_id = request.args.get("station", "")
    conn = get_db()
    try:
        stations_data = conn.execute(
            "SELECT id, station_name FROM charging_stations ORDER BY station_name"
        ).fetchall()
        if not station_id and stations_data:
            station_id = str(stations_data[0]["id"])
        station = (
            conn.execute(
                "SELECT id,station_name,location,charger_type FROM charging_stations WHERE id=?",
                (station_id,),
            ).fetchone()
            if station_id
            else None
        )
        telemetry = (
            conn.execute(
                "SELECT * FROM telemetry WHERE charging_station_id=? ORDER BY id DESC LIMIT 20",
                (station_id,),
            ).fetchall()
            if station_id
            else []
        )
        sessions = (
            conn.execute(
                "SELECT COUNT(*) FROM charging_sessions WHERE station_id=?",
                (station_id,),
            ).fetchone()[0]
            if station_id
            else 0
        )
        energy = (
            conn.execute(
                "SELECT COALESCE(SUM(energy_consumed),0) FROM charging_sessions WHERE station_id=?",
                (station_id,),
            ).fetchone()[0]
            if station_id
            else 0
        )
        cost = (
            conn.execute(
                "SELECT COALESCE(SUM(cost),0) FROM charging_sessions WHERE station_id=?",
                (station_id,),
            ).fetchone()[0]
            if station_id
            else 0
        )
        alerts = (
            conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE charging_station_id=?", (station_id,)
            ).fetchone()[0]
            if station_id
            else 0
        )
        failures = (
            conn.execute(
                "SELECT COUNT(*) FROM failure_history WHERE charging_station_id=?",
                (station_id,),
            ).fetchone()[0]
            if station_id
            else 0
        )
        maintenance = (
            conn.execute(
                "SELECT COUNT(*) FROM maintenance WHERE charging_station_id=?",
                (station_id,),
            ).fetchone()[0]
            if station_id
            else 0
        )
    except sqlite3.Error:
        stations_data, telemetry, station = [], [], None
        sessions = energy = cost = alerts = failures = maintenance = 0
    conn.close()

    latest = telemetry[0] if telemetry else None
    latest_temp = float(latest["temperature"] or 0) if latest else 0
    latest_humidity = float(latest["humidity"] or 0) if latest else 0
    latest_power = float(latest["power_consumption"] or 0) if latest else 0
    health = calculate_health(latest_temp, latest_power) if latest else 0
    healthy_count = sum(
        calculate_health(
            float(r["temperature"] or 0), float(r["power_consumption"] or 0)
        )
        >= 80
        for r in telemetry
    )
    warning_count = sum(
        60
        <= calculate_health(
            float(r["temperature"] or 0), float(r["power_consumption"] or 0)
        )
        < 80
        for r in telemetry
    )
    critical_count = max(0, len(telemetry) - healthy_count - warning_count)
    options = "".join(
        f'<option value="{s["id"]}" {"selected" if str(s["id"]) == str(station_id) else ""}>{html.escape(s["station_name"] or "Charging Station " + str(s["id"]))}</option>'
        for s in stations_data
    )
    name = html.escape(
        station["station_name"] if station else "Charging Station Analytics"
    )
    status = "Healthy" if health >= 80 else ("Warning" if health >= 60 else "Critical")
    status_cls = (
        "healthy" if health >= 80 else ("warning" if health >= 60 else "critical")
    )
    rows_html = (
        "".join(
            f'<tr><td>{r["id"]}</td><td>{float(r["temperature"] or 0):.1f} °C</td><td>{float(r["humidity"] or 0):.1f} %</td><td>{float(r["power_consumption"] or 0):.2f} kW</td><td><span class="health-pill">{calculate_health(float(r["temperature"] or 0), float(r["power_consumption"] or 0))}%</span></td></tr>'
            for r in telemetry[:10]
        )
        or '<tr><td colspan="5">No telemetry records available for this station.</td></tr>'
    )

    def _chart_points(values, width=520, height=210):
        vals = [float(v or 0) for v in values]
        if not vals:
            return ""
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or 1
        n = len(vals)
        return " ".join(
            f"{18+i*(width-36)/max(1,n-1):.1f},{(height-20)-((v-lo)/span)*(height-45):.1f}"
            for i, v in enumerate(vals)
        )

    temp_points = _chart_points([r["temperature"] for r in reversed(telemetry[:12])])
    power_points = _chart_points(
        [r["power_consumption"] for r in reversed(telemetry[:12])]
    )
    css = """
    <style>
    .analytics-heading{text-align:center;margin:4px 0 24px}.analytics-heading h1{margin:0;color:#17352B;font-size:38px;font-weight:900;letter-spacing:-1.2px}.analytics-heading p{margin:9px 0 0;color:#6C8278}.analytics-line{width:72px;height:4px;border-radius:99px;margin:12px auto 0;background:linear-gradient(90deg,#16A36A,#E49A18,#D83F83)}
    .analytics-selector{background:#FFF;border-radius:20px;padding:20px;box-shadow:0 10px 28px rgba(23,53,43,.08);display:grid;grid-template-columns:1.2fr 1fr;gap:14px;align-items:end;margin-bottom:20px}.analytics-selector label{display:block;color:#61786E;font-size:11px;font-weight:850;margin-bottom:7px}.analytics-selector select{width:100%;height:48px;border-radius:12px;padding:0 13px}.analytics-load{height:48px;border:0;border-radius:12px;background:linear-gradient(135deg,#16A36A,#31B77D);color:#FFF;font-weight:850;cursor:pointer}
    .analytics-metrics{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:20px}.analytics-metric{background:#FFF;border-radius:17px;padding:18px;box-shadow:0 9px 25px rgba(23,53,43,.07);min-width:0}.analytics-metric:nth-child(3n+1){border-top:4px solid #16A36A}.analytics-metric:nth-child(3n+2){border-top:4px solid #D83F83}.analytics-metric:nth-child(3n){border-top:4px solid #E49A18}.analytics-metric span{display:block;color:#71877D;font-size:9px;font-weight:850;letter-spacing:.7px;text-transform:uppercase}.analytics-metric strong{display:block;margin-top:7px;color:#17352B;font-size:23px;font-weight:900}.analytics-metric:nth-child(2) strong{color:#D83F83}.analytics-metric:nth-child(3) strong{color:#C77B0B}.analytics-metric:nth-child(4) strong{color:#D83F83}.analytics-metric:nth-child(6) strong{color:#C77B0B}
    .analytics-two{display:grid;grid-template-columns:1fr 1fr;gap:20px}.analytics-panel{background:#FFF;border-radius:20px;padding:22px;box-shadow:0 10px 28px rgba(23,53,43,.08)}.analytics-panel h2{margin:0;color:#17352B;font-size:20px}.analytics-panel-sub{margin:5px 0 15px;color:#71877D;font-size:12px}.analytics-row{display:flex;justify-content:space-between;padding:13px 0;border-bottom:1px solid #E5EFEA;color:#61786E;font-size:13px}.analytics-row:last-child{border-bottom:0}.analytics-row strong{color:#355349}.health-visual{display:flex;align-items:center;justify-content:center;gap:25px;min-height:205px}.health-donut{width:150px;height:150px;border-radius:50%;display:grid;place-items:center;background:conic-gradient(#16A36A 0 75%,#D83F83 75% 87%,#E49A18 87% 100%);position:relative}.health-donut:after{content:"";width:102px;height:102px;border-radius:50%;background:#FFF;position:absolute}.health-center{position:relative;z-index:1;text-align:center}.health-center strong{display:block;color:#17352B;font-size:28px}.health-center span{color:#71877D;font-size:9px;font-weight:850;letter-spacing:.8px}.health-legend div{display:flex;align-items:center;gap:9px;margin:12px 0;color:#587067;font-size:12px}.health-dot{width:9px;height:9px;border-radius:50%}.health-dot.g{background:#16A36A}.health-dot.p{background:#D83F83}.health-dot.o{background:#E49A18}.status-strip{margin-top:15px;border-radius:12px;padding:13px 15px;font-weight:800}.status-strip.healthy{background:#EAF8F1;color:#168553}.status-strip.warning{background:#FFF5E4;color:#A96812}.status-strip.critical{background:#FFF0F2;color:#C43B55}
    .analytics-charts{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px}.analytics-chart-panel{background:#FFF;border:1px solid #DFECE6;border-radius:20px;padding:22px;box-shadow:0 10px 28px rgba(23,53,43,.07)}.analytics-chart-panel h2{margin:0;color:#17352B;font-size:20px}.analytics-chart-sub{margin:5px 0 14px;color:#71877D;font-size:12px}.analytics-chart-panel svg{width:100%;height:220px;display:block;background:#FAFDFC;border:1px solid #E7EFEA;border-radius:14px}.analytics-chart-panel svg line{stroke:#E1ECE7;stroke-width:1}.analytics-table{margin-top:20px;background:#FFF;border-radius:20px;padding:22px;box-shadow:0 10px 28px rgba(23,53,43,.08);overflow:auto}.analytics-table table{width:100%;border-collapse:collapse}.analytics-table th{padding:12px;text-align:left;background:#F4F9F6;color:#61786E;font-size:10px;letter-spacing:.5px}.analytics-table td{padding:12px;border-bottom:1px solid #E5EFEA;color:#355349;font-size:12px}.health-pill{display:inline-block;padding:6px 10px;border-radius:999px;background:#EAF8F1;color:#168553;font-weight:800;font-size:10px}
    @media(max-width:1100px){.analytics-metrics{grid-template-columns:repeat(3,1fr)}}@media(max-width:800px){.analytics-selector,.analytics-two{grid-template-columns:1fr}.analytics-metrics{grid-template-columns:repeat(2,1fr)}}@media(max-width:520px){.analytics-metrics{grid-template-columns:1fr}.health-visual{flex-direction:column}}
    </style>"""
    return f"""
    <!DOCTYPE html><html><head><title>{name} Analytics | EV Charging Station Health Care</title>{STYLE}{css}</head>
    <body class="dashboard-body">{sidebar("analytics")}
    <main class="main-content">
        <div class="analytics-heading"><h1>{name} Analytics</h1><div class="analytics-line"></div></div>
        <form class="analytics-selector" method="GET"><div><label>Select Charging Station</label><select name="station" required>{options}</select></div><button class="analytics-load" type="submit">Load Analytics</button></form>
        <section class="analytics-metrics"><div class="analytics-metric"><span>Telemetry Records</span><strong>{len(telemetry)}</strong></div><div class="analytics-metric"><span>Charging Sessions</span><strong>{sessions}</strong></div><div class="analytics-metric"><span>Energy Consumed</span><strong>{float(energy or 0):.2f} kWh</strong></div><div class="analytics-metric"><span>Charging Cost</span><strong>₹{float(cost or 0):.2f}</strong></div><div class="analytics-metric"><span>Total Alerts</span><strong>{alerts}</strong></div><div class="analytics-metric"><span>Total Failures</span><strong>{failures}</strong></div></section>
        <section class="analytics-two">
            <article class="analytics-panel"><div class="section-kicker">HEALTH &amp; MAINTENANCE</div><h2>Operational Summary</h2><div class="analytics-panel-sub">Latest readings and service activity.</div><div class="analytics-row"><span>Maintenance Records</span><strong>{maintenance}</strong></div><div class="analytics-row"><span>Latest Temperature</span><strong>{latest_temp:.2f} °C</strong></div><div class="analytics-row"><span>Latest Humidity</span><strong>{latest_humidity:.2f} %</strong></div><div class="analytics-row"><span>Latest Power</span><strong>{latest_power:.2f} kW</strong></div></article>
            <article class="analytics-panel"><div class="section-kicker">CURRENT HEALTH</div><h2>Station Health Status</h2><div class="analytics-panel-sub">Calculated from the latest telemetry readings.</div><div class="health-visual"><div class="health-donut"><div class="health-center"><strong>{health}%</strong><span>HEALTH STATUS</span></div></div><div class="health-legend"><div><i class="health-dot g"></i>Healthy <strong>{healthy_count}</strong></div><div><i class="health-dot p"></i>Warning <strong>{warning_count}</strong></div><div><i class="health-dot o"></i>Critical <strong>{critical_count}</strong></div></div></div><div class="status-strip {status_cls}">Station status: {status}</div></article>
        </section>
        <section class="analytics-charts"><article class="analytics-chart-panel"><div class="section-kicker">TEMPERATURE</div><h2>Temperature Trend</h2><div class="analytics-chart-sub">Recent thermal readings from this station.</div><svg viewBox="0 0 520 210" preserveAspectRatio="none"><line x1="18" y1="190" x2="502" y2="190"/><line x1="18" y1="120" x2="502" y2="120"/><line x1="18" y1="50" x2="502" y2="50"/><polyline points="{temp_points}" fill="none" stroke="#16A36A" stroke-width="4" stroke-linecap="round"/></svg></article><article class="analytics-chart-panel"><div class="section-kicker" style="color:#D83F83!important">POWER CONSUMPTION</div><h2>Power Trend</h2><div class="analytics-chart-sub">Recent load readings from this station.</div><svg viewBox="0 0 520 210" preserveAspectRatio="none"><line x1="18" y1="190" x2="502" y2="190"/><line x1="18" y1="120" x2="502" y2="120"/><line x1="18" y1="50" x2="502" y2="50"/><polyline points="{power_points}" fill="none" stroke="#D83F83" stroke-width="4" stroke-linecap="round"/></svg></article></section>
        <section class="analytics-table"><div class="section-kicker">RECENT ACTIVITY</div><h2 style="margin:0;color:#17352B">Latest Telemetry</h2><div class="analytics-panel-sub">Recent sensor readings from this station.</div><table><thead><tr><th>ID</th><th>Temperature</th><th>Humidity</th><th>Power</th><th>Health</th></tr></thead><tbody>{rows_html}</tbody></table></section>
    </main></body></html>"""


@app.route("/battery-health")
def battery_health():

    if "user" not in session:
        return redirect("/")

    conn = get_db()

    data = conn.execute(
        """
        SELECT *
        FROM telemetry
        ORDER BY id DESC
        LIMIT 20
        """
    ).fetchall()

    conn.close()

    data = list(reversed(data))

    health_values = []
    temperatures = []
    powers = []

    for item in data:
        temperature = item["temperature"] or 0
        power = item["power_consumption"] or 0
        health_values.append(calculate_health(temperature, power))
        temperatures.append(temperature)
        powers.append(power)

    current = health_values[-1] if health_values else 0
    latest_temp = temperatures[-1] if temperatures else 0
    latest_power = powers[-1] if powers else 0
    avg_health = (
        round(sum(health_values) / len(health_values), 1) if health_values else 0
    )

    if current >= 80:
        status = "HEALTHY"
        badge = "badge-good"
        status_class = "health-good"
    elif current >= 60:
        status = "MODERATE"
        badge = "badge-warning"
        status_class = "health-warning"
    else:
        status = "CRITICAL"
        badge = "badge-danger"
        status_class = "health-danger"

    # Build a simple SVG trend from the same backend health calculation.
    points = []
    if health_values:
        for i, value in enumerate(health_values):
            x = 25 + (i * 390 / max(1, len(health_values) - 1))
            y = 220 - ((value / 100) * 175)
            points.append(f"{x:.1f},{y:.1f}")
    graph_points = " ".join(points)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Battery Health | EV Charging Station Health Care</title>
        {STYLE}
    </head>
    <body class="dashboard-body">
        {sidebar("battery")}

        <div class="main-content">
            {topbar("Battery Health", "Monitor battery condition and recent health trends")}

            <div class="page-top">
                <div>
                    <h1 class="page-title">Battery Health Monitoring</h1>
                </div>
            </div>

            <div class="battery-hero">
                <div class="panel battery-hero-card {status_class}">
                    <div class="section-kicker">CURRENT CONDITION</div>
                    <div class="battery-dashboard">
                        <div class="battery-ring" style="--health:{current}">
                            <div class="battery-ring-content">
                                <div class="battery-ring-value">{current}%</div>
                                <div class="battery-ring-label">BATTERY HEALTH</div>
                            </div>
                        </div>
                    </div>
                    <div style="text-align:center;margin-top:-8px;">
                        <span class="badge {badge}">{status}</span>
                    </div>
                    <p class="health-text">Based on the latest available telemetry reading.</p>
                </div>

                <div class="panel">
                    <div class="section-kicker">LIVE BATTERY METRICS</div>
                    <h2 class="panel-title">Battery Performance</h2>
                    <div class="metric-list">
                        <div class="metric-row">
                            <div><span class="metric-row-icon metric-temp"></span><span>Temperature</span></div>
                            <strong>{latest_temp:.1f}°C</strong>
                        </div>
                        <div class="metric-row">
                            <div><span class="metric-row-icon metric-power"></span><span>Power Consumption</span></div>
                            <strong>{latest_power:.1f} kW</strong>
                        </div>
                        <div class="metric-row">
                            <div><span class="metric-row-icon metric-health"></span><span>Average Health</span></div>
                            <strong>{avg_health}%</strong>
                        </div>
                        <div class="metric-row">
                            <div><span class="metric-row-icon metric-samples"></span><span>Telemetry Samples</span></div>
                            <strong>{len(data)}</strong>
                        </div>
                    </div>
                </div>
            </div>

            <div class="panel trend-panel">
                <div class="panel-heading-row">
                    <div>
                        <div class="section-kicker">HEALTH HISTORY</div>
                        <h2 class="panel-title">Battery Health Trend</h2>
                        <div class="panel-subtitle">Latest {len(data)} telemetry samples</div>
                    </div>
                    <div class="trend-legend"><span></span> Health Score</div>
                </div>

                <svg class="graph large-graph" viewBox="0 0 440 260" preserveAspectRatio="none">
                    <line x1="25" y1="45" x2="415" y2="45" stroke="#1d3a2d" />
                    <line x1="25" y1="132" x2="415" y2="132" stroke="#1d3a2d" />
                    <line x1="25" y1="220" x2="415" y2="220" stroke="#1d3a2d" />
                    <text x="2" y="49" fill="#789087" font-size="10">100</text>
                    <text x="7" y="136" fill="#789087" font-size="10">50</text>
                    <text x="12" y="224" fill="#789087" font-size="10">0</text>
                    <polyline points="{graph_points}" fill="none" stroke="#34d399" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
            </div>

            <div class="two-col">
                <div class="panel ai-panel">
                    <div class="section-kicker ai-accent">AI INSIGHT</div>
                    <h2 class="panel-title">Predictive Battery Insight</h2>
                    <p class="insight-text">
                        The current battery health is <strong>{current}%</strong> and the latest
                        telemetry reports <strong>{latest_temp:.1f}°C</strong> temperature with
                        <strong>{latest_power:.1f} kW</strong> power consumption.
                    </p>
                    <a href="/predictions" class="ai-btn">Open AI Predictions →</a>
                </div>

                <div class="panel">
                    <div class="section-kicker">HEALTH THRESHOLDS</div>
                    <h2 class="panel-title">Status Guide</h2>
                    <div class="thresholds">
                        <div><span class="threshold-dot good"></span><b>80–100%</b><span>Healthy</span></div>
                        <div><span class="threshold-dot warning"></span><b>60–79%</b><span>Moderate</span></div>
                        <div><span class="threshold-dot danger"></span><b>Below 60%</b><span>Critical</span></div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


# =========================================================
# LOGOUT
# =========================================================


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(debug=True, port=5000)
