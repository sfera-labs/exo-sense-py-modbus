from network import WLAN
from network import Server
from machine import UART
import os
import time
import pycom
import config

pycom.heartbeat(False)

uart = UART(0, 115200)
os.dupterm(uart)

if config.AP_ON_TIME_SEC < 120:
    config.AP_ON_TIME_SEC = 120

server = Server()
server.deinit()
server.init(login=(config.FTP_USER, config.FTP_PASSWORD))

wlan = WLAN()

pycom.rgbled(0xff0000)
print('Booted')
