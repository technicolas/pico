import network
import ntptime
import math
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

# Écran OLED 128x32
WIDTH = 128
HEIGHT = 32
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=200000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

# Connexion WiFi
ssid = 		"monSSID"
password = 	"monPWD_WIFI"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while not wlan.isconnected():
    oled.fill(0)
    oled.text("Connexion WiFi...", 0, 10)
    oled.show()
    time.sleep(1)

# Synchronisation NTP
ntptime.host = '0.europe.pool.ntp.org'				# prendra le serveur le plus rapide dans ma région
                                                    # 0.europe.pool.ntp.org,... , 3.europe.pool.ntp.org
ntptime.settime()

# Cercle cadran
def draw_circle(oled, cx, cy, r, color=1):
    for angle in range(0, 360, 5):
        rad = math.radians(angle)
        x = int(cx + r * math.cos(rad))
        y = int(cy + r * math.sin(rad))
        if 0 <= x < oled.width and 0 <= y < oled.height:
            oled.pixel(x, y, color)

# Repères cadran
def draw_clock_marks(oled, cx, cy, radius):
    for hour in [0, 90, 180, 270]:
        rad = math.radians(hour)
        x = int(cx + radius * math.cos(rad))
        y = int(cy + radius * math.sin(rad))
        oled.pixel(x, y, 1)

# Heure d’été
def is_summer_time(t):
    year = t[0]
    march_last_sunday = max(day for day in range(25, 32)
        if time.localtime(time.mktime((year, 3, day, 2, 0, 0, 0, 0)))[6] == 6)
    october_last_sunday = max(day for day in range(25, 32)
        if time.localtime(time.mktime((year, 10, day, 2, 0, 0, 0, 0)))[6] == 6)
    month, day = t[1], t[2]
    if (month > 3 and month < 10):
        return True
    elif month == 3 and day >= march_last_sunday:
        return True
    elif month == 10 and day < october_last_sunday:
        return True
    return False

# Date, heure, saison
def get_datetime():
    t = time.localtime()
    heure_locale = t[3] + (2 if is_summer_time(t) else 1)
    heure_locale %= 24
    date_str = "{:02}.{:02}.{}".format(t[2], t[1], t[0])
    time_str = "{:02}:{:02}:{:02}".format(heure_locale, t[4], t[5])
    saison = "H+2" if is_summer_time(t) else "H+1"
    return date_str, time_str, saison, heure_locale, t[4], t[5]

# Point de la seconde
def draw_thicker_point(oled, x, y, thickness=1):
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if 0 <= x + dx < oled.width and 0 <= y + dy < oled.height:
                oled.pixel(x + dx, y + dy, 1)

# Dessin horloge analogique
def draw_clock(oled, cx, cy, radius, h, m, s):
    draw_circle(oled, cx, cy, radius)
    draw_clock_marks(oled, cx, cy, radius)
    h_angle = math.radians((h % 12 + m / 60) * 30 - 90)
    m_angle = math.radians(m * 6 - 90)
    s_angle = math.radians(s * 6 - 90)

    h_len = int(radius * 0.6)
    m_len = int(radius * 0.9)
    s_len = int(radius * 0.95)

    hx = int(cx + h_len * math.cos(h_angle))
    hy = int(cy + h_len * math.sin(h_angle))
    mx = int(cx + m_len * math.cos(m_angle))
    my = int(cy + m_len * math.sin(m_angle))
    sx = int(cx + s_len * math.cos(s_angle))
    sy = int(cy + s_len * math.sin(s_angle))

    oled.line(cx, cy, hx, hy, 1)
    oled.line(cx, cy, mx, my, 1)
    draw_thicker_point(oled, sx, sy, thickness=1)  # (1 = carré 3×3 pixels, 2 = carré 5×5 pixels)

# Boucle principale
while True:
    oled.fill(0)
    date_str, time_str, saison, h, m, s = get_datetime()

    # Texte à gauche
    oled.text(date_str, 0, 0)						# Affichage de la date
    oled.text(time_str, 0, 12)						# Affichage de l'heure
    oled.text(saison, 0, 24)						# Affichage du décalage saison été/hiver

    # Horloge à droite
    draw_clock(oled, 112, 16, 12, h, m, s)			# Affichage de l'horloge analogique

    oled.show()
    time.sleep(1)									#Sleep d'une seconde
