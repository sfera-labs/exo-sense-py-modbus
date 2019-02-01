import time
import _thread
import pycom
import machine
import uos
from exosense import ExoSense
from modbus import ModbusRTU
from modbus import ModbusTCP

def _disable_config_check():
    try:
        global _config_check_alarm
        if _config_check_alarm != None:
            _config_check_alarm.cancel()
            _config_check_alarm = None
            print('Config check stopped')
    except Exception as e:
        print('Exception in _disable_config_check():', e)

def _enable_config_check():
    try:
        global _config_check_alarm
        if _config_check_alarm == None:
            _config_check_alarm = machine.Timer.Alarm(_config_check, 5, periodic=True)
            print('Config check started')
    except Exception as e:
        print('Exception in _enable_config_check():', e)

def _config_check(alarm):
    try:
        if _config_stat != _get_config_stat():
            print('Config changed - restarting in 5 secs...')
            alarm.cancel()
            time.sleep(5)
            machine.reset()
    except Exception as e:
        print('Exception in _config_check():', e)

def _get_config_stat():
    try:
        return uos.stat("config.py")
    except Exception as e:
        return None

def _enable_ap(feed_wdt=False):
    try:
        global _status_ap_enabled_once
        pycom.rgbled(0xffff00)
        wlan.deinit()
        time.sleep(1)
        wlan.init(mode=WLAN.AP, ssid=config_AP_SSID, auth=(WLAN.WPA2, config_AP_PASSWORD), channel=config_AP_CHANNEL, antenna=WLAN.INT_ANT)
        print("AP '{}' on for {} secs".format(config_AP_SSID, config_AP_ON_TIME_SEC))
        pycom.rgbled(0x0000ff)
        _status_ap_enabled_once = True

        _enable_config_check()

        start_ms = time.ticks_ms()
        while time.ticks_diff(start_ms, time.ticks_ms()) < config_AP_ON_TIME_SEC * 1000:
            print('.', end='')
            if feed_wdt:
                _wdt.feed()
            time.sleep(1)

        wlan.deinit()
        print('AP off')

        _disable_config_check()

        if _status_mb_got_request:
            pycom.rgbled(0x000000)
        else:
            pycom.rgbled(0x00ff00)
    except Exception as e:
        print('Exception in _enable_ap():', e)
        raise e

def _connect_wifi():
    try:
        pycom.rgbled(0xff0030)
        wlan.deinit()
        time.sleep(1)
        wlan.init(mode=WLAN.STA)
        if config.MB_TCP_IP == 'dhcp':
            wlan.ifconfig(config=('dhcp'))
        else:
            wlan.ifconfig(config=(config.MB_TCP_IP, config.MB_TCP_MASK, config.MB_TCP_GW, config.MB_TCP_DNS))

        if config.MB_TCP_WIFI_SEC == 0:
            auth = (None, None)
        elif config.MB_TCP_WIFI_SEC == 1:
            auth = (WLAN.WEP, config.MB_TCP_WIFI_PWD)
        elif config.MB_TCP_WIFI_SEC == 2:
            auth = (WLAN.WPA, config.MB_TCP_WIFI_PWD)
        else:
            auth = (WLAN.WPA2, config.MB_TCP_WIFI_PWD)

        print("Connecting to WiFi '{}'...".format(config.MB_TCP_WIFI_SSID))
        wlan.connect(ssid=config.MB_TCP_WIFI_SSID, auth=auth)

        blink = True
        start_ms = time.ticks_ms()
        while not wlan.isconnected():
            print('.', end='')
            if not _status_mb_got_request and config.AP_ON_TIMEOUT_SEC > 0 \
                and not _status_ap_enabled_once \
                and time.ticks_diff(start_ms, time.ticks_ms()) >= config.AP_ON_TIMEOUT_SEC * 1000:
                print('WiFi connection timeout')
                wlan.disconnect()
                _enable_ap(True)
                return False
            blink = not blink
            pycom.rgbled(0xff0030 if blink else 0x000000)
            _wdt.feed()
            time.sleep(0.3)

        print("Connected!")
        print(wlan.ifconfig())

        if _status_mb_got_request:
            pycom.rgbled(0x000000)
        else:
            pycom.rgbled(0x00ff00)

        return True
    except Exception as e:
        print('Exception in _connect_wifi():', e)
        raise e

def _sample_sound():
    while True:
        try:
            _exo.sound.sample()
            time.sleep_ms(1)
        except Exception as e:
            print("Sound sample error: {}".format(e))
            time.sleep(1)

def _read_thpa():
    for i in range(10):
        try:
            _exo.thpa.read()
        except Exception as e:
            print("THPA read error: {}".format(e))
    while True:
        try:
            _exo.thpa.read()
        except Exception as e:
            print("THPA read error: {}".format(e))
        time.sleep(5)

def _process_modbus_rtu():
    global _status_mb_got_request
    modbusrtu = ModbusRTU(
        exo=_exo,
        enable_ap_func=_enable_ap,
        addr=config.MB_RTU_ADDRESS,
        baudrate=config.MB_RTU_BAUDRATE,
        data_bits=config.MB_RTU_DATA_BITS,
        stop_bits=config.MB_RTU_STOP_BITS,
        parity=UART.ODD if config.MB_RTU_PARITY == 2 else None if config.MB_RTU_PARITY == 3 else UART.EVEN,
        pins=(_exo.PIN_TX, _exo.PIN_RX),
        ctrl_pin=_exo.PIN_TX_EN
    )
    start_ms = time.ticks_ms()
    pycom.rgbled(0x00ff00)
    print('Modbus RTU started - addr:', config.MB_RTU_ADDRESS)
    while True:
        try:
            if modbusrtu.process():
                if not _status_mb_got_request:
                    pycom.rgbled(0x000000)
                    _status_mb_got_request = True
            elif not _status_mb_got_request and config.AP_ON_TIMEOUT_SEC > 0 \
                and not _status_ap_enabled_once \
                and time.ticks_diff(start_ms, time.ticks_ms()) >= config.AP_ON_TIMEOUT_SEC * 1000:
                _thread.start_new_thread(_enable_ap, ())
            _wdt.feed()
        except Exception as e:
            print("Modbus RTU process error: {}".format(e))
            time.sleep(1)

def _process_modbus_tcp():
    global _status_mb_got_request
    modbustcp = ModbusTCP(exo=_exo)
    pycom.rgbled(0x00ff00)
    while True:
        try:
            if wlan.isconnected():
                if modbustcp.process():
                    if not _status_mb_got_request:
                        pycom.rgbled(0x000000)
                        _status_mb_got_request = True
            else:
                if _connect_wifi():
                    _enable_config_check()
                    local_ip = wlan.ifconfig()[0]
                    modbustcp.bind(local_ip=local_ip, local_port=config.MB_TCP_PORT)
                    print('Modbus TCP started on {}:{}'.format(local_ip, config.MB_TCP_PORT))

            _wdt.feed()

        except Exception as e:
            print("Modbus TCP process error: {}".format(e))
            time.sleep(1)

# main =========================================================================

try:
    import config
    config_AP_SSID = config.AP_SSID
    config_AP_PASSWORD = config.AP_PASSWORD
    config_AP_CHANNEL = config.AP_CHANNEL
    config_AP_ON_TIME_SEC = config.AP_ON_TIME_SEC
    config_FTP_USER = config.FTP_USER
    config_FTP_PASSWORD = config.FTP_PASSWORD
    config_ERROR = False
except Exception:
    print('Configuration error - Starting with default configuration')
    config_AP_SSID = 'ExoSensePy'
    config_AP_PASSWORD = 'exosense'
    config_AP_CHANNEL = 7
    config_AP_ON_TIME_SEC = 600
    config_FTP_USER = 'exo'
    config_FTP_PASSWORD = 'sense'
    config_ERROR = True

try:
    if config_AP_ON_TIME_SEC < 120:
        config_AP_ON_TIME_SEC = 120

    server = Server()
    server.deinit()
    server.init(login=(config_FTP_USER, config_FTP_PASSWORD))

    _config_check_alarm = None
    _config_stat = _get_config_stat()

    if not config_ERROR and (config.MB_RTU_ADDRESS > 0 or len(config.MB_TCP_IP) > 0):
        _exo = ExoSense()
        _wdt = machine.WDT(timeout=20000)
        _status_ap_enabled_once = False
        _status_mb_got_request = False

        while True:
            try:
                _exo.sound.init()
                break
            except Exception as e:
                print("Sound init error: {}".format(e))
                time.sleep(1)

        while True:
            try:
                _exo.light.init()
                break
            except Exception as e:
                print("Light init error: {}".format(e))
                time.sleep(1)

        while True:
            try:
                _exo.thpa.init(
                    temp_offset=(config.TEMP_OFFSET - 5)
                )
                break
            except Exception as e:
                print("Light init error: {}".format(e))
                time.sleep(1)

        _thread.start_new_thread(_sample_sound, ())
        _thread.start_new_thread(_read_thpa, ())

        if config.MB_RTU_ADDRESS > 0:
            _process_modbus_rtu()
        else:
            _process_modbus_tcp()

except Exception as e:
    print('Exception in main:', e)

_enable_ap()
print('Waiting for reboot...')
while True:
    pycom.rgbled(0x000000)
    time.sleep(1)
    pycom.rgbled(0xff0000)
    time.sleep(1)
