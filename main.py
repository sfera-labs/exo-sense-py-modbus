import time
import _thread
from exosense import ExoSense
from modbusrtu import ModbusRTU
import config

exo = ExoSense()
exo.sound.init()
exo.light.init()
exo.thpa.init()

modbusrtu = ModbusRTU(
    exo=exo,
    addr=config.ADDRESS,
    baudrate=config.BAUDRATE,
    data_bits=config.DATA_BITS,
    stop_bits=config.STOP_BITS,
    parity=UART.ODD if config.PARITY == 2 else None if config.PARITY == 3 else UART.EVEN,
    pins=(exo.PIN_TX, exo.PIN_RX),
    ctrl_pin=exo.PIN_TX_EN
    )

def _sample_sound():
    while True:
        try:
            exo.sound.sample()
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
    while True:
        try:
            modbusrtu.process()
        except Exception as e:
            print("Modbus RTU process error: {}".format(e))


_thread.start_new_thread(_sample_sound, ())
_thread.start_new_thread(_read_thpa, ())
_thread.start_new_thread(_process_modbus_rtu, ())

print('Press ENTER to enter the REPL')
input()
