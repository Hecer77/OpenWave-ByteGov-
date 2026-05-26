import sys, os

with open('c:/Users/USER/openwave/dashboard.py', encoding='utf-8') as f:
    lines = f.readlines()

def get_lines(start, end):
    return ''.join(lines[start-1:end])

imports = get_lines(1, 17)
login_html = get_lines(18, 64)
landing_html = get_lines(65, 408)
muraciet_html = get_lines(409, 909)
track_html = get_lines(910, 1225)
route_landing = get_lines(1226, 1240)
route_admin = get_lines(1241, 1246)
route_giris = get_lines(1247, 1250)
route_login = get_lines(1251, 1259)
route_cixis = get_lines(1260, 1264)
route_muraciet = get_lines(1265, 1354)
route_izle = get_lines(1355, 1383)
admin_html = get_lines(1384, 2085)
route_api_muracietler = get_lines(2086, 2103)
route_api_status_yenile = get_lines(2104, 2145)
route_foto = get_lines(2146, 2160)
route_api_statistika = get_lines(2161, 2166)

admin_route_foto = '''@app.route("/foto/<int:muraciet_id>")
def get_foto(muraciet_id):
    if not session.get("giris"):
        return redirect("/giris")
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
'''

app_citizen = imports + landing_html + muraciet_html + track_html + route_landing + route_muraciet + route_izle + route_foto + '\nif __name__ == "__main__":\n    app.run(debug=True, port=5000)\n'
app_admin = imports + login_html + admin_html + route_admin + route_giris + route_login + route_cixis + route_api_muracietler + route_api_status_yenile + admin_route_foto + '\n' + route_api_statistika + '\nif __name__ == "__main__":\n    app.run(debug=True, port=5002)\n'

with open('c:/Users/USER/openwave/app_citizen.py', 'w', encoding='utf-8') as f:
    f.write(app_citizen)
with open('c:/Users/USER/openwave/app_admin.py', 'w', encoding='utf-8') as f:
    f.write(app_admin)

print('Split completed successfully.')
