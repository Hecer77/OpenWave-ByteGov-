import os
import json
import base64
import httpx
from dotenv import load_dotenv

load_dotenv()
CLAUDE_KEY = os.getenv("CLAUDE_KEY")

def get_weather(lat: float, lon: float) -> str:
    if lat is None or lon is None:
        return "Hava məlumatı yoxdur"
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m&timezone=auto"
        res = httpx.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            curr = data.get("current", {})
            temp = curr.get("temperature_2m", 0)
            precip = curr.get("precipitation", 0)
            wind = curr.get("wind_speed_10m", 0)
            
            # Formulating a concise text for AI
            durum = []
            if precip > 0:
                durum.append("Yağış/Qar")
            if wind > 20:
                durum.append("Güclü Külək")
            
            elave = f" ({', '.join(durum)})" if durum else ""
            hava_metni = f"Temperatur: {temp}°C, Yağıntı: {precip}mm, Külək: {wind}km/s{elave}"
            return hava_metni
    except Exception as e:
        print(f"Hava melumati xetasi: {e}")
    return "Hava məlumatı əldə edilə bilmədi"

def hava_prioritet_yoxla(nov: str, aciqla: str, lat: float, lon: float) -> dict:
    """
    Hava şəraiti ilə problem növünü kəsişdirir.
    Əgər hava problemi gücləndirsə, prioritet avtomatik TƏCİLİ olur.
    Münsiflər üçün səbəb mətni də qaytarır.
    """
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,precipitation,wind_speed_10m,weather_code"
            f"&timezone=auto"
        )
        res = httpx.get(url, timeout=5)
        if res.status_code != 200:
            return {"tecili_et": False, "sebeb": ""}

        curr = res.json().get("current", {})
        yagis = curr.get("precipitation", 0)        # mm
        kuleк = curr.get("wind_speed_10m", 0)       # km/s
        temp = curr.get("temperature_2m", 20)       # °C
        weather_code = curr.get("weather_code", 0)

        nov_lower = nov.lower()
        aciqla_lower = aciqla.lower()

        # Kəsişmə qaydaları: (hava şərti) + (problem növü) → TƏCİLİ
        if yagis > 0.5:
            if any(k in nov_lower or k in aciqla_lower for k in
                   ["kanalizasiya", "su", "dam", "boru", "axma", "sel"]):
                return {
                    "tecili_et": True,
                    "sebeb": f"Cari yağış ({yagis}mm) su/kanalizasiya problemini kəskinləşdirir"
                }
            if any(k in nov_lower or k in aciqla_lower for k in
                   ["yol", "cuxur", "asfalt", "sel"]):
                return {
                    "tecili_et": True,
                    "sebeb": f"Yağış şəraitində ({yagis}mm) yol problemi sürücülər üçün təhlükəlidir"
                }

        if kuleк > 25:
            if any(k in nov_lower or k in aciqla_lower for k in
                   ["agac", "ağac", "direk", "dirək", "işıq", "isiq", "elektrik"]):
                return {
                    "tecili_et": True,
                    "sebeb": f"Güclü külək ({kuleк}km/s) ağac/elektrik infrastrukturuna risk yaradır"
                }

        if temp < 2:
            if any(k in nov_lower or k in aciqla_lower for k in
                   ["su", "boru", "kanalizasiya"]):
                return {
                    "tecili_et": True,
                    "sebeb": f"Dondurucu hava ({temp}°C) boru donması riskini artırır"
                }

        # Şiddətli hava kodları (thunderstorm, blizzard və s.)
        if weather_code in range(95, 100):
            return {
                "tecili_et": True,
                "sebeb": f"İldırımlı fırtına şəraitində istənilən infrastruktur problemi TƏCİLİ sayılır"
            }

        return {"tecili_et": False, "sebeb": ""}

    except Exception as e:
        print(f"hava_prioritet_yoxla xetasi: {e}")
        return {"tecili_et": False, "sebeb": ""}


def ai_foto_analiz(foto_path: str) -> dict:
    if not CLAUDE_KEY:
        print("Warning: CLAUDE_KEY not found. Skipping photo AI analysis.")
        return {"problem_var": True, "red_sebebi": ""}
        
    with open(foto_path, "rb") as f:
        foto_base64 = base64.b64encode(f.read()).decode("utf-8")

    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {CLAUDE_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "anthropic/claude-opus-4",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{foto_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """Bu sekilde Baki seheri kommunal infrastruktur problemi gorursenmü?
Yalniz asagidaki problemler qebul olunur:
- Yol: cuxur, asfalt sinigi, bordyur
- Su: boru sizintisi, kanalizasiya
- Isiq: direk sinigi, fonarin ishlememesi
- Zibil: ictimai erazide zibil yigilmasi
- Agac: devrilmis, tehlikeli agac

Cavabi YALNIZ bu JSON formatinda ver:
{
    "problem_var": true ya false,
    "red_sebebi": "eger problem_var false olarsa sebebi yaz, yoxsa bos saxla"
}"""
                        }
                    ]
                }
            ]
        },
        timeout=60
    )

    text = response.json()["choices"][0]["message"]["content"].strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)


def ai_analiz(nov: str, aciqla: str, lat: float = 40.4093, lon: float = 49.8671) -> dict:
    if not CLAUDE_KEY:
        print("Warning: CLAUDE_KEY not found. Using fallback analysis.")
        return {
            "prioritet": "NORMAL",
            "mesul_sobe": "Diger",
            "qisa_xulase": aciqla[:30],
            "saxta_muraciet": False,
            "red_sebebi": ""
        }
        
    try:
        yoxlama_prompt = f"""Mətnin şəhər kommunal infrastrukturuna (yollar, su boruları, kanalizasiya, küçə işıqları, zibil yığılması, aşmış ağaclar və s.) aid olan FİZİKİ və İCTİMAİ bir problem olub-olmadığını müəyyən et.

Aşağıdakı halları QƏBUL ETMƏ (fiziki_problem: false):
1. Şəxsi maliyyə, borc, kommunal ödənişlər (məsələn: "su pulunu ödəyə bilmirəm", "işıq pulu çox gəlib", "qaz pulu")
2. Şəxsi sağlamlıq, tibbi yardım
3. Şəxsi mülk daxili problemlər (YALNIZ mənzilin/evin İÇİNDƏki nasazlıqlar — məsələn, evdaxili kran, duş, elektrik rozeti. Evin/binanın XARICINDƏKI, küçədəki, həyətdəki problemlər QƏBUL OLUNUR)
4. İnsanlar arası münaqişələr, şikayətlər
5. Nəqliyyat sıxlığı, parkinq problemləri

Mətn: "{aciqla}"

Cavabı YALNIZ aşağıdakı JSON formatında ver:
{{
    "fiziki_problem": false,
    "sebeb": "qısa səbəb"
}}
və ya
{{
    "fiziki_problem": true,
    "sebeb": ""
}}"""

        yoxlama = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {CLAUDE_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": [
                    {
                        "role": "user",
                        "content": yoxlama_prompt
                    }
                ]
            },
            timeout=30
        )

        res_text = yoxlama.json()["choices"][0]["message"]["content"].strip()
        if "```json" in res_text:
            res_text = res_text.split("```json")[1].split("```")[0].strip()
        elif "```" in res_text:
            res_text = res_text.split("```")[1].split("```")[0].strip()

        try:
            yoxlama_data = json.loads(res_text)
        except Exception:
            if "false" in res_text.lower():
                yoxlama_data = {"fiziki_problem": False, "sebeb": "Məlumat düzgün formatda deyil"}
            else:
                yoxlama_data = {"fiziki_problem": True, "sebeb": ""}

        if not yoxlama_data.get("fiziki_problem"):
            return {
                "prioritet": "ASAGI",
                "mesul_sobe": "Diger",
                "qisa_xulase": "Kommunal problem deyil",
                "saxta_muraciet": True,
                "red_sebebi": yoxlama_data.get("sebeb", "Aciqlamada fiziki infrastruktur zedesi askar edilmedi")
            }

        # Fetch weather data for intelligent priority boosting
        hava_melumati = get_weather(lat, lon)

        analiz = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {CLAUDE_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-3-haiku",
                "messages": [
                    {
                        "role": "user",
                        "content": f"""Bu kommunal problemi analiz et:

Problem novu: {nov}
Aciqlamasi: {aciqla}
Cari Hava Şəraiti: {hava_melumati}

PRİORİTET:
TECILI: Ani fiziki tehlike - boru partlayib, elektrik naqili dushub, agac devrilib. Həmçinin, cari hava şəraiti (məs. güclü yağış, güclü külək) mövcud problemi (məs. dam axması, aşmaqda olan ağac, kanalizasiya daşması) daha da pisləşdirib təhlükəli edirsə, mütləq TECILI təyin et! Havanın problemə vurduğu ziyan riskini nəzərə al.
NORMAL: Tezlikle lazim - su kesintisi, iri cuxur, isiq yoxdur
ASAGI: Gozleye biler - kicik cuxur, zibil dolu

Cavabi YALNIZ bu JSON formatinda ver:
{{
    "prioritet": "TECILI" ya "NORMAL" ya "ASAGI",
    "mesul_sobe": "Kommunal xidmet" ya "Yol xidmeti" ya "Temizlik xidmeti" ya "Diger",
    "qisa_xulase": "maksimum 10 sozle xulase",
    "saxta_muraciet": false,
    "red_sebebi": ""
}}"""
                    }
                ]
            },
            timeout=30
        )

        text = analiz.json()["choices"][0]["message"]["content"].strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        try:
            natice = json.loads(text)
        except Exception:
            natice = {
                "prioritet": "NORMAL",
                "mesul_sobe": "Diger",
                "qisa_xulase": aciqla[:30],
                "saxta_muraciet": False,
                "red_sebebi": ""
            }

        # Hava kəsişməsi yoxlaması — AI-dan asılı olmadan məcburi TƏCİLİ
        hava_qeyd = hava_prioritet_yoxla(nov, aciqla, lat, lon)
        if hava_qeyd.get("tecili_et") and natice.get("prioritet") != "TECILI":
            natice["prioritet"] = "TECILI"
            original_xulase = natice.get("qisa_xulase", "")
            natice["qisa_xulase"] = f"{original_xulase} | ⚠️ {hava_qeyd['sebeb']}"

        return natice

    except Exception as e:
        print(f"ai_analiz xetasi: {e}")
        return {
            "prioritet": "NORMAL",
            "mesul_sobe": "Diger",
            "qisa_xulase": aciqla[:30],
            "saxta_muraciet": False,
            "red_sebebi": ""
        }
