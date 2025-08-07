import network, ntptime, math, urequests, _thread, time, utime
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# Réseau
ssid = "monSSID"                           # !!! Ne pas oublier de modifier ce paramètre !!!
password = "monPWD"                        # !!! Ne pas oublier de modifier ce paramètre !!!
WIDTH, HEIGHT = 128, 64
TAILLE_HORLOGE = 16

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=200000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)
donnees = {"saint": "Chargement...", "temperature": "---C"}

def initialiser_reseau():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(1)
    ntptime.host = '0.europe.pool.ntp.org'
    ntptime.settime()

# Heure
def is_summer_time(t):
    y = t[0]
    mls = max(d for d in range(25, 32) if time.localtime(time.mktime((y,3,d,2,0,0,0,0)))[6] == 6)
    ols = max(d for d in range(25, 32) if time.localtime(time.mktime((y,10,d,2,0,0,0,0)))[6] == 6)
    return (t[1]>3 and t[1]<10) or (t[1]==3 and t[2]>=mls) or (t[1]==10 and t[2]<ols)

def get_datetime():
    t = time.localtime()
    h = (t[3] + (2 if is_summer_time(t) else 1)) % 24
    return "{:02}.{:02}.{}".format(t[2], t[1], t[0]), "{:02}:{:02}:{:02}".format(h, t[4], t[5]), "+2" if is_summer_time(t) else "+1", h, t[4], t[5]

def supprimer_accents(texte):
    remplacements = {
        'à': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'î': 'i', 'ï': 'i',
        'ô': 'o', 'ö': 'o',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c',
        'À': 'A', 'Â': 'A', 'Ä': 'A',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'Î': 'I', 'Ï': 'I',
        'Ô': 'O', 'Ö': 'O',
        'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C'
    }
    return ''.join(remplacements.get(c, c) for c in texte)

# Données externes
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
        saint = supprimer_accents(saint)
        return saint
    except:
        return "Inconnu"

def get_temperature():
    try:
        r = urequests.get("http://wttr.in/Acoz?format=%t")
        temp = r.text.strip()
        r.close()
        temp = temp.replace("°C", " deg").replace("+", "").strip()
        return temp
    except:
        return "??C"

class GestionInfos:
    def __init__(self, donnees):
        self.donnees = donnees

    def actualiser(self):
        last_day = time.localtime()[2]
        self.donnees["saint"] = get_saint_of_day()
        self.donnees["temperature"] = get_temperature()
        last_update_temp = time.time()

        while True:
            now = time.localtime()

            if now[3] == 0 and now[2] != last_day:
                self.donnees["saint"] = get_saint_of_day()
                last_day = now[2]

            if time.time() - last_update_temp >= 1800:
                self.donnees["temperature"] = get_temperature()
                last_update_temp = time.time()

            time.sleep(5)

# Horloge
class HorlogeAnalogique:
    def __init__(self, oled, cx, cy, rayon):
        self.oled = oled
        self.cx = cx
        self.cy = cy
        self.r = rayon

    def dessiner_cadran(self):
        for a in range(0, 360, 5):
            x = int(self.cx + self.r * math.cos(math.radians(a)))
            y = int(self.cy + self.r * math.sin(math.radians(a)))
            self.oled.pixel(x, y, 1)
        for a in [0, 90, 180, 270]:
            x = int(self.cx + self.r * math.cos(math.radians(a)))
            y = int(self.cy + self.r * math.sin(math.radians(a)))
            self.oled.pixel(x, y, 1)

    def dessiner(self, h, m, s):
        self.dessiner_cadran()
        angles = {
            "h": math.radians((h % 12 + m / 60) * 30 - 90),
            "m": math.radians(m * 6 - 90),
            "s": math.radians(s * 6 - 90)
        }
        longueurs = {
            "h": int(self.r * 0.6),
            "m": int(self.r * 0.9),
            "s": int(self.r * 0.95)
        }
        for k in ["h", "m"]:
            x = int(self.cx + longueurs[k] * math.cos(angles[k]))
            y = int(self.cy + longueurs[k] * math.sin(angles[k]))
            self.oled.line(self.cx, self.cy, x, y, 1)
        sx = int(self.cx + longueurs["s"] * math.cos(angles["s"]))
        sy = int(self.cy + longueurs["s"] * math.sin(angles["s"]))
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if 0 <= sx+dx < self.oled.width and 0 <= sy+dy < self.oled.height:
                    self.oled.pixel(sx+dx, sy+dy, 1)

# Affichage
class AfficheurOLED:
    def __init__(self, oled, horloge, donnees):
        self.oled = oled
        self.horloge = horloge
        self.donnees = donnees

    def afficher(self):
        intervalle_ms = 1000
        prochaine_frame = utime.ticks_add(utime.ticks_ms(), intervalle_ms)
        while True:
            self.oled.fill(0)
            date, heure, saison, h, m, s = get_datetime()
            self.oled.text(date, 0, 0)
            self.oled.text(heure, 0, 12)
            self.oled.text(saison, 72, 12)
            self.oled.text("Tmp: " + self.donnees.get("temperature", "??"), 0, 26)
            self.horloge.dessiner(h, m, s)
            self.oled.text("Saint(e) du jour", 0, 42)
            self.oled.text(self.donnees["saint"][:15], 0, 54)
            self.oled.show()
            attente = utime.ticks_diff(prochaine_frame, utime.ticks_ms())
            if attente > 0:
                utime.sleep_ms(attente)
            prochaine_frame = utime.ticks_add(prochaine_frame, intervalle_ms)

# Lancement
# print("Connexion réseau…")
initialiser_reseau()
# print("Réseau OK")

horloge = HorlogeAnalogique(oled, 112, 16, TAILLE_HORLOGE)
afficheur = AfficheurOLED(oled, horloge, donnees)
infos = GestionInfos(donnees)

# print("Démarrage du thread")
_thread.start_new_thread(infos.actualiser, ())
# print("Thread lancé")

# print("Affichage lancé")
afficheur.afficher()

