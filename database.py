import sqlite3
import json
from datetime import datetime, timedelta

DB_NAME = "openwave.db"

def _get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def db_init():
    conn = _get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS muracietler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        nov TEXT,
        aciqla TEXT,
        prioritet TEXT,
        mesul_sobe TEXT,
        xulase TEXT,
        lat REAL,
        lon REAL,
        tarix TEXT,
        status TEXT DEFAULT 'YENI',
        foto_yol TEXT,
        deleted INTEGER DEFAULT 0
    )''')

    try:
        c.execute("ALTER TABLE muracietler ADD COLUMN deleted INTEGER DEFAULT 0")
    except Exception:
        pass

    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        muraciet_id INTEGER,
        emeliyyat TEXT,
        kohne_deyishen TEXT,
        yeni_deyishen TEXT,
        eden_user TEXT,
        tarix TEXT
    )''')

    conn.commit()
    conn.close()

def audit_yaz(muraciet_id, emeliyyat, kohne="", yeni="", eden_user="sistem"):
    conn = _get_conn()
    c = conn.cursor()
    c.execute('''INSERT INTO audit_log (muraciet_id, emeliyyat, kohne_deyishen, yeni_deyishen, eden_user, tarix)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (muraciet_id, emeliyyat, str(kohne), str(yeni), eden_user, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def muraciet_elave_et(user_id, nov, aciqla, prioritet, mesul_sobe, xulase, lat, lon, tarix, status, foto_yol=None):
    conn = _get_conn()
    c = conn.cursor()
    c.execute('''INSERT INTO muracietler 
                 (user_id, nov, aciqla, prioritet, mesul_sobe, xulase, lat, lon, tarix, status, foto_yol, deleted)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)''',
              (user_id, nov, aciqla, prioritet, mesul_sobe, xulase, lat, lon, tarix, status, foto_yol))
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    audit_yaz(last_id, "ELAVE_EDILDI", yeni=f"{nov} | {prioritet}", eden_user=user_id)
    return last_id

def muracietleri_al(deleted_dahil=False):
    conn = _get_conn()
    c = conn.cursor()
    if deleted_dahil:
        c.execute("SELECT id, user_id, nov, aciqla, prioritet, mesul_sobe, xulase, lat, lon, tarix, status, foto_yol, deleted FROM muracietler ORDER BY id DESC")
    else:
        c.execute("SELECT id, user_id, nov, aciqla, prioritet, mesul_sobe, xulase, lat, lon, tarix, status, foto_yol, deleted FROM muracietler WHERE deleted = 0 ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def status_yenile(muraciet_id, yeni_status, eden_user="admin"):
    conn = _get_conn()
    c = conn.cursor()
    c.execute("SELECT status FROM muracietler WHERE id = ?", (muraciet_id,))
    row = c.fetchone()
    kohne_status = row[0] if row else "?"
    c.execute("UPDATE muracietler SET status = ? WHERE id = ?", (yeni_status, muraciet_id))
    conn.commit()
    conn.close()
    audit_yaz(muraciet_id, "STATUS_DEYISDI", kohne=kohne_status, yeni=yeni_status, eden_user=eden_user)

def muraciet_sil(muraciet_id, eden_user="admin"):
    conn = _get_conn()
    c = conn.cursor()
    c.execute("UPDATE muracietler SET deleted = 1 WHERE id = ?", (muraciet_id,))
    conn.commit()
    conn.close()
    audit_yaz(muraciet_id, "SILINDI", kohne="deleted=0", yeni="deleted=1", eden_user=eden_user)

def muraciet_berpa_et(muraciet_id, eden_user="admin"):
    conn = _get_conn()
    c = conn.cursor()
    c.execute("UPDATE muracietler SET deleted = 0 WHERE id = ?", (muraciet_id,))
    conn.commit()
    conn.close()
    audit_yaz(muraciet_id, "BERPA_EDILDI", kohne="deleted=1", yeni="deleted=0", eden_user=eden_user)

def audit_log_al(muraciet_id=None):
    conn = _get_conn()
    c = conn.cursor()
    if muraciet_id:
        c.execute("SELECT * FROM audit_log WHERE muraciet_id = ? ORDER BY id DESC", (muraciet_id,))
    else:
        c.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 200")
    rows = c.fetchall()
    conn.close()
    return rows

def statistika_al():
    conn = _get_conn()
    c = conn.cursor()
    
    stats = {
        "nov": {},
        "prioritet": {"TECILI": 0, "NORMAL": 0, "ASAGI": 0},
        "status": {"YENI": 0, "ISLENILIR": 0, "HELL_EDILDI": 0},
        "top_mehelle": "Məlumat yoxdur",
        "top_mehelle_count": 0,
        "avg_resolution_time": 0,
        "tovsiye": "Süni intellekt məlumatları analiz edir...",
        "dinamika": []
    }
    
    c.execute("SELECT nov, COUNT(*) FROM muracietler WHERE deleted=0 GROUP BY nov")
    for r in c.fetchall():
        stats["nov"][r[0]] = r[1]
        
    c.execute("SELECT prioritet, COUNT(*) FROM muracietler WHERE deleted=0 GROUP BY prioritet")
    for r in c.fetchall():
        stats["prioritet"][r[0]] = r[1]
        
    c.execute("SELECT status, COUNT(*) FROM muracietler WHERE deleted=0 GROUP BY status")
    for r in c.fetchall():
        stats["status"][r[0]] = r[1]

    # Real dinamika — son 7 günün müraciət sayı bazadan
    bugun = datetime.now()
    dinamika = []
    for i in range(6, -1, -1):
        gun = bugun - timedelta(days=i)
        gun_str = gun.strftime("%Y-%m-%d")
        gun_label = gun.strftime("%d %b")
        c.execute(
            "SELECT COUNT(*) FROM muracietler WHERE deleted=0 AND tarix LIKE ?",
            (gun_str + "%",)
        )
        say = c.fetchone()[0]
        dinamika.append({"tarix": gun_label, "say": say})
    stats["dinamika"] = dinamika

    # Real ortalama həll müddəti (saat)
    c.execute("""
        SELECT tarix FROM muracietler 
        WHERE deleted=0 AND status='HELL_EDILDI' AND tarix IS NOT NULL
    """)
    hell_rows = c.fetchall()
    if hell_rows:
        # Audit logdan həll tarixini tap
        muddetler = []
        for (yaradilma,) in hell_rows:
            try:
                c.execute("""
                    SELECT tarix FROM audit_log 
                    WHERE emeliyyat='STATUS_DEYISDI' AND yeni_deyishen='HELL_EDILDI'
                    AND muraciet_id IN (
                        SELECT id FROM muracietler WHERE tarix=? AND deleted=0
                    )
                    ORDER BY id DESC LIMIT 1
                """, (yaradilma,))
                hell_tarixi = c.fetchone()
                if hell_tarixi:
                    t1 = datetime.strptime(yaradilma[:19], "%Y-%m-%d %H:%M:%S")
                    t2 = datetime.strptime(hell_tarixi[0][:19], "%Y-%m-%d %H:%M:%S")
                    diff = (t2 - t1).total_seconds() / 3600
                    if diff > 0:
                        muddetler.append(diff)
            except Exception:
                pass
        if muddetler:
            stats["avg_resolution_time"] = round(sum(muddetler) / len(muddetler), 1)

    # Ən problemli ərazi — mətn analizi
    c.execute("SELECT aciqla FROM muracietler WHERE deleted=0")
    descriptions = c.fetchall()
    mehelle_counts = {}
    for (desc,) in descriptions:
        if desc:
            words = desc.split()
            for w in words:
                if len(w) > 4:
                    mehelle_counts[w] = mehelle_counts.get(w, 0) + 1
    if mehelle_counts:
        top_word = max(mehelle_counts.items(), key=lambda x: x[1])
        stats["top_mehelle"] = top_word[0].capitalize() + " ətrafı"
        stats["top_mehelle_count"] = top_word[1]

    tecili = stats["prioritet"].get("TECILI", 0)
    if tecili > 5:
        stats["tovsiye"] = "Təcili müraciətlərin sayı kritik həddə çatıb. <br><b>Fəaliyyət:</b> Təmir briqadalarının sayını artırın."
    elif stats["status"].get("YENI", 0) > stats["status"].get("HELL_EDILDI", 0):
        stats["tovsiye"] = "Yeni müraciətlər həll olunanlardan çoxdur. Əməliyyat sürətini artırmaq lazımdır."
    else:
        stats["tovsiye"] = "Sistem stabil işləyir. Həllolunma faizi qənaətbəxşdir."
        
    conn.close()
    return stats

db_init()
