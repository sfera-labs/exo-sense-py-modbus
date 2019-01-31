from network import WLAN
from network import Server
from machine import UART
import os
import time
import pycom

pycom.heartbeat(False)

uart = UART(0, 115200)
os.dupterm(uart)

print('=== Exo Sense Py - Modbus RTU/TCP - v1.0.0 ===')

wlan = WLAN()
wlan.deinit()

pycom.rgbled(0xff0000)
print('Booted')
