# **************************
# Programme BLINK (avec fct)
# **************************

# Sources:
# https://passionelectronique.fr/programmer-raspberry-pico-en-micropython/
# https://micropython.org/download/RPI_PICO_W/

from machine import Pin
from time import sleep
import time                           # Pour la fonction cligno2

#led = Pin(25, mode=Pin.OUT)          # Pour Raspberry Pi Pico simple
led = Pin('LED', mode=Pin.OUT)        # Pour Raspberry Pi Pico W

def cligno(t_on,t_off):
    t_off=t_off-t_on                  # Temps OFF = Temps total - Temps ON
    led.on()
    sleep(t_on)
    led.off()
    sleep(t_off)

def cligno2(time_ms):
    led.toggle()
    time.sleep_ms(time_ms)            # time.sleep_us, time.sleep_ms, time.sleep(T_sec)

while True:
    cligno(0.25,3)
#    cligno2(1000)
