import os
import re
import time
import json
import random
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# Список слов-исключений
STOP_WORDS = ["повітря"]
# Фразы для ручной очистки ВСЕЙ карты
CLEAR_WORDS = ["локаційно втрачено", "без подальшої фіксації", "чисто", "втрачено", "мінус", "збито"]
# Фразы для удаления конкретного маркера (локально)
DISAPPEAR_WORDS = ["локаційно зник", "локаційно чисто", "зник", "припинив існування", "вийшов з області", "впали", "чисто", "локаційно втрачений" ]

DNIPRO_BORDER_LAT = 48.15

VILLAGES = {
    # --- ЗАПОРОЖЬЕ И ПРИГОРОД ---
    "запоріж": [47.838, 35.139], "космос": [47.795, 35.201], "піск": [47.778, 35.182],
    "південн": [47.778, 35.182], "кічкас": [47.892, 35.152], "бабурк": [47.812, 35.064],
    "верхня хортиц": [47.858, 35.061], " вх ": [47.858, 35.061], "бомбей": [47.864, 35.082],
    "шевченківськ": [47.845, 35.215], "комунарськ": [47.790, 35.200], "олександрівськ": [47.824, 35.161],
    "вознесенівськ": [47.838, 35.127], "дніпровськ": [47.862, 35.115], "хортицьк": [47.812, 35.064],
    "заводськ": [47.885, 35.148], "шавлон": [47.848, 35.234], "зеленій": [47.818, 35.225], 
    "ддт": [47.854, 35.215], "карантин": [47.813, 35.176], "болгарк": [47.796, 35.155],
    "кушугум": [47.712, 35.218], "балабин": [47.743, 35.221], "малокатерин": [47.661, 35.257],
    "розумівк": [47.747, 35.131], "нижня хортиц": [47.778, 35.111], "канівськ": [47.702, 35.114],
    "лисогірк": [47.674, 35.121], "біленьк": [47.625, 35.043], "наталівк": [47.828, 35.291],
    "степне": [47.794, 35.308], "лeжине": [47.768, 35.347], "новоолександрівк": [47.751, 35.365],
    "григорівк": [47.712, 35.369], "широке": [47.915, 34.905], "відрадне": [47.994, 35.106],
    "богатир": [47.986, 35.197], "новосергіївка": [47.736, 35.003], "нове запорі": [47.827, 34.933],
    "миролюбів": [47.916, 35.667], "новомиргоро": [47.985, 35.656], "русло": [47.657, 35.189],
    "долинське": [47.787, 34.938], "балаби": [47.745, 35.219], "Аеро": [47.867, 35.312], "димитр": [47.836, 35.233], 
    "17": [47.836, 35.011], "ждановск": [47.834, 35.109],  "гребний": [47.764, 35.173], "червонодніпров": [47.569, 34.968], 
    "Томаківк": [47.812, 34.749], 

    # --- ВОЛЬНЯНСКИЙ И НОВОНИКОЛАЕВСКИЙ НАПРАВЛЕНИЯ ---
    "вільнянськ": [47.942, 35.438], "матвіївк": [47.907, 35.311], "люцерн": [47.917, 35.289],
    "михайлівк": [47.954, 35.228], "любимівк": [47.986, 35.419], "вільноандріївк": [47.973, 35.112],
    "павлівк": [47.951, 35.474], "петро-михайлівк": [48.028, 35.219], 
    "куприянівк": [47.905, 35.498], "новогупалівк": [48.014, 35.452], "новомиколаївк": [47.977, 35.912],
    "тернуват": [47.828, 36.136], "любицьк": [47.835, 35.968], "софіївк": [47.944, 35.807],
    "підгірн": [47.946, 35.992], "зелене": [47.914, 36.039], "миколай-поле": [48.069, 34.908],
    "ясн полян": [47.809, 35.747], "одарівк": [47.715, 35.6177], "адріанівк": [47.886, 35.576],
    "мокрянк": [47.812, 35.229], "міськпаливо": [47.814, 35.194], "гортоп": [47.814, 35.194],
     "гес": [47.868, 35.088], "перемо": [47.827, 35.145], "металург": [47.860131,35.106392], "заводи": [47.864556,35.153966], 
     "мостозагін": [47.815888,35.069729], "вирва": [47.840773,35.037018], "ирас": [47.732298,35.270778], "метр": [47.788, 35.238],
     "нх": [47.770, 35.128],

    # --- ПОЛОГОВСКИЙ РАЙОН И ОКРЕСТНОСТИ ГУЛЯЙПОЛЯ ---
    "гуляйпол": [47.662, 36.262], "гуляйпіль": [47.611, 36.061], "полог": [47.474, 36.252],
    "оріхів": [47.566, 35.786], "комишувах": [47.717, 35.523], "омельник": [47.589, 35.894],
    "мала токмач": [47.535, 35.892], "вербове": [47.424, 35.986], "роботин": [47.448, 35.837],
    "новофедорівк": [47.458, 36.082], "інженерн": [47.477, 36.141], "воскreсенк": [47.451, 36.355],
    "залізничн": [47.652, 36.172], "малинівк": [47.671, 36.425], "успенівськ": [47.578, 36.291],
    "новомиколаївк_пол": [47.531, 36.208], "марфопіл": [47.612, 36.305], "червоне": [47.643, 36.398],
    "зелений гай": [47.715, 36.211], "дорожнянк": [47.575, 36.217], "мирне_пол": [47.514, 36.342],
    "tokmak": [47.248, 35.706], "молочанськ": [47.204, 35.597], "таврійськ": [47.660, 35.698],

    # --- МЕЛИТОПОЛЬСКИЙ И ВАСИЛЬЕВСКИЙ РАЙОНЫ ---
    "мелітопол": [46.848, 35.372], "якимівк": [46.690, 35.153], "приазовськ": [46.732, 35.632],
    "веселе": [47.018, 34.921], "костянтинівк": [46.821, 35.418], "вознесенк": [46.871, 35.474],
    "терпінн": [46.931, 35.424], "мирне": [46.936, 35.431], "новгородківк": [46.825, 35.206],
    "семенівк": [46.892, 35.405], "обільне": [46.885, 35.524], "тихонівк": [46.882, 35.612],
    "михайлівка_мел": [47.222, 35.223], "дніпрорудн": [47.387, 34.987], "василівк": [47.435, 35.275]
}

LATEST_MAP_DATA = {"targets": [], "infobox": "Завантаження даних..."}

KYIV_TZ = timezone(timedelta(hours=3))

def get_tg_posts():
    targets = []
    try:
        url = "https://t.me/s/eyes_everywhere_ua"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        cards = soup.find_all(class_="tgme_widget_message")
        
        for card in cards:
            data_post = card.get('data-post', '')
            if not data_post:
                continue
            post_id = data_post.split('/')[-1]

            time_element = card.find(class_="tgme_widget_message_date")
            if not time_element:
                continue
            datetime_block = time_element.find("time")
            if not datetime_block or not datetime_block.get('datetime'):
                continue
            
            post_time_utc = datetime.fromisoformat(datetime_block.get('datetime')).replace(tzinfo=timezone.utc)
            post_time_kyiv = post_time_utc.astimezone(KYIV_TZ)
            
            text_block = card.find(class_="tgme_widget_message_text")
            if not text_block:
                continue
            
            text = text_block.get_text(separator="\n").strip()
            if any(word in text.lower() for word in STOP_WORDS):
                continue
                
            reply_link = card.find(class_="tgme_widget_message_reply")
            reply_to_id = None
            if reply_link:
                href = reply_link.get('href', '')
                match = re.search(r'/(\d+)$', href)
                if match:
                    reply_to_id = match.group(1)

            targets.append({
                "id": post_id, 
                "time": post_time_kyiv, 
                "text": text, 
                "reply_to": reply_to_id
            })
    except Exception as e:
        print(f"Помилка парсингу ТГ: {e}")
    return targets

def parse_target_data(text):
    clean_text = f" {text.lower()} "
    
    # Полная очистка
    if any(word in clean_text for word in CLEAR_WORDS):
        return "clear", "red", False, None
        
    # Локальное исчезновение цели
    if any(word in clean_text for word in DISAPPEAR_WORDS):
        # Ищем, в каком месте цель пропала, чтобы передать на удаление
        found_locs = []
        for key in VILLAGES:
            if key in clean_text:
                found_locs.append(key)
        return "disappear", "gray", False, {"locations": found_locs}

    is_course_changed = "змін" in clean_text or "смін" in clean_text
    is_dnipro_direction = "дніпро" in clean_text and ("курс" in clean_text or "на дні" in clean_text or "далі на" in clean_text)

    target_type = "shahed"
    if any(w in clean_text for w in ["фпв", "fpv", "камікадзе"]):
        target_type = "fpv"
    elif any(w in clean_text for w in ["невстановлений", "бпла", "безпілотник"]) and not any(w in clean_text for w in ["шахед", "ударний", "каб", "розвідник", "фпв", "Молнія"]):
        target_type = "unknown"
    elif any(w in clean_text for w in ["каб", "кабів", "скид ка", "пуск ка"]):
        target_type = "kab"
    elif any(w in clean_text for w in ["борт", "літак", "су-3", "сушки", "авіа"]):
        target_type = "bort"
    elif any(w in clean_text for w in ["розвідник", "бпла-розвідник", "зала", "орлан", "суперкам"]):
        target_type = "scout"

    color_map = {"shahed": "red", "kab": "orange", "bort": "blue", "scout": "green", "unknown": "black", "fpv": "purple", "lightning": "yellow"}
    color = color_map[target_type]

    is_list = False
    lines = text.split('\n')
    if sum(1 for line in lines if re.match(r'^\s*\d+[\s\.\)]', line)) >= 2:
        is_list = True

    words_positions = []
    for key in VILLAGES:
        idx = clean_text.find(key)
        if idx != -1:
            words_positions.append((idx, key))
    words_positions.sort()
    found = [item[1] for item in words_positions]

    if is_list:
        return "list", color, False, {"locations": found}
    if len(found) >= 2:
        return "vector", color, False, {"start": found[0], "end": found[1]}
    elif len(found) == 1:
        return "single", color, False, {"end": found[0]}
    return "unknown", color, False, None

def process_data_loop():
    global LATEST_MAP_DATA
    while True:
        try:
            posts = get_tg_posts()
            if posts:
                now_kyiv = datetime.now(timezone.utc).astimezone(KYIV_TZ)
                # Сортируем от старых к новым, чтобы правильно обрабатывать цепочки ответов
                posts.sort(key=lambda x: x["time"])
                
                # Сначала определим посты, которые приказывают удалить маркеры
                deleted_post_ids = set()
                deleted_locations = set()
                
                for post in posts:
                    clean_text = post["text"].lower()
                    if any(word in clean_text for word in DISAPPEAR_WORDS):
                        if post["reply_to"]:
                            deleted_post_ids.add(post["reply_to"])
                        for key in VILLAGES:
                            if key in clean_text:
                                deleted_locations.add(key)

                active_targets = []
                infobox_html_list = []
                
                # Обрабатываем цели
                for post in posts:
                    age_seconds = (now_kyiv - post["time"]).total_seconds()
                    if age_seconds > 350 or age_seconds < -350:
                        continue
                        
                    # МГНОВЕННОЕ УДАЛЕНИЕ: если этот пост был аннулирован реплаем "зник"
                    if post["id"] in deleted_post_ids:
                        continue
                        
                    g_type, color, force_single, geo_data = parse_target_data(post["text"])
                    
                    if g_type == "clear":
                        active_targets = []
                        infobox_html_list = ["<div style='color:green;'><b>Чисте небо. Активних цілей немає.</b></div>"]
                        break
                        
                    # МГНОВЕННОЕ УДАЛЕНИЕ: если в посте упомянуто село, по которому была команда отмены
                    if geo_data:
                        if g_type == "single" and geo_data.get("end") in deleted_locations:
                            continue
                        if g_type == "vector" and geo_data.get("end") in deleted_locations:
                            continue
                        if g_type == "list" and geo_data.get("locations"):
                            geo_data["locations"] = [l for l in geo_data["locations"] if l not in deleted_locations]
                            if not geo_data["locations"]:
                                continue

                    opacity = 1.0 if age_seconds < 300 else 0.5
                    time_str = post["time"].strftime("%H:%M:%S")
                    clean_text_box = post["text"].replace("\n", "<br>")
                    
                    infobox_html_list.append(f"<div style='opacity: {opacity}; border-left: 3px solid {color}; padding-left:5px; margin-bottom:8px;'>[{time_str}] {clean_text_box}</div>")
                    
                    print(
    "ДОБАВЛЕНА ЦЕЛЬ:",
    post["time"].strftime("%H:%M:%S"),
    post["text"][:80]
)

                    active_targets.append({
                        "g_type": g_type, "color": color, "force_single": force_single,
                        "geo_data": geo_data, "opacity": opacity, "time_str": time_str
                    })
                
                # Формируем инфобокс (новые сверху)
                infobox_html_list.reverse()
                infobox_html = "".join(infobox_html_list)
                
                if not active_targets and not infobox_html:
                    infobox_html = "Чисте небо. Активних цілей немає."
                    
                LATEST_MAP_DATA = {"targets": active_targets, "infobox": infobox_html}
                print(f"[{now_kyiv.strftime('%H:%M:%S')}] Оновлено. Активно цілей: {len(active_targets)}")
        except Exception as e:
            print(f"Помилка в циклі обробки: {e}")
        time.sleep(5)

# --- ВЕБ СЕРВЕР ---
class MapServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
        
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.end_headers()
        
        targets_json = json.dumps(LATEST_MAP_DATA.get("targets", []))
        infobox_content = LATEST_MAP_DATA.get("infobox", "Чисте небо. Активних цілей немає.")
        
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="15">
    <title>Оперативна Карта</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/leaflet-polyline-decorator@1.6.0/leaflet.polylineDecorator.min.js"></script>
    <style>
        body, html, #map { margin: 0; padding: 0; height: 100%; width: 100%; }
        #box { position: absolute; top: 10px; left: 10px; z-index: 1000; background: white; padding: 10px; border-radius: 5px; max-width: 90%; font-family: sans-serif; box-shadow: 0 2px 5px rgba(0,0,0,0.3); max-height: 40%; overflow-y: auto; font-size:13px; }
        .legend { position: absolute; bottom: 20px; left: 10px; z-index: 1000; background: white; padding: 8px; border-radius: 5px; font-family: sans-serif; font-size: 11px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }
        .legend-item { display: flex; align-items: center; margin-bottom: 3px; }
        .color-box { width: 14px; height: 4px; margin-right: 6px; }
    </style>
</head>
<body>
    <div id="box"><b>Оперативна обстановка:</b><br><div id="info-content">""" + infobox_content + """</div></div>
    <div class="legend">
        <div class="legend-item"><div class="color-box" style="background:red;"></div> Шахед</div>
        <div class="legend-item"><div class="color-box" style="background:purple;"></div> FPV-дрон</div>
        <div class="legend-item"><div class="color-box" style="background:black;"></div> Невстановлений БпЛА</div>
        <div class="legend-item"><div class="color-box" style="background:blue;"></div> Авіація</div>
        <div class="legend-item"><div class="color-box" style="background:orange;"></div> КАБ</div>
        <div class="legend-item"><div class="color-box" style="background:green;"></div> Розвідник</div>
        <div class="legend-item"><div class="color-box" style="background:yellow;;"></div> Молния</div>
    </div>
    <div id="map"></div>

    <script>
        const savedCenter = localStorage.getItem('map_center') ? JSON.parse(localStorage.getItem('map_center')) : [47.4, 35.6];
        const savedZoom = localStorage.getItem('map_zoom') ? parseInt(localStorage.getItem('map_zoom')) : 9;

        const map = L.map('map').setView(savedCenter, savedZoom);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        
        map.on('moveend', () => {
            localStorage.setItem('map_center', JSON.stringify([map.getCenter().lat, map.getCenter().lng]));
            localStorage.setItem('map_zoom', map.getZoom());
        });

        let markerLayerGroup = L.layerGroup().addTo(map);
        const VILLAGES_JS = """ + str(VILLAGES) + """;
        const targets = """ + targets_json + """;

        targets.forEach(target => {
            let geo = target.geo_data;
            if(!geo) return;
            
            let opacity = target.opacity;
            let color = target.color;
            let pTime = "<br><small style='color:gray;'>Час публікації: " + target.time_str + "</small>";
            
            if (target.g_type === "list" && geo.locations) {
                geo.locations.forEach(loc => {
                    let coords = VILLAGES_JS[loc];
                    if(coords) {
                        L.circleMarker(coords, {
                            radius: 8, fillColor: color, color: '#fff', weight: 2, fillOpacity: opacity, opacity: opacity
                        }).addTo(markerLayerGroup).bindPopup("<b>Зведення: " + loc + "</b>" + pTime);
                    }
                });
            }
            else if (target.g_type === "single" && geo.end) {
                let coords = VILLAGES_JS[geo.end];
                if(coords) {
                    let title = target.force_single ? "⚠️ Зміна курсу!" : "Ціль: " + geo.end;
                    L.circleMarker(coords, {
    radius: 10,
    fillColor: color,
    color: "#fff",
    weight: 2,
    opacity: opacity,
    fillOpacity: opacity
})
.addTo(markerLayerGroup)
.bindPopup("<b>"+title+"</b>" + pTime);
                }
            }
            else if (target.g_type === "vector" && geo.start && geo.end) {
                let start = VILLAGES_JS[geo.start];
                let end = VILLAGES_JS[geo.end];
                if(start && end) {
                    L.circleMarker(start, {
    radius: 7,
    fillColor: color,
    color: "#fff",
    weight: 1,
    opacity: opacity * 0.6,
    fillOpacity: opacity * 0.6
}).addTo(markerLayerGroup)
  .bindPopup("Початок курсу");

L.circleMarker(end, {
    radius: 10,
    fillColor: color,
    color: "#fff",
    weight: 2,
    opacity: opacity,
    fillOpacity: opacity
}).addTo(markerLayerGroup)
  .bindPopup("<b>Поточна позиція</b>" + pTime);
                }
            }
        });
    </script>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))

def run_server():
    server = HTTPServer(('127.0.0.1', 8080), MapServer)
    print("\n[!] Сервер успішно запущено на http://127.0.0.1:8080")
    server.serve_forever()

if __name__ == '__main__':
    t = threading.Thread(target=process_data_loop, daemon=True)
    t.start()
    run_server()