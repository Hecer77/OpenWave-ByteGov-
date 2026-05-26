from flask import Flask, jsonify, render_template_string, request, session, redirect
from database import muracietleri_al, status_yenile, statistika_al
from ai_service import ai_analiz, ai_foto_analiz
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

LANDING_HTML = """
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ByteGov — Nərimanov Rayon Vətəndaş Portalı</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --accent: #10b981;
            --dark-bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border: rgba(255, 255, 255, 0.08);
            --text: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: radial-gradient(circle at top right, #1e1b4b 0%, #0f172a 60%, #020617 100%);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }
        .glow {
            position: absolute;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, rgba(0,0,0,0) 70%);
            top: 10%;
            left: 10%;
            pointer-events: none;
            z-index: 1;
        }
        .glow-right {
            position: absolute;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, rgba(0,0,0,0) 70%);
            bottom: 10%;
            right: 5%;
            pointer-events: none;
            z-index: 1;
        }
        header {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 10;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .logo span { font-size: 26px; -webkit-text-fill-color: initial; }
        .admin-link {
            text-decoration: none;
            color: var(--text-muted);
            font-size: 14px;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 20px;
            border: 1px solid var(--border);
            background: rgba(255, 255, 255, 0.03);
            transition: all 0.25s ease;
        }
        .admin-link:hover {
            color: var(--text);
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }
        main {
            flex: 1;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 24px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            z-index: 10;
        }
        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(59, 130, 246, 0.1);
            border: 1.5px solid rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 24px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
            70% { transform: scale(1.02); box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
        }
        h1 {
            font-size: 54px;
            font-weight: 800;
            line-height: 1.15;
            letter-spacing: -1.5px;
            margin-bottom: 20px;
            max-width: 800px;
        }
        h1 span {
            background: linear-gradient(135deg, #a78bfa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero-desc {
            font-size: 18px;
            color: var(--text-muted);
            max-width: 600px;
            line-height: 1.6;
            margin-bottom: 40px;
        }
        .cta-group {
            display: flex;
            gap: 16px;
            margin-bottom: 60px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            font-weight: 700;
            font-size: 16px;
            padding: 16px 32px;
            border-radius: 14px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
        }
        .btn-primary {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
            box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.4);
            border: none;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 30px -5px rgba(59, 130, 246, 0.6);
            background: linear-gradient(135deg, #4f46e5, #3b82f6);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            width: 100%;
            max-width: 1000px;
            margin-top: 20px;
        }
        .stat-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            transition: all 0.25s ease;
        }
        .stat-card:hover {
            transform: translateY(-4px);
            border-color: rgba(59, 130, 246, 0.25);
            background: rgba(30, 41, 59, 0.85);
        }
        .stat-val {
            font-size: 32px;
            font-weight: 800;
            color: #fff;
            margin-bottom: 6px;
            background: linear-gradient(135deg, #ffffff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stat-card.resolved .stat-val {
            background: linear-gradient(135deg, #34d399, #10b981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stat-lbl {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .tracker-box {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            width: 100%;
            max-width: 500px;
            margin-top: 40px;
            backdrop-filter: blur(8px);
        }
        .tracker-title {
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #fff;
        }
        .tracker-form { display: flex; gap: 10px; }
        .tracker-input {
            flex: 1;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 10px 14px;
            color: white;
            font-size: 14px;
            outline: none;
            transition: all 0.2s;
        }
        .tracker-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }
        .tracker-btn {
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 18px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .tracker-btn:hover { background: var(--primary-hover); }
        footer {
            width: 100%;
            padding: 30px 24px;
            margin-top: auto;
            border-top: 1px solid var(--border);
            text-align: center;
            font-size: 13px;
            color: var(--text-muted);
            z-index: 10;
        }
        @media (max-width: 768px) {
            h1 { font-size: 38px; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
            .btn { width: 100%; justify-content: center; }
            .cta-group { width: 100%; flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="glow"></div>
    <div class="glow-right"></div>
    <header>
        <div class="logo"><span>⚡</span> ByteGov</div>
       
    </header>
    <main>
        <div class="hero-badge">⚡ Narimanov Smart City</div>
        <h1>Şəhərimizin İnkişafında <span>Söz Sahibi Olun</span></h1>
        <p class="hero-desc">
            Nərimanov rayonu sakini olaraq qarşılaşdığınız su, işıq, yol və ya təmizlik problemlərini saniyələr içində bizə bildirin. Süni İntellekt tərəfindən sürətli analiz və birbaşa aidiyyatı şöbəyə yönləndirmə ilə probleminiz tezliklə həll olunsun.
        </p>
        <div class="cta-group">
            <a href="/muraciet" class="btn btn-primary">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"/></svg>
                Yeni Müraciət Yarat
            </a>
        </div>
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-val">{{ umumi_say }}</span>
                <span class="stat-lbl">Ümumi Müraciət</span>
            </div>
            <div class="stat-card resolved">
                <span class="stat-val">{{ hell_say }}</span>
                <span class="stat-lbl">Həll Edilmiş</span>
            </div>
            <div class="stat-card">
                <span class="stat-val">{{ aktiv_say }}</span>
                <span class="stat-lbl">İcrada Olan</span>
            </div>
            <div class="stat-card">
                <span class="stat-val">{{ avg_time }}s</span>
                <span class="stat-lbl">Ortalama Həll Vaxtı</span>
            </div>
        </div>
        <div class="tracker-box">
            <div class="tracker-title">🔍 Müraciətin statusunu izləyin</div>
            <div class="tracker-form">
                <input type="number" id="muraciet-kod" placeholder="Məsələn: 12" class="tracker-input" required>
                <button onclick="trackRequest()" class="tracker-btn">Axtar</button>
            </div>
        </div>
    </main>
    <footer>
        © 2026 ByteGov Portal. Nərimanov Rayon İcra Hakimiyyəti Rəqəmsal Xidmətlər Şöbəsi.
    </footer>
    <script>
        function trackRequest() {
            const id = document.getElementById('muraciet-kod').value.trim();
            if (id) {
                window.location.href = '/izle/' + id;
            } else {
                alert('Zəhmət olmasa müraciət kodunu daxil edin.');
            }
        }
        document.getElementById('muraciet-kod').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') { trackRequest(); }
        });
    </script>
</body>
</html>
"""

MURACIET_HTML = """
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ByteGov — Yeni Müraciət</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        :root {
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --accent: #10b981;
            --bg: #0b0f19;
            --card-bg: rgba(22, 30, 49, 0.75);
            --border: rgba(255, 255, 255, 0.08);
            --text: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: radial-gradient(circle at bottom left, #1e1b4b 0%, #0b0f19 70%);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }
        header {
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            padding: 24px 16px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 20px;
            font-weight: 800;
            background: linear-gradient(135deg, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .logo span { -webkit-text-fill-color: initial; }
        .back-link {
            text-decoration: none;
            color: var(--text-muted);
            font-size: 14px;
            font-weight: 600;
            transition: color 0.2s;
        }
        .back-link:hover { color: white; }
        main {
            flex: 1;
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            padding: 30px 16px;
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 32px;
            width: 100%;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            backdrop-filter: blur(16px);
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        h2 { font-size: 24px; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.5px; }
        .subtitle { color: var(--text-muted); font-size: 14px; margin-bottom: 28px; line-height: 1.5; }
        .form-group { margin-bottom: 24px; }
        label { display: block; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #fff; margin-bottom: 10px; }
        .category-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
        .cat-btn {
            background: rgba(255, 255, 255, 0.03);
            border: 1.5px solid var(--border);
            border-radius: 14px;
            padding: 16px 12px;
            color: var(--text);
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            text-align: center;
        }
        .cat-btn .icon { font-size: 24px; }
        .cat-btn .name { font-size: 13px; font-weight: 600; }
        .cat-btn:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(59, 130, 246, 0.4);
            transform: translateY(-2px);
        }
        .cat-btn.active {
            background: rgba(59, 130, 246, 0.15);
            border-color: var(--primary);
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.25);
        }
        textarea {
            width: 100%;
            height: 110px;
            background: rgba(15, 23, 42, 0.6);
            border: 1.5px solid var(--border);
            border-radius: 14px;
            padding: 14px 18px;
            color: white;
            font-family: inherit;
            font-size: 14px;
            outline: none;
            resize: none;
            transition: border-color 0.2s;
            line-height: 1.5;
        }
        textarea:focus { border-color: var(--primary); }
        .char-count { text-align: right; font-size: 11px; color: var(--text-muted); margin-top: 6px; }
        .input-text {
            width: 100%;
            background: rgba(15, 23, 42, 0.6);
            border: 1.5px solid var(--border);
            border-radius: 14px;
            padding: 12px 18px;
            color: white;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        .input-text:focus { border-color: var(--primary); }
        .upload-area {
            border: 2px dashed var(--border);
            border-radius: 14px;
            padding: 24px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            background: rgba(15, 23, 42, 0.3);
            position: relative;
        }
        .upload-area:hover { border-color: var(--primary); background: rgba(15, 23, 42, 0.5); }
        .upload-area .upload-icon { font-size: 32px; margin-bottom: 8px; }
        .upload-area p { font-size: 13px; color: var(--text-muted); }
        .upload-area p strong { color: var(--primary); }
        #foto-preview { max-width: 100%; max-height: 160px; border-radius: 8px; margin-top: 12px; display: none; border: 1px solid var(--border); }
        .map-container { border-radius: 14px; overflow: hidden; border: 1px solid var(--border); margin-bottom: 12px; }
        #map { height: 250px; width: 100%; }
        .map-actions { display: flex; justify-content: space-between; align-items: center; }
        .btn-location {
            background: rgba(255,255,255,0.04);
            border: 1px solid var(--border);
            color: white;
            padding: 8px 14px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }
        .btn-location:hover { background: rgba(255,255,255,0.08); border-color: white; }
        .coordinate-info { font-size: 12px; color: var(--text-muted); font-family: monospace; }
        .submit-btn {
            width: 100%;
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
            border: none;
            border-radius: 14px;
            padding: 16px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.4);
            transition: all 0.25s;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
        }
        .submit-btn:hover { transform: translateY(-2px); box-shadow: 0 15px 30px -5px rgba(59, 130, 246, 0.6); }
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--bg);
            z-index: 100;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 32px;
            text-align: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }
        .loading-overlay.active { opacity: 1; pointer-events: all; }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(59,130,246,0.1);
            border-left-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading-title { font-size: 18px; font-weight: 700; margin-bottom: 8px; }
        .loading-desc { font-size: 13px; color: var(--text-muted); max-width: 250px; line-height: 1.5; }
        .status-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--bg);
            z-index: 101;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 32px;
            text-align: center;
            display: none;
        }
        .circle-icon {
            width: 72px;
            height: 72px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            margin-bottom: 24px;
        }
        .circle-success { background: rgba(16, 185, 129, 0.15); color: var(--accent); border: 2px solid var(--accent); }
        .circle-error { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 2px solid #ef4444; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase; margin: 10px 0; }
        .badge-TECILI { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge-NORMAL { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-ASAGI { background: rgba(16, 185, 129, 0.15); color: var(--accent); border: 1px solid rgba(16, 185, 129, 0.3); }
        .ai-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px;
            width: 100%;
            max-width: 400px;
            margin: 16px 0 24px;
            text-align: left;
        }
        .ai-title { font-size: 11px; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
        .ai-text { font-size: 13px; line-height: 1.4; color: #fff; }
        .overlay-actions { display: flex; gap: 12px; width: 100%; max-width: 400px; }
        .overlay-actions .btn { flex: 1; justify-content: center; }
        .btn-secondary { background: rgba(255, 255, 255, 0.04); color: var(--text); border: 1px solid var(--border); }
        .btn-secondary:hover { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.2); transform: translateY(-2px); }
        @media (max-width: 768px) {
            .category-grid { grid-template-columns: repeat(2, 1fr); }
            .card { padding: 20px; }
            .overlay-actions { flex-direction: column; }
        }
    </style>
</head>
<body>
    <header>
        <a href="/" class="logo"><span>⚡</span> ByteGov</a>
        <a href="/" class="back-link">➔ Əsas Səhifə</a>
    </header>
    <main>
        <div class="card">
            <div id="loading-overlay" class="loading-overlay">
                <div class="spinner"></div>
                <div class="loading-title">Müraciət Göndərilir...</div>
                <div class="loading-desc">Süni İntellekt mətni və yüklənən şəkili yoxlayır. Zəhmət olmasa bir neçə saniyə gözləyin.</div>
            </div>
            <div id="success-overlay" class="status-overlay">
                <div class="circle-icon circle-success">✓</div>
                <h2>Müraciətiniz Qəbul Edildi!</h2>
                <div class="subtitle" style="margin-bottom:12px;" id="success-id">Müraciət Kodu: #00</div>
                <div class="ai-card">
                    <div class="ai-title">🧠 Süni İntellekt Təsnifatı</div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-size:12px; color:var(--text-muted);" id="success-sobe">Məsul Şöbə: Yol Xidməti</span>
                        <span id="success-prioritet-badge" class="badge">NORMAL</span>
                    </div>
                    <div class="ai-title" style="margin-top:12px;">📝 Qısa Xülasə</div>
                    <p class="ai-text" id="success-xulase">Bilinməyən</p>
                </div>
                <div class="overlay-actions">
                    <button onclick="window.location.reload()" class="btn btn-secondary">Yeni Müraciət</button>
                    <a id="success-track-btn" href="#" class="btn btn-primary">Müraciəti İzlə</a>
                </div>
            </div>
            <div id="error-overlay" class="status-overlay">
                <div class="circle-icon circle-error">✗</div>
                <h2>Müraciət Rədd Edildi</h2>
                <div class="subtitle" id="error-msg">Səbəb göstərilməyib.</div>
                <div class="ai-card" style="border-color: rgba(239, 68, 68, 0.25);">
                    <div class="ai-title" style="color:#ef4444;">Niyə qəbul edilmədi?</div>
                    <p class="ai-text" style="color:var(--text-muted);">Sistem yalnız şəhər təsərrüfatı və kommunal problemlərini (su sızması, zibil yığılması, yol çuxurları, sıradan çıxmış işıqlar və s.) qəbul edir. Borc, şəxsi mülk daxili nasazlıqlar və digər qeyri-komunal şikayətlər qəbul olunmur.</p>
                </div>
                <div class="overlay-actions" style="max-width:200px;">
                    <button onclick="closeErrorOverlay()" class="btn btn-primary">Düzəliş Et</button>
                </div>
            </div>
            <h2>Müraciət Forması</h2>
            <p class="subtitle">Aşağıdakı formanı dolduraraq Nərimanov rayonu ərazisindəki kommunal və infrastruktur problemləri barədə birbaşa aidiyyatı şöbələrə məlumat göndərin.</p>
            <form id="muraciet-form" onsubmit="submitForm(event)">
                <input type="hidden" name="nov" id="nov-input" required>
                <input type="hidden" name="lat" id="lat-input" required>
                <input type="hidden" name="lon" id="lon-input" required>
                <div class="form-group">
                    <label>1. Problemin növü</label>
                    <div class="category-grid">
                        <button type="button" class="cat-btn" onclick="selectCategory('Su problemi', this)">
                            <span class="icon">💧</span>
                            <span class="name">Su</span>
                        </button>
                        <button type="button" class="cat-btn" onclick="selectCategory('Isiq problemi', this)">
                            <span class="icon">💡</span>
                            <span class="name">İşıq</span>
                        </button>
                        <button type="button" class="cat-btn" onclick="selectCategory('Yol problemi', this)">
                            <span class="icon">🛣️</span>
                            <span class="name">Yol</span>
                        </button>
                        <button type="button" class="cat-btn" onclick="selectCategory('Zibil problemi', this)">
                            <span class="icon">🗑️</span>
                            <span class="name">Zibil</span>
                        </button>
                        <button type="button" class="cat-btn" onclick="selectCategory('Agac problemi', this)">
                            <span class="icon">🌳</span>
                            <span class="name">Ağac</span>
                        </button>
                        <button type="button" class="cat-btn" onclick="selectCategory('Diger', this)">
                            <span class="icon">⚙️</span>
                            <span class="name">Digər</span>
                        </button>
                    </div>
                </div>
                <div class="form-group">
                    <label for="aciqla">2. Problemin təsviri</label>
                    <textarea id="aciqla" name="aciqla" placeholder="Məsələn: Təbriz küçəsi 45 ünvanında, yolun kənarındakı su borusunda sızma var. Su yola axır..." oninput="updateCharCount(this)" required></textarea>
                    <div class="char-count"><span id="char-num">0</span> / 1000 simvol (ən azı 10 simvol)</div>
                </div>
                <div class="form-group">
                    <label for="elaqe">3. Əlaqə məlumatınız (Ad və Telefon)</label>
                    <input type="text" id="elaqe" name="elaqe" class="input-text" placeholder="Məsələn: Əli Məmmədov, +994 50 123 45 67" required>
                </div>
                <div class="form-group">
                    <label>4. Fotoşəkil əlavə et (Könüllü)</label>
                    <div class="upload-area" onclick="document.getElementById('foto-input').click()">
                        <div class="upload-icon">📸</div>
                        <p id="upload-txt">Şəkili seçmək üçün <strong>klikləyin</strong> və ya bura sürüşdürün</p>
                        <input type="file" id="foto-input" name="foto" accept="image/*" style="display:none" onchange="previewPhoto(this)">
                        <img id="foto-preview" src="#" alt="Preview">
                    </div>
                </div>
                <div class="form-group">
                    <label>5. Problemin yerləşdiyi yer (Xəritədə qeyd edin)</label>
                    <div class="map-container">
                        <div id="map"></div>
                    </div>
                    <div class="map-actions">
                        <button type="button" class="btn-location" onclick="getLocationGPS()">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z"/><circle cx="12" cy="10" r="3"/></svg>
                            Cari məkandan istifadə et
                        </button>
                        <span class="coordinate-info" id="coord-display">Koordinat seçilməyib</span>
                    </div>
                </div>
                <button type="submit" class="submit-btn">
                    <span>🚀 Müraciəti Göndər</span>
                </button>
            </form>
        </div>
    </main>
    <script>
        const map = L.map('map').setView([40.4069, 49.8694], 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        let marker = null;
        const redIcon = L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        });
        setMarker([40.4069, 49.8694]);
        map.on('click', function(e) { setMarker([e.latlng.lat, e.latlng.lng]); });
        function setMarker(latlng) {
            if (marker) {
                marker.setLatLng(latlng);
            } else {
                marker = L.marker(latlng, {draggable: true, icon: redIcon}).addTo(map);
                marker.on('dragend', function() {
                    const pos = marker.getLatLng();
                    updateCoordinates(pos.lat, pos.lng);
                });
            }
            updateCoordinates(latlng[0], latlng[1]);
        }
        function updateCoordinates(lat, lon) {
            document.getElementById('lat-input').value = lat;
            document.getElementById('lon-input').value = lon;
            document.getElementById('coord-display').textContent = lat.toFixed(5) + ', ' + lon.toFixed(5);
        }
        function getLocationGPS() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(pos) {
                    const latlng = [pos.coords.latitude, pos.coords.longitude];
                    map.setView(latlng, 16);
                    setMarker(latlng);
                }, function(err) {
                    alert("GPS məlumatı alına bilmədi. Zəhmət olmasa xəritə üzərinə klikləyərək seçin.");
                });
            } else { alert("Brauzeriniz GPS xidmətini dəstəkləmir."); }
        }
        function selectCategory(category, element) {
            document.querySelectorAll('.cat-btn').forEach(btn => btn.classList.remove('active'));
            element.classList.add('active');
            document.getElementById('nov-input').value = category;
        }
        function updateCharCount(textarea) {
            document.getElementById('char-num').textContent = textarea.value.length;
        }
        function previewPhoto(input) {
            const file = input.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.getElementById('foto-preview');
                    img.src = e.target.result;
                    img.style.display = 'block';
                    document.getElementById('upload-txt').innerHTML = "Şəkil: <strong>" + file.name + "</strong>";
                }
                reader.readAsDataURL(file);
            }
        }
        function submitForm(event) {
            event.preventDefault();
            const nov = document.getElementById('nov-input').value;
            const aciqla = document.getElementById('aciqla').value.trim();
            const lat = document.getElementById('lat-input').value;
            if (!nov) { alert('Zəhmət olmasa problemin növünü seçin.'); return; }
            if (aciqla.length < 10) { alert('Zəhmət olmasa problemi ən azı 10 simvolla təsvir edin.'); return; }
            if (!lat) { alert('Zəhmət olmasa xəritədə müraciət yerini seçin.'); return; }
            document.getElementById('loading-overlay').classList.add('active');
            const formData = new FormData(document.getElementById('muraciet-form'));
            fetch('/muraciet', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('loading-overlay').classList.remove('active');
                if (data.ok) {
                    document.getElementById('success-id').textContent = "Müraciət Kodu: #" + data.id;
                    document.getElementById('success-sobe').textContent = "Məsul Şöbə: " + data.mesul_sobe;
                    const badge = document.getElementById('success-prioritet-badge');
                    badge.className = "badge badge-" + data.prioritet;
                    badge.textContent = data.prioritet;
                    document.getElementById('success-xulase').textContent = data.xulase;
                    document.getElementById('success-track-btn').href = '/izle/' + data.id;
                    document.getElementById('success-overlay').style.display = 'flex';
                } else {
                    document.getElementById('error-msg').textContent = data.error;
                    document.getElementById('error-overlay').style.display = 'flex';
                }
            })
            .catch(err => {
                document.getElementById('loading-overlay').classList.remove('active');
                alert('Müraciəti göndərərkən xəta baş verdi.');
            });
        }
        function closeErrorOverlay() { document.getElementById('error-overlay').style.display = 'none'; }
    </script>
</body>
</html>
"""

TRACK_HTML = """
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Müraciət Statusu — #{{ m.id }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        :root {
            --primary: #3b82f6;
            --accent: #10b981;
            --bg: #0b0f19;
            --card-bg: rgba(22, 30, 49, 0.75);
            --border: rgba(255, 255, 255, 0.08);
            --text: #f8fafc;
            --text-muted: #94a3b8;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: radial-gradient(circle at top right, #1e1b4b 0%, #0b0f19 80%);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            padding: 24px 16px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 20px;
            font-weight: 800;
            background: linear-gradient(135deg, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .logo span { -webkit-text-fill-color: initial; }
        .back-link {
            text-decoration: none;
            color: var(--text-muted);
            font-size: 14px;
            font-weight: 600;
            transition: color 0.2s;
        }
        .back-link:hover { color: white; }
        main {
            flex: 1;
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
            padding: 30px 16px;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 32px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            backdrop-filter: blur(16px);
        }
        .title-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 12px;
        }
        h2 { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase; }
        .badge-TECILI { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge-NORMAL { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-ASAGI { background: rgba(16, 185, 129, 0.15); color: var(--accent); border: 1px solid rgba(16, 185, 129, 0.3); }
        .timeline {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 40px 0;
            position: relative;
            padding: 0 10px;
        }
        .timeline::before {
            content: '';
            position: absolute;
            height: 4px;
            background: rgba(255,255,255,0.06);
            left: 10%;
            right: 10%;
            top: 24px;
            z-index: 1;
        }
        .timeline-progress {
            position: absolute;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            left: 10%;
            top: 24px;
            z-index: 2;
            transition: width 0.5s ease;
        }
        .timeline-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 3;
            width: 80px;
        }
        .circle {
            width: 52px;
            height: 52px;
            border-radius: 50%;
            background: #1e293b;
            border: 3px solid rgba(255,255,255,0.1);
            color: var(--text-muted);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: 700;
            transition: all 0.3s ease;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }
        .step-title {
            margin-top: 10px;
            font-size: 13px;
            font-weight: 700;
            color: var(--text-muted);
            text-align: center;
            white-space: nowrap;
        }
        .timeline-step.done .circle {
            background: var(--primary);
            border-color: var(--primary);
            color: white;
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
        }
        .timeline-step.done .step-title { color: white; }
        .timeline-step.current .circle {
            background: #1e1b4b;
            border-color: var(--primary);
            color: var(--primary);
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
            animation: pulse-ring 1.8s infinite;
        }
        .timeline-step.current .step-title { color: var(--primary); }
        .timeline-step.resolved .circle {
            background: var(--accent);
            border-color: var(--accent);
            color: white;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
        }
        .timeline-step.resolved .step-title { color: var(--accent); }
        @keyframes pulse-ring {
            0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.6); }
            70% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
            100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
        }
        .info-grid {
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 24px;
            margin-top: 32px;
        }
        .info-panel {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
        }
        .info-label {
            font-size: 11px;
            font-weight: 700;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 6px;
        }
        .info-value {
            font-size: 15px;
            line-height: 1.5;
            color: white;
            margin-bottom: 20px;
        }
        .info-value:last-child { margin-bottom: 0; }
        .info-value.bold { font-weight: 700; }
        .foto-container {
            width: 100%;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
            margin-bottom: 20px;
            background: rgba(0,0,0,0.2);
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .foto-img { max-width: 100%; max-height: 250px; object-fit: contain; display: block; }
        .map-container { border-radius: 12px; overflow: hidden; border: 1px solid var(--border); height: 200px; }
        #map { height: 100%; width: 100%; }
        @media (max-width: 768px) {
            .info-grid { grid-template-columns: 1fr; }
            .timeline::before, .timeline-progress { display: none; }
            .timeline { flex-direction: column; gap: 20px; align-items: flex-start; padding-left: 20%; }
            .timeline-step { flex-direction: row; gap: 16px; width: 100%; text-align: left; }
            .step-title { margin-top: 0; }
        }
    </style>
</head>
<body>
    <header>
        <a href="/" class="logo"><span>⚡</span> ByteGov</a>
        <a href="/" class="back-link">➔ Əsas Səhifə</a>
    </header>
    <main>
        <div class="card">
            <div class="title-row">
                <div>
                    <h2>Müraciət İzləmə</h2>
                    <span style="font-size: 14px; color: var(--text-muted);">Kod: #{{ m.id }}</span>
                </div>
                <span class="badge badge-{{ m.prioritet }}">{{ m.prioritet }}</span>
            </div>
            <div class="timeline">
                <div class="timeline-progress" id="t-prog"></div>
                <div class="timeline-step" id="step-yeni">
                    <div class="circle">1</div>
                    <span class="step-title">Qeydə Alındı</span>
                </div>
                <div class="timeline-step" id="step-islenilir">
                    <div class="circle">2</div>
                    <span class="step-title">İcradadır</span>
                </div>
                <div class="timeline-step" id="step-hell">
                    <div class="circle">3</div>
                    <span class="step-title">Həll Olundu</span>
                </div>
            </div>
            <div class="info-grid">
                <div class="info-panel">
                    <div class="info-label">📋 Problemin Növü</div>
                    <div class="info-value bold">{{ m.nov }}</div>
                    <div class="info-label">📝 Sakin Açıqlaması</div>
                    <div class="info-value" style="font-style: italic;">"{{ m.aciqla }}"</div>
                    <div class="info-label">🧠 Süni İntellekt Xülasəsi</div>
                    <div class="info-value" style="color: #60a5fa;">{{ m.xulase }}</div>
                    <div class="info-label">🏢 Məsul Qurum/Şöbə</div>
                    <div class="info-value bold">{{ m.mesul_sobe }}</div>
                    <div class="info-label">📅 Qeydiyyat Tarixi</div>
                    <div class="info-value">{{ m.tarix }}</div>
                </div>
                <div>
                    {% if m.foto_yol %}
                    <div class="foto-container">
                        <img class="foto-img" src="/foto/{{ m.id }}" alt="Müraciət fotoşəkli">
                    </div>
                    {% endif %}
                    <div class="map-container">
                        <div id="map"></div>
                    </div>
                </div>
            </div>
        </div>
    </main>
    <script>
        const status = "{{ m.status }}";
        const tProg = document.getElementById('t-prog');
        const stepYeni = document.getElementById('step-yeni');
        const stepIslenilir = document.getElementById('step-islenilir');
        const stepHell = document.getElementById('step-hell');
        if (status === "YENI") {
            stepYeni.classList.add('current');
            tProg.style.width = "0%";
        } else if (status === "ISLENILIR") {
            stepYeni.classList.add('done');
            stepIslenilir.classList.add('current');
            tProg.style.width = "40%";
        } else if (status === "HELL_EDILDI") {
            stepYeni.classList.add('done');
            stepIslenilir.classList.add('done');
            stepHell.classList.add('resolved');
            tProg.style.width = "80%";
            stepHell.querySelector('.circle').innerHTML = "✓";
        }
        const lat = {{ m.lat }};
        const lon = {{ m.lon }};
        const map = L.map('map', {zoomControl: false, scrollWheelZoom: false, doubleClickZoom: false, boxZoom: false, dragging: false}).setView([lat, lon], 15);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);
        const color = "{{ m.prioritet }}" === "TECILI" ? "#e74c3c" : "{{ m.prioritet }}" === "NORMAL" ? "#f39c12" : "#2ecc71";
        L.circleMarker([lat, lon], {
            radius: 10,
            color: color,
            fillColor: color,
            fillOpacity: 0.8,
            weight: 2
        }).addTo(map);
    </script>
</body>
</html>
"""

@app.route("/")
def landing():
    stats = statistika_al()
    nov_stats = stats.get('nov', {})
    status_stats = stats.get('status', {})
    umumi_say = sum(nov_stats.values())
    hell_say = status_stats.get('HELL_EDILDI', 0)
    aktiv_say = status_stats.get('YENI', 0) + status_stats.get('ISLENILIR', 0)
    avg_time = stats.get('avg_resolution_time', 4.2)
    return render_template_string(LANDING_HTML,
                                  umumi_say=umumi_say,
                                  hell_say=hell_say,
                                  aktiv_say=aktiv_say,
                                  avg_time=avg_time)

@app.route("/muraciet", methods=["GET", "POST"])
def public_muraciet():
    if request.method == "POST":
        nov = request.form.get("nov")
        aciqla = request.form.get("aciqla")
        elaqe = request.form.get("elaqe")
        lat_str = request.form.get("lat")
        lon_str = request.form.get("lon")
        
        if not nov or not aciqla or not lat_str or not lon_str:
            return jsonify({"ok": False, "error": "Zəhmət olmasa bütün məlumatları doldurun və xəritədə məkanı seçin."})
            
        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            return jsonify({"ok": False, "error": "Məkan koordinatları düzgün deyil."})
            
        if len(aciqla.strip()) < 10:
            return jsonify({"ok": False, "error": "Zəhmət olmasa problemi daha aydın açıqlayın (ən azı 10 simvol). Meselen: 'Nizami kucesinde iri cuxur var'"})
            
        foto_path = None
        file = request.files.get("foto")
        if file and file.filename != '':
            filename = secure_filename(f"web_{datetime.now().timestamp()}_{file.filename}")
            foto_path = os.path.join(PHOTOS_DIR, filename)
            file.save(foto_path)
            
            try:
                foto_res = ai_foto_analiz(foto_path)
                if not foto_res.get("problem_var"):
                    os.remove(foto_path)
                    return jsonify({
                        "ok": False, 
                        "error": f"Şəkildə kommunal infrastruktur problemi aşkar edilmədi: {foto_res.get('red_sebebi', 'Qeyri-müəyyən səbəb')}"
                    })
            except Exception as e:
                print(f"Web AI photo validation exception: {e}")
                
        try:
            analiz = ai_analiz(nov, aciqla, lat, lon)
            if analiz.get("saxta_muraciet"):
                if foto_path and os.path.exists(foto_path):
                    os.remove(foto_path)
                return jsonify({
                    "ok": False,
                    "error": f"Müraciət qəbul edilmədi. Səbəb: {analiz.get('red_sebebi', 'Kommunal infrastruktur problemi deyil.')}"
                })
        except Exception as e:
            print(f"Web AI text validation exception: {e}")
            analiz = {
                "prioritet": "NORMAL",
                "mesul_sobe": "Diger",
                "qisa_xulase": aciqla[:30],
                "saxta_muraciet": False,
                "red_sebebi": ""
            }
            
        user_id = f"WEB: {elaqe}" if elaqe else "WEB: Sakin"
        
        from database import muraciet_elave_et
        try:
            rowid = muraciet_elave_et(
    user_id=user_id,
    nov=nov,
    aciqla=aciqla,
    prioritet=analiz.get("prioritet", "NORMAL"),
    mesul_sobe=analiz.get("mesul_sobe", "Diger"),
    xulase=analiz.get("qisa_xulase", aciqla[:30]),
    lat=lat,
    lon=lon,
    tarix=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    status="YENI",
    foto_yol=foto_path
)
            
            return jsonify({
                "ok": True,
                "id": rowid,
                "nov": nov,
                "prioritet": analiz.get("prioritet", "NORMAL"),
                "mesul_sobe": analiz.get("mesul_sobe", "Diger"),
                "xulase": analiz.get("qisa_xulase", aciqla[:30])
            })
        except Exception as e:
            print(f"DB insert error: {e}")
            if foto_path and os.path.exists(foto_path):
                os.remove(foto_path)
            return jsonify({"ok": False, "error": f"Verilənlər bazasına yazarkən xəta baş verdi: {str(e)}"})
            
    return render_template_string(MURACIET_HTML)

@app.route("/izle/<int:muraciet_id>")
def track_muraciet(muraciet_id):
    rows = muracietleri_al()
    muraciet = None
    for r in rows:
        if r[0] == muraciet_id:
            muraciet = {
                "id": r[0],
                "user_id": r[1],
                "nov": r[2],
                "aciqla": r[3],
                "prioritet": r[4],
                "mesul_sobe": r[5],
                "xulase": r[6],
                "lat": r[7],
                "lon": r[8],
                "tarix": r[9],
                "status": r[10],
                "foto_yol": r[11] if len(r) > 11 else None
            }
            break
            
    if not muraciet:
        return "Müraciət tapılmadı", 404
        
    return render_template_string(TRACK_HTML, m=muraciet)


# Simple dashboard HTML used when user is logged in
@app.route("/foto/<int:muraciet_id>")
def get_foto(muraciet_id):
    import os
    from flask import send_from_directory
    rows = muracietleri_al()
    for r in rows:
        if r[0] == muraciet_id:
            foto_yol = r[11] if len(r) > 11 else None
            if foto_yol:
                dirname, filename = os.path.split(foto_yol)
                abs_dir = os.path.abspath(dirname)
                return send_from_directory(abs_dir, filename)
            break
    return "Fotoğraf bulunamadı", 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
