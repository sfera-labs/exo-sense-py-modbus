import time
import _thread
import pycom
from exosense import ExoSense
from modbusrtu import ModbusRTU
import config

_status_ap_enabled_once = False
_status_mb_got_request = False

def _enable_ap():
    global _status_ap_enabled_once
    pycom.rgbled(0xffff00)
    wlan.deinit()
    time.sleep(2)
    wlan.init(mode=WLAN.AP, ssid=config.AP_SSID, auth=(WLAN.WPA2, config.AP_PASSWORD), channel=config.AP_CHANNEL, antenna=WLAN.INT_ANT)
    print('AP on for {} secs'.format(config.AP_ON_TIME_SEC))
    pycom.rgbled(0x0000ff)
    _status_ap_enabled_once = True
    time.sleep(config.AP_ON_TIME_SEC)
    wlan.deinit()
    print('AP off')
    if _status_mb_got_request:
        pycom.rgbled(0x000000)
    else:
        pycom.rgbled(0x00ff00)

def _sample_sound():
    while True:
        try:
            exo.sound.sample()
            time.sleep_ms(1)
        except Exception as e:
            print("Sound sample error: {}".format(e))
            time.sleep(1)

def _read_thpa():
    while True:
        try:
            exo.thpa.read()
        except Exception as e:
            print("THPA read error: {}".format(e))
        time.sleep(1)

def _process_modbus_rtu():
    global _status_mb_got_request
    start_ms = time.ticks_ms()
    pycom.rgbled(0x00ff00)
    print('Modbus started')
    while True:
        try:
            if modbusrtu.process():
                if not _status_mb_got_request:
                    pycom.rgbled(0x000000)
                    _status_mb_got_request = True
            elif not _status_mb_got_request and config.AP_ON_MB_TIMEOUT_SEC > 0 \
                and not _status_ap_enabled_once \
                and time.ticks_diff(start_ms, time.ticks_ms()) >= config.AP_ON_MB_TIMEOUT_SEC * 1000:
                _thread.start_new_thread(_enable_ap, ())
        except Exception as e:
            print("Modbus RTU process error: {}".format(e))

if config.MB_ADDRESS > 0:
    exo = ExoSense()

    while True:
        try:
            exo.sound.init(
            )
            break
        except Exception as e:
            print("Sound init error: {}".format(e))
            time.sleep(1)

    while True:
        try:
            exo.light.init(
            )
            break
        except Exception as e:
            print("Light init error: {}".format(e))
            time.sleep(1)

    while True:
        try:
            exo.thpa.init(
                temp_offset=(config.TEMP_OFFSET - 5)
            )
            break
        except Exception as e:
            print("Light init error: {}".format(e))
            time.sleep(1)

    modbusrtu = ModbusRTU(
        exo=exo,
        enable_ap_func=_enable_ap,
        addr=config.MB_ADDRESS,
        baudrate=config.MB_BAUDRATE,
        data_bits=config.MB_DATA_BITS,
        stop_bits=config.MB_STOP_BITS,
        parity=UART.ODD if config.MB_PARITY == 2 else None if config.MB_PARITY == 3 else UART.EVEN,
        pins=(exo.PIN_TX, exo.PIN_RX),
        ctrl_pin=exo.PIN_TX_EN
    )

    _thread.start_new_thread(_sample_sound, ())
    _thread.start_new_thread(_read_thpa, ())
    _thread.start_new_thread(_process_modbus_rtu, ())

else:
    _enable_ap()
    print('Waiting for configuration...')
    while True:
        pycom.rgbled(0x000000)
        time.sleep(1)
        pycom.rgbled(0xff0000)
        time.sleep(1)
