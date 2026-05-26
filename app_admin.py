from flask import Flask, jsonify, render_template_string, request, session, redirect
from database import muracietleri_al, status_yenile, statistika_al
from ai_service import ai_analiz, ai_foto_analiz, get_weather
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "bytegov2025gizli"

PHOTOS_DIR = "photos"
if not os.path.exists(PHOTOS_DIR):
    os.makedirs(PHOTOS_DIR)

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ByteGov — Giriş</title>
    <meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'Inter',sans-serif; background:linear-gradient(135deg,#1a1a2e,#16213e); min-height:100vh; display:flex; align-items:center; justify-content:center; }
        .card { background:white; border-radius:16px; padding:40px; width:360px; box-shadow:0 20px 60px rgba(0,0,0,0.3); }
        .logo { text-align:center; margin-bottom:28px; }
        .logo h1 { font-size:22px; font-weight:700; color:#1a1a2e; }
        .logo p { font-size:13px; color:#888; margin-top:4px; }
        .form-group { margin-bottom:16px; }
        label { display:block; font-size:12px; font-weight:600; color:#555; margin-bottom:6px; text-transform:uppercase; letter-spacing:0.5px; }
        input { width:100%; padding:11px 14px; border:1.5px solid #e0e0e0; border-radius:10px; font-size:14px; outline:none; transition:border-color 0.2s; }
        input:focus { border-color:#1a1a2e; }
        button { width:100%; padding:12px; background:linear-gradient(135deg,#1a1a2e,#16213e); color:white; border:none; border-radius:10px; font-size:14px; font-weight:600; cursor:pointer; margin-top:8px; }
        .error { background:#fde8e8; color:#e74c3c; padding:10px 14px; border-radius:8px; font-size:13px; margin-bottom:16px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">
            <h1>⚡ ByteGov</h1>
            <p>Nərimanov Rayon İdarəetmə Paneli</p>
        </div>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/login">
            <div class="form-group">
                <label>İstifadəçi adı</label>
                <input type="text" name="username" placeholder="admin" required>
            </div>
            <div class="form-group">
                <label>Şifrə</label>
                <input type="password" name="password" placeholder="••••••••" required>
            </div>
            <button type="submit">Daxil ol</button>
        </form>
    </div>
</body>
</html>
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ByteGov Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #f0f2f5; color: #1a1a2e; }
        .header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 16px 28px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 12px rgba(0,0,0,0.15); }
        .header h1 { font-size: 18px; font-weight: 600; }
        .tabs-nav { display: flex; gap: 10px; }
        .tab-btn { background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: rgba(255, 255, 255, 0.8); padding: 8px 18px; border-radius: 20px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.25s ease; }
        .tab-btn:hover { background: rgba(255, 255, 255, 0.18); color: white; }
        .tab-btn.active { background: #3498db; border-color: #3498db; color: white; box-shadow: 0 0 12px rgba(52, 152, 219, 0.4); }
        .hidden { display: none !important; }
        .header-right { display:flex; align-items:center; gap:12px; }
        .live { display: flex; align-items: center; gap: 8px; font-size: 13px; opacity: 0.85; }
        .dot { width: 8px; height: 8px; background: #2ecc71; border-radius: 50%; animation: pulse 1.5s infinite; }
        .cixis-btn { font-size:12px; color:rgba(255,255,255,0.7); text-decoration:none; padding:5px 12px; border:1px solid rgba(255,255,255,0.3); border-radius:20px; transition:all 0.2s; cursor:pointer; background:transparent; }
        .cixis-btn:hover { background:rgba(255,255,255,0.1); color:white; }
        @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.8)} }

        /* Hava widget */
        .hava-widget { display:flex; align-items:center; gap:8px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); border-radius:20px; padding:5px 14px; font-size:13px; color:white; }
        .hava-widget .hava-icon { font-size:18px; }
        .hava-widget .hava-temp { font-weight:700; font-size:15px; }
        .hava-widget .hava-info { font-size:11px; opacity:0.75; line-height:1.3; }
        .hava-widget.xeberdarliq { border-color:#f39c12; background:rgba(243,156,18,0.15); }
        .hava-widget.tecili { border-color:#e74c3c; background:rgba(231,76,60,0.15); animation: hava-pulse 2s infinite; }
        @keyframes hava-pulse { 0%,100%{box-shadow:0 0 0 0 rgba(231,76,60,0.4)} 50%{box-shadow:0 0 0 6px rgba(231,76,60,0)} }

        .stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; padding: 20px 28px 0; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
        .stat-card { background: white; border-radius: 12px; padding: 18px 20px; display: flex; align-items: center; gap: 14px; box-shadow: 0 1px 8px rgba(0,0,0,0.06); border-left: 4px solid transparent; transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-2px); }
        .stat-card.umumi { border-color: #3498db; }
        .stat-card.tecili { border-color: #e74c3c; }
        .stat-card.normal { border-color: #f39c12; }
        .stat-card.asagi  { border-color: #2ecc71; }
        .stat-card.hell   { border-color: #2ecc71; }
        .stat-card.faiz   { border-color: #f1c40f; }
        .stat-icon { font-size: 28px; }
        .stat-info .number { font-size: 28px; font-weight: 700; line-height: 1; }
        .stat-info .label { font-size: 12px; color: #888; margin-top: 3px; }
        .stat-card.umumi .number { color: #3498db; }
        .stat-card.tecili .number { color: #e74c3c; }
        .stat-card.normal .number { color: #f39c12; }
        .stat-card.asagi  .number { color: #2ecc71; }
        .stat-card.hell   .number { color: #2ecc71; }
        .stat-card.faiz   .number { color: #f1c40f; }
        .controls { display: flex; align-items: center; gap: 10px; padding: 14px 28px 0; flex-wrap: wrap; }
        .filter-btn { padding: 7px 16px; border-radius: 20px; border: 1.5px solid transparent; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; background: white; display: flex; align-items: center; gap: 6px; }
        .filter-btn.all   { border-color: #3498db; color: #3498db; }
        .filter-btn.su    { border-color: #2980b9; color: #2980b9; }
        .filter-btn.isiq  { border-color: #f39c12; color: #f39c12; }
        .filter-btn.yol   { border-color: #27ae60; color: #27ae60; }
        .filter-btn.zibil { border-color: #8e44ad; color: #8e44ad; }
        .filter-btn.active { color: white !important; }
        .filter-btn.all.active   { background: #3498db; border-color: #3498db; }
        .filter-btn.su.active    { background: #2980b9; border-color: #2980b9; }
        .filter-btn.isiq.active  { background: #f39c12; border-color: #f39c12; }
        .filter-btn.yol.active   { background: #27ae60; border-color: #27ae60; }
        .filter-btn.zibil.active { background: #8e44ad; border-color: #8e44ad; }
        .divider { width: 1px; height: 28px; background: #e0e0e0; margin: 0 4px; }
        .search-input { padding: 7px 16px; border-radius: 20px; border: 1.5px solid #e0e0e0; font-size: 13px; outline: none; min-width: 200px; background: white; transition: border-color 0.2s; }
        .search-input:focus { border-color: #3498db; }
        .status-select { padding: 7px 14px; border-radius: 20px; border: 1.5px solid #e0e0e0; font-size: 13px; outline: none; background: white; cursor: pointer; }
        .map-wrap { margin: 14px 28px; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 8px rgba(0,0,0,0.08); }
        #map { height: 380px; }
        .table-section { margin: 14px 28px 28px; }
        .table-section h2 { font-size: 14px; font-weight: 600; color: #555; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
        .table-wrap { background: white; border-radius: 12px; box-shadow: 0 1px 8px rgba(0,0,0,0.06); overflow: hidden; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #1a1a2e; color: white; padding: 11px 16px; text-align: left; font-size: 11px; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; }
        td { padding: 11px 16px; font-size: 13px; color: #444; border-bottom: 1px solid #f5f5f5; }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: #fafbff; }
        .badge { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
        .badge-TECILI { background: #fde8e8; color: #e74c3c; }
        .badge-NORMAL { background: #fef3e2; color: #f39c12; }
        .badge-ASAGI  { background: #e8f8f0; color: #27ae60; }
        .row-select { padding: 4px 10px; border-radius: 8px; border: 1px solid #e0e0e0; font-size: 12px; cursor: pointer; background: white; outline: none; }
        .container { padding: 20px 28px; max-width: 1400px; margin: 0 auto; }
        .dss-card { background: linear-gradient(135deg, #ffffff 0%, #fbfcfe 100%); border-radius: 12px; padding: 20px; box-shadow: 0 1px 8px rgba(0,0,0,0.06); border: 1px solid rgba(52, 152, 219, 0.15); margin-bottom: 24px; display: flex; flex-direction: column; gap: 16px; }
        .dss-header { display: flex; align-items: center; gap: 12px; }
        .dss-icon { font-size: 22px; background: rgba(52, 152, 219, 0.1); width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 8px; }
        .dss-title { font-size: 15px; font-weight: 700; color: #1a1a2e; }
        .dss-body { display: grid; grid-template-columns: 1fr 1.5fr; gap: 20px; }
        .dss-metrics { display: flex; gap: 14px; }
        .dss-metric-box { flex: 1; background: #f8fafc; border-radius: 10px; padding: 14px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; justify-content: center; }
        .dss-metric-box.hotspot { border-left: 4px solid #e74c3c; }
        .dss-metric-box.time { border-left: 4px solid #3498db; }
        .dss-metric-lbl { font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 4px; }
        .dss-metric-val { font-size: 15px; font-weight: 700; color: #1e293b; line-height: 1.2; }
        .dss-metric-sub { font-size: 11px; color: #94a3b8; margin-top: 3px; }
        .dss-recommendation { background: linear-gradient(135deg, rgba(52, 152, 219, 0.04) 0%, rgba(52, 152, 219, 0.01) 100%); border-radius: 10px; padding: 16px; border: 1px solid rgba(52, 152, 219, 0.08); position: relative; display: flex; flex-direction: column; justify-content: center; }
        .dss-rec-badge { position: absolute; top: -9px; left: 14px; background: #3498db; color: white; font-size: 9px; font-weight: 700; text-transform: uppercase; padding: 1px 8px; border-radius: 20px; letter-spacing: 0.5px; box-shadow: 0 2px 5px rgba(52, 152, 219, 0.2); }
        .dss-recommendation p { font-size: 13px; line-height: 1.5; color: #334155; }
        .charts-grid-top { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 20px; }
        .charts-grid-bottom { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .chart-card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 8px rgba(0,0,0,0.06); display: flex; flex-direction: column; }
        .chart-card h3 { font-size: 13px; font-weight: 600; margin-bottom: 16px; color: #555; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1.5px solid #f1f2f6; padding-bottom: 8px; }
        .chart-container { position: relative; width: 100%; height: 260px; display: flex; align-items: center; justify-content: center; }
        @media (max-width: 1024px) { .charts-grid-top, .charts-grid-bottom { grid-template-columns: 1fr; } .dss-body { grid-template-columns: 1fr; } }
        @media (max-width: 768px) { .stats { grid-template-columns: repeat(2, 1fr); } .stats-grid { grid-template-columns: repeat(2, 1fr); } }
        .emergency-banner { position: fixed; top: 24px; left: 50%; transform: translateX(-50%) translateY(-150px); z-index: 99999; background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 16px 28px; border-radius: 16px; box-shadow: 0 12px 40px rgba(231, 76, 60, 0.4); display: flex; align-items: center; gap: 20px; font-weight: 500; transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); border: 2px solid rgba(255, 255, 255, 0.25); backdrop-filter: blur(10px); min-width: 480px; max-width: 90%; }
        .emergency-banner.show { transform: translateX(-50%) translateY(0); }
        .emergency-banner-pulse { animation: alert-pulse 1.8s infinite ease-in-out; }
        @keyframes alert-pulse { 0% { transform: translateX(-50%) translateY(0) scale(1); box-shadow: 0 12px 40px rgba(231, 76, 60, 0.4); } 50% { transform: translateX(-50%) translateY(-4px) scale(1.02); box-shadow: 0 16px 50px rgba(231, 76, 60, 0.7); } 100% { transform: translateX(-50%) translateY(0) scale(1); box-shadow: 0 12px 40px rgba(231, 76, 60, 0.4); } }
        .emergency-close-btn { background: rgba(255, 255, 255, 0.2); border: none; color: white; cursor: pointer; font-size: 13px; padding: 6px 14px; border-radius: 20px; font-weight: 600; transition: all 0.2s; white-space: nowrap; }
        .emergency-close-btn:hover { background: white; color: #e74c3c; transform: scale(1.05); }
        .emergency-content { flex: 1; font-size: 14px; line-height: 1.4; }
    </style>
</head>
<body>

<div id="emergency-alert-banner" class="emergency-banner hidden">
    <div class="emergency-content" id="emergency-alert-msg">🚨 <b>TƏCİLİ MÜRACİƏT:</b> Su sızması</div>
    <button class="emergency-close-btn" onclick="hideEmergencyBanner()">Bağla</button>
</div>

<div class="header">
    <h1>⚡ ByteGov — Nərimanov Rayon İdarəetmə Paneli</h1>
    <div class="tabs-nav">
        <button class="tab-btn active" onclick="switchTab('xəritə')">🗺️ Xəritə və Müraciətlər</button>
        <button class="tab-btn" onclick="switchTab('statistika')">📊 Qərar Dəstəyi və Analitika</button>
    </div>
    <div class="header-right">
        <div id="hava-widget" class="hava-widget">
            <span class="hava-icon">⏳</span>
            <div>
                <div class="hava-temp" id="hava-temp">--°C</div>
                <div class="hava-info" id="hava-info">Yüklənir...</div>
            </div>
        </div>
        <div class="live"><div class="dot"></div> Canlı izləmə</div>
        <button onclick="testEmergencyAlert()" class="cixis-btn" style="background:#e74c3c; border-color:#e74c3c; color:white; font-weight:600;">🚨 Test Siqnalı</button>
        <a href="/cixis" class="cixis-btn">Çıxış</a>
    </div>
</div>

<!-- TAB 1 -->
<div id="tab-xəritə" class="tab-content">
    <div class="stats">
        <div class="stat-card umumi"><div class="stat-icon">📋</div><div class="stat-info"><div class="number" id="umumi">0</div><div class="label">Ümumi Müraciət</div></div></div>
        <div class="stat-card tecili"><div class="stat-icon">🔴</div><div class="stat-info"><div class="number" id="tecili">0</div><div class="label">Təcili</div></div></div>
        <div class="stat-card normal"><div class="stat-icon">🟡</div><div class="stat-info"><div class="number" id="normal">0</div><div class="label">Normal</div></div></div>
        <div class="stat-card asagi"><div class="stat-icon">🟢</div><div class="stat-info"><div class="number" id="asagi">0</div><div class="label">Aşağı</div></div></div>
    </div>
    <div class="controls">
        <button class="filter-btn all active" onclick="filterNov('HAMISI', this)">Hamısı</button>
        <button class="filter-btn su"    onclick="filterNov('Su problemi', this)">💧 Su</button>
        <button class="filter-btn isiq"  onclick="filterNov('Isiq problemi', this)">💡 İşıq</button>
        <button class="filter-btn yol"   onclick="filterNov('Yol problemi', this)">🛣️ Yol</button>
        <button class="filter-btn zibil" onclick="filterNov('Zibil problemi', this)">🗑️ Zibil</button>
        <div class="divider"></div>
        <input class="search-input" id="axtar" type="text" placeholder="🔍 Aciqlamada axtar..." oninput="axtar()">
        <select class="status-select" id="status-filter" onchange="axtar()">
            <option value="">Bütün statuslar</option>
            <option value="YENI">Yeni</option>
            <option value="ISLENILIR">İşlənilir</option>
            <option value="HELL_EDILDI">Həll edildi</option>
        </select>
    </div>
    <div class="map-wrap"><div id="map"></div></div>
    <div class="table-section">
        <h2>Son Müraciətlər</h2>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr><th>No</th><th>Növ</th><th>Acıqlama</th><th>Prioritet</th><th>Mesul Şöbə</th><th>Tarix</th><th>Foto</th><th>Status</th><th>Əməliyyat</th></tr>
                </thead>
                <tbody id="table-body"></tbody>
            </table>
        </div>
    </div>
</div>

<!-- TAB 2 -->
<div id="tab-statistika" class="tab-content hidden">
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card umumi"><div class="stat-icon">📋</div><div class="stat-info"><span class="number" id="card-umumi">0</span><span class="label">Ümumi Müraciət</span></div></div>
            <div class="stat-card tecili"><div class="stat-icon">🚨</div><div class="stat-info"><span class="number" id="card-tecili">0</span><span class="label">Təcili Şikayətlər</span></div></div>
            <div class="stat-card hell"><div class="stat-icon">✅</div><div class="stat-info"><span class="number" id="card-hell">0</span><span class="label">Həll Olunanlar</span></div></div>
            <div class="stat-card faiz"><div class="stat-icon">📈</div><div class="stat-info"><span class="number" id="card-faiz">0%</span><span class="label">Həllolunma Nisbəti</span></div></div>
        </div>
        <div class="dss-card">
            <div class="dss-header">
                <span class="dss-icon">🧠</span>
                <div class="dss-title">Qərar Dəstək Sistemi (DSS) və AI Analitikası</div>
            </div>
            <div class="dss-body">
                <div class="dss-metrics">
                    <div class="dss-metric-box hotspot">
                        <span class="dss-metric-lbl">🚨 Ən Problemli Ərazi</span>
                        <span class="dss-metric-val" id="dss-hotspot">Məlumat yoxdur</span>
                        <span class="dss-metric-sub" id="dss-hotspot-count">0 şikayət</span>
                    </div>
                    <div class="dss-metric-box time">
                        <span class="dss-metric-lbl">⏱️ Ort. Həll Müddəti</span>
                        <span class="dss-metric-val" id="dss-avg-time">0 saat</span>
                        <span class="dss-metric-sub">Sürətli müdaxilə</span>
                    </div>
                </div>
                <div class="dss-recommendation">
                    <div class="dss-rec-badge">Süni İntellekt Rəyi</div>
                    <p id="dss-tovsiye">Hesablanır...</p>
                </div>
            </div>
        </div>
        <div class="charts-grid-top">
            <div class="chart-card"><h3>📈 Son Müraciət Dinamikası</h3><div class="chart-container"><canvas id="timelineChart"></canvas></div></div>
            <div class="chart-card"><h3>⚡ Prioritet bölgüsü</h3><div class="chart-container"><canvas id="priorityChart"></canvas></div></div>
        </div>
        <div class="charts-grid-bottom">
            <div class="chart-card"><h3>💧 Kateqoriyalar Üzrə Müraciətlər</h3><div class="chart-container"><canvas id="categoryChart"></canvas></div></div>
            <div class="chart-card"><h3>⚙️ Müraciətlərin Statusları</h3><div class="chart-container"><canvas id="statusChart"></canvas></div></div>
        </div>
    </div>
</div>

<script>
    const map = L.map('map').setView([40.4069, 49.8694], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '© OpenStreetMap'}).addTo(map);

    let butunData = [];
    let activNov = 'HAMISI';
    let timelineChart = null, priorityChart = null, categoryChart = null, statusChart = null;
    const notifiedTeciliIds = new Set();
    let audioCtx = null;

    // Hava məlumatını yüklə
    function loadHava() {
        fetch('/api/hava')
            .then(r => r.json())
            .then(d => {
                const widget = document.getElementById('hava-widget');
                document.getElementById('hava-temp').textContent = d.temp + '°C';
                document.getElementById('hava-info').textContent = d.metn;

                // İkonu seç
                let ikon = '🌤️';
                if (d.yagis > 0.5) ikon = '🌧️';
                else if (d.kulak > 25) ikon = '💨';
                else if (d.temp < 2) ikon = '🥶';
                else if (d.temp > 32) ikon = '🥵';
                widget.querySelector('.hava-icon').textContent = ikon;

                // Risk səviyyəsinə görə rəng
                widget.className = 'hava-widget';
                if (d.risk === 'tecili') widget.classList.add('tecili');
                else if (d.risk === 'xeberdarliq') widget.classList.add('xeberdarliq');
            })
            .catch(() => {
                document.getElementById('hava-info').textContent = 'Məlumat yox';
            });
    }

    function playEmergencySound() {
        try {
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
            const now = audioCtx.currentTime;
            for (let i = 0; i < 4; i++) {
                const t = now + i * 0.35;
                const osc1 = audioCtx.createOscillator(); const g1 = audioCtx.createGain();
                osc1.type = 'sawtooth'; osc1.frequency.setValueAtTime(950, t); osc1.frequency.linearRampToValueAtTime(1050, t+0.15);
                g1.gain.setValueAtTime(0.15, t); g1.gain.exponentialRampToValueAtTime(0.001, t+0.18);
                osc1.connect(g1); g1.connect(audioCtx.destination); osc1.start(t); osc1.stop(t+0.2);
                const t2 = t+0.18; const osc2 = audioCtx.createOscillator(); const g2 = audioCtx.createGain();
                osc2.type = 'sawtooth'; osc2.frequency.setValueAtTime(750, t2); osc2.frequency.linearRampToValueAtTime(850, t2+0.15);
                g2.gain.setValueAtTime(0.15, t2); g2.gain.exponentialRampToValueAtTime(0.001, t2+0.18);
                osc2.connect(g2); g2.connect(audioCtx.destination); osc2.start(t2); osc2.stop(t2+0.2);
            }
        } catch(e) {}
    }

    function showEmergencyBanner(d) {
        const banner = document.getElementById('emergency-alert-banner');
        document.getElementById('emergency-alert-msg').innerHTML = `🚨 <b>TƏCİLİ MÜRACİƏT #${d.id}</b>: <u>${d.nov}</u> - <i>"${d.aciqla}"</i>`;
        banner.classList.remove('hidden'); banner.offsetHeight;
        banner.classList.add('show', 'emergency-banner-pulse');
        playEmergencySound();
    }

    function hideEmergencyBanner() {
        const banner = document.getElementById('emergency-alert-banner');
        banner.classList.remove('emergency-banner-pulse', 'show');
        setTimeout(() => banner.classList.add('hidden'), 500);
    }

    function testEmergencyAlert() {
        showEmergencyBanner({id:999, nov:"Su sızması (Test)", aciqla:"Ağa Nemətulla küçəsi, bina 12 ünvanında magistral boru partlayıb!"});
    }

    function renderTable(data) {
        const tbody = document.getElementById('table-body');
        tbody.innerHTML = '';
        if (!data.length) { tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:24px;color:#aaa">Müraciət tapılmadı</td></tr>'; return; }
        data.forEach(d => {
            tbody.innerHTML += `<tr>
                <td><b>#${d.id}</b></td><td>${d.nov}</td><td>${d.aciqla}</td>
                <td><span class="badge badge-${d.prioritet}">${d.prioritet}</span></td>
                <td>${d.mesul_sobe}</td><td>${d.tarix||'-'}</td>
                <td>${d.foto_yol?'<a href="/foto/'+d.id+'" target="_blank" style="color:#3498db">Foto Bax</a>':'-'}</td>
                <td><span class="badge" style="background:#eaf4ff;color:#3498db">${d.status}</span></td>
                <td style="display:flex;gap:6px;align-items:center;">
                    <select class="row-select" onchange="statusDeyis(${d.id},this.value)">
                        <option ${d.status==='YENI'?'selected':''}>YENI</option>
                        <option ${d.status==='ISLENILIR'?'selected':''}>ISLENILIR</option>
                        <option ${d.status==='HELL_EDILDI'?'selected':''}>HELL_EDILDI</option>
                    </select>
                    <button onclick="muracietSil(${d.id})" style="background:#fde8e8;border:1px solid #e74c3c;color:#e74c3c;border-radius:8px;padding:4px 10px;cursor:pointer;font-size:12px;font-weight:600;">🗑 Sil</button>
                </td>
            </tr>`;
        });
    }

    function renderMap(data) {
        map.eachLayer(l => { if (l instanceof L.CircleMarker) map.removeLayer(l); });
        data.forEach(d => {
            const color = d.prioritet==='TECILI'?'#e74c3c':d.prioritet==='NORMAL'?'#f39c12':'#2ecc71';
            L.circleMarker([d.lat,d.lon],{radius:10,color,fillColor:color,fillOpacity:0.75,weight:2})
             .addTo(map).bindPopup(`<b>${d.nov}</b><br>${d.aciqla}<br><b style="color:${color}">${d.prioritet}</b><br><small>${d.mesul_sobe}</small>`);
        });
    }

    function getFiltered() {
        const metn = document.getElementById('axtar').value.toLowerCase();
        const status = document.getElementById('status-filter').value;
        return butunData.filter(d => {
            return (activNov==='HAMISI'||d.nov===activNov) &&
                   (metn===''||d.aciqla.toLowerCase().includes(metn)) &&
                   (status===''||d.status===status);
        });
    }

    function filterNov(nov, btn) {
        activNov = nov;
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const f = getFiltered(); renderTable(f); renderMap(f);
    }

    function axtar() { const f = getFiltered(); renderTable(f); renderMap(f); }

    function statusDeyis(id, yeniStatus) {
        fetch('/api/status_yenile', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id,status:yeniStatus})})
        .then(() => { refreshData(); loadStatistika(); });
    }

    function muracietSil(id) {
        if (!confirm('#'+id+' nömrəli müraciəti silmək istədiyinizdən əminsiniz?')) return;
        fetch('/api/muraciet_sil', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id})})
        .then(r=>r.json()).then(d => { if(d.ok) refreshData(); });
    }

    function refreshData() {
        fetch('/api/muracietler').then(r=>r.json()).then(data => {
            butunData = data;
            document.getElementById('umumi').textContent = data.length;
            document.getElementById('tecili').textContent = data.filter(d=>d.prioritet==='TECILI').length;
            document.getElementById('normal').textContent = data.filter(d=>d.prioritet==='NORMAL').length;
            document.getElementById('asagi').textContent = data.filter(d=>d.prioritet==='ASAGI').length;
            const f = getFiltered(); renderTable(f); renderMap(f);
            data.forEach(d => {
                if (d.prioritet==='TECILI' && d.status==='YENI' && !notifiedTeciliIds.has(d.id)) {
                    notifiedTeciliIds.add(d.id);
                    showEmergencyBanner(d);
                }
            });
        });
    }

    function switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        if (tabName==='xəritə') {
            document.querySelector('.tab-btn[onclick*="xəritə"]').classList.add('active');
            document.getElementById('tab-xəritə').classList.remove('hidden');
            document.getElementById('tab-statistika').classList.add('hidden');
            setTimeout(() => map.invalidateSize(), 100);
        } else {
            document.querySelector('.tab-btn[onclick*="statistika"]').classList.add('active');
            document.getElementById('tab-xəritə').classList.add('hidden');
            document.getElementById('tab-statistika').classList.remove('hidden');
            loadStatistika();
        }
    }

    function loadStatistika() {
        fetch('/api/statistika').then(r=>r.json()).then(data => {
            const umumi = Object.values(data.nov).reduce((a,b)=>a+b,0);
            const tecili = data.prioritet['TECILI']||0;
            const hell = data.status['HELL_EDILDI']||0;
            const faiz = umumi>0?Math.round(hell/umumi*100):0;
            document.getElementById('card-umumi').textContent = umumi;
            document.getElementById('card-tecili').textContent = tecili;
            document.getElementById('card-hell').textContent = hell;
            document.getElementById('card-faiz').textContent = faiz+'%';
            document.getElementById('dss-hotspot').textContent = data.top_mehelle;
            document.getElementById('dss-hotspot-count').textContent = data.top_mehelle_count+' müraciət';
            document.getElementById('dss-avg-time').textContent = data.avg_resolution_time+' saat';
            document.getElementById('dss-tovsiye').innerHTML = data.tovsiye;
            renderCharts(data);
        });
    }

    function renderCharts(data) {
        const tCtx = document.getElementById('timelineChart').getContext('2d');
        if (timelineChart) timelineChart.destroy();
        timelineChart = new Chart(tCtx, {type:'line', data:{labels:data.dinamika.map(d=>d.tarix), datasets:[{label:'Müraciət sayı', data:data.dinamika.map(d=>d.say), borderColor:'#3498db', backgroundColor:'rgba(52,152,219,0.08)', borderWidth:2.5, fill:true, tension:0.35}]}, options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true, ticks:{stepSize:1}}}}});

        const pCtx = document.getElementById('priorityChart').getContext('2d');
        if (priorityChart) priorityChart.destroy();
        priorityChart = new Chart(pCtx, {type:'bar', data:{labels:['Təcili','Normal','Aşağı'], datasets:[{data:[data.prioritet['TECILI']||0, data.prioritet['NORMAL']||0, data.prioritet['ASAGI']||0], backgroundColor:['#e74c3c','#f39c12','#2ecc71'], borderRadius:5}]}, options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true, ticks:{stepSize:1}}}}});

        const cCtx = document.getElementById('categoryChart').getContext('2d');
        if (categoryChart) categoryChart.destroy();
        categoryChart = new Chart(cCtx, {type:'doughnut', data:{labels:Object.keys(data.nov), datasets:[{data:Object.values(data.nov), backgroundColor:['#2980b9','#f39c12','#27ae60','#8e44ad','#7f8c8d']}]}, options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'bottom', labels:{boxWidth:12, padding:10}}}}});

        const sCtx = document.getElementById('statusChart').getContext('2d');
        if (statusChart) statusChart.destroy();
        statusChart = new Chart(sCtx, {type:'pie', data:{labels:['Yeni','İşlənilir','Həll Edildi'], datasets:[{data:[data.status['YENI']||0, data.status['ISLENILIR']||0, data.status['HELL_EDILDI']||0], backgroundColor:['#3498db','#f1c40f','#2ecc71']}]}, options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'bottom', labels:{boxWidth:12, padding:10}}}}});
    }

    refreshData();
    loadHava();
    setInterval(refreshData, 3000);
    setInterval(loadHava, 300000); // Hava hər 5 dəqiqədən bir yenilənir
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return redirect("/admin")

@app.route("/admin")
def admin_dashboard():
    if not session.get("giris"):
        return redirect("/giris")
    return render_template_string(HTML)

@app.route("/giris")
def giris():
    return render_template_string(LOGIN_HTML, error=None)

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    if username == "admin" and password == "bytegov2025gizli":
        session["giris"] = True
        return redirect("/admin")
    return render_template_string(LOGIN_HTML, error="İstifadəçi adı və ya şifrə yanlışdır!")

@app.route("/cixis")
def cixis():
    session.clear()
    return redirect("/")

@app.route("/api/hava")
def api_hava():
    if not session.get("giris"):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        import httpx
        url = "https://api.open-meteo.com/v1/forecast?latitude=40.4093&longitude=49.8671&current=temperature_2m,precipitation,wind_speed_10m,weather_code&timezone=auto"
        res = httpx.get(url, timeout=5)
        curr = res.json().get("current", {})
        temp = curr.get("temperature_2m", 0)
        yagis = curr.get("precipitation", 0)
        kulak = curr.get("wind_speed_10m", 0)
        wcode = curr.get("weather_code", 0)

        durum = []
        if yagis > 0.5: durum.append(f"Yağış {yagis}mm")
        if kulak > 25: durum.append(f"Güclü külək {round(kulak)}km/s")
        if wcode in range(95, 100): durum.append("Fırtına")
        metn = ", ".join(durum) if durum else f"Külək: {round(kulak)}km/s"

        # Risk səviyyəsi
        risk = "normal"
        if wcode in range(95, 100) or (yagis > 2 and kulak > 20):
            risk = "tecili"
        elif yagis > 0.5 or kulak > 25 or temp < 2:
            risk = "xeberdarliq"

        return jsonify({"temp": round(temp, 1), "yagis": yagis, "kulak": round(kulak), "metn": metn, "risk": risk})
    except Exception as e:
        return jsonify({"temp": "--", "yagis": 0, "kulak": 0, "metn": "Məlumat alınmadı", "risk": "normal"})

@app.route("/api/muracietler")
def api_muracietler():
    if not session.get("giris"):
        return jsonify({"error": "Unauthorized"}), 401
    rows = muracietleri_al()
    result = []
    for r in rows:
        if r[7] is None or r[8] is None:
            continue
        result.append({"id":r[0],"user_id":r[1],"nov":r[2],"aciqla":r[3],"prioritet":r[4],"mesul_sobe":r[5],"xulase":r[6],"lat":r[7],"lon":r[8],"tarix":r[9],"status":r[10],"foto_yol":r[11] if len(r)>11 else None})
    return jsonify(result)

@app.route("/api/status_yenile", methods=["POST"])
def api_status_yenile():
    if not session.get("giris"):
        return jsonify({"error": "Unauthorized"}), 401
    import httpx
    data = request.json
    muraciet_id = data["id"]
    yeni_status = data["status"]
    status_yenile(muraciet_id, yeni_status)
    rows = muracietleri_al()
    user_id = nov = aciqla = ""
    for r in rows:
        if r[0] == muraciet_id:
            user_id = r[1]; nov = r[2]; aciqla = r[3]; break
    if user_id and not user_id.startswith("WEB:"):
        mesajlar = {
            "ISLENILIR": f"Muracietiniz artiq islenilir.\n\nProbleminiz: {nov}\nAciqlamasi: {aciqla}\n\nTezlikle hell edilecek!",
            "HELL_EDILDI": f"Muracietiniz hell edildi!\n\nProbleminiz: {nov}\nAciqlamasi: {aciqla}\n\nTesekkurler!"
        }
        mesaj = mesajlar.get(yeni_status)
        if mesaj:
            try:
                httpx.post("http://127.0.0.1:5001/send_message", json={"user_id":user_id,"message":mesaj}, timeout=5)
            except: pass
    return jsonify({"ok": True})

@app.route("/foto/<int:muraciet_id>")
def get_foto(muraciet_id):
    if not session.get("giris"):
        return redirect("/giris")
    from flask import send_from_directory
    rows = muracietleri_al()
    for r in rows:
        if r[0] == muraciet_id:
            foto_yol = r[11] if len(r) > 11 else None
            if foto_yol:
                dirname, filename = os.path.split(foto_yol)
                return send_from_directory(os.path.abspath(dirname), filename)
            break
    return "Fotoğraf bulunamadı", 404

@app.route("/api/muraciet_sil", methods=["POST"])
def api_muraciet_sil():
    if not session.get("giris"):
        return jsonify({"error": "Unauthorized"}), 401
    from database import muraciet_sil
    data = request.json
    muraciet_sil(data["id"], eden_user="admin")
    return jsonify({"ok": True})

@app.route("/api/statistika")
def api_statistika():
    if not session.get("giris"):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(statistika_al())

if __name__ == "__main__":
    app.run(debug=True, port=5002)
