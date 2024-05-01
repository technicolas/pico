# **************************
# Programme BLINK (avec fct)
# **************************

# Sources:
# https://passionelectronique.fr/programmer-raspberry-pico-en-micropython/
# https://micropython.org/download/RPI_PICO_W/

from machine import Pin
from time import sleep

#led = Pin(25, mode=Pin.OUT)          # Pour Raspberry Pi Pico simple
led = Pin('LED', mode=Pin.OUT)        # Pour Raspberry Pi Pico W

def cligno(t_on,t_off):
    led.on()
    sleep(t_on)
    led.off()
    sleep(t_off)

while True:
    cligno(0.1,1.9)