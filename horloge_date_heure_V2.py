import network, ntptime, math, urequests, _thread, time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# Paramètres WiFi
ssid = "monSSID"
password = "monPWD"

# Initialisation WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
while not wlan.isconnected():
    time.sleep(1)

# Synchronisation NTP
ntptime.host = '0.europe.pool.ntp.org'
ntptime.settime()

# OLED setup
WIDTH, HEIGHT = 128, 32
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=200000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

# Données partagées
donnees = {"saint": "Chargement..."}

# Fonctions
def get_saint_of_day():
    try:
        r = urequests.get("https://www.ephemeride-jour.fr/ephemeride/saints-jour.php")
        texte = r.text
        r.close()
        start = texte.find("nous fêtons") + len("nous fêtons ")
        end = texte.find(".", start)
        saint = texte[start:end].strip()
        for prefixe in ["Saint ", "Sainte ", "St ", "St. "]:
            if saint.startswith(prefixe):
                saint = saint[len(prefixe):]
                break
        for sep in ['"', '<', '/', '>']:
            if sep in saint:
                saint = saint.split(sep)[0].strip()
        return saint
    except:
        return "Inconnu"

def is_summer_time(t):
    y = t[0]
    mls = max(d for d in range(25, 32) if time.localtime(time.mktime((y,3,d,2,0,0,0,0)))[6] == 6)
    ols = max(d for d in range(25, 32) if time.localtime(time.mktime((y,10,d,2,0,0,0,0)))[6] == 6)
    return (t[1]>3 and t[1]<10) or (t[1]==3 and t[2]>=mls) or (t[1]==10 and t[2]<ols)

def get_datetime():
    t = time.localtime()
    h = (t[3] + (2 if is_summer_time(t) else 1)) % 24
    return "{:02}.{:02}.{}".format(t[2], t[1], t[0]), "{:02}:{:02}:{:02}".format(h, t[4], t[5]), "+2" if is_summer_time(t) else "+1", h, t[4], t[5]

def draw_circle(oled, cx, cy, r):
    for a in range(0, 360, 5):
        x = int(cx + r * math.cos(math.radians(a)))
        y = int(cy + r * math.sin(math.radians(a)))
        if 0 <= x < oled.width and 0 <= y < oled.height:
            oled.pixel(x, y, 1)

def draw_clock_marks(oled, cx, cy, r):
    for a in [0, 90, 180, 270]:
        x = int(cx + r * math.cos(math.radians(a)))
        y = int(cy + r * math.sin(math.radians(a)))
        oled.pixel(x, y, 1)

def draw_thicker_point(oled, x, y, t=1):
    for dx in range(-t, t+1):
        for dy in range(-t, t+1):
            if 0 <= x+dx < oled.width and 0 <= y+dy < oled.height:
                oled.pixel(x+dx, y+dy, 1)

def draw_clock(oled, cx, cy, r, h, m, s):
    draw_circle(oled, cx, cy, r)
    draw_clock_marks(oled, cx, cy, r)
    a = {
        "h": math.radians((h % 12 + m / 60) * 30 - 90),
        "m": math.radians(m * 6 - 90),
        "s": math.radians(s * 6 - 90)
    }
    l = {"h": int(r*0.6), "m": int(r*0.9), "s": int(r*0.95)}
    for k in ["h","m"]:
        x = int(cx + l[k]*math.cos(a[k]))
        y = int(cy + l[k]*math.sin(a[k]))
        oled.line(cx, cy, x, y, 1)
    sx = int(cx + l["s"] * math.cos(a["s"]))
    sy = int(cy + l["s"] * math.sin(a["s"]))
    draw_thicker_point(oled, sx, sy, 1)

# Tâche affichage (cœur principal)
def affichage():
    while True:
        oled.fill(0)
        date, heure, saison, h, m, s = get_datetime()
        oled.text(date, 0, 0)
        oled.text(heure, 0, 12)
        oled.text(saison, 74, 12)
        draw_clock(oled, 112, 16, 15, h, m, s)  # Diamètre ajusté : rayon = 15
        oled.text(donnees["saint"][:15], 0, 24)
        oled.show()
        time.sleep(1)

# Tâche réseau (cœur secondaire)
def gestion_saint_du_jour():
    global donnees
    donnees["saint"] = get_saint_of_day()  # au démarrage
    last_day = time.localtime()[2]         # jour du mois
    while True:
        now = time.localtime()
        if now[3] == 0 and now[2] != last_day:  # à minuit
            donnees["saint"] = get_saint_of_day()
            last_day = now[2]
        time.sleep(120)  # vérification toutes les 60s

# Démarrage des tâches
_thread.start_new_thread(gestion_saint_du_jour, ())
affichage()

