from machine import Pin
from machine import ADC
from machine import I2C
import pycom
import time
import math
from .opt3001 import OPT3001
from . import bme680
from .bme680 import constants as thpa_const

class ExoPin:
    def __init__(self, id, pin, mode, pull=None):
        self._pin = Pin(pin, mode=mode, pull=pull)
        self._exo_id = id

    def __call__(self, val=None):
        if val is None:
            return self._pin()
        else:
            self._pin(val)

    def id(self):
        return self._exo_id

    def __getattr__(self, attr):
        return getattr(self._pin, attr)

class Sound:
    def __init__(self, pin):
        self._pin = pin
        self._chan = None
        self._buff = None

    def init(self, avg_samples=100, peak_samples=10, peak_return_time=500):
        self._chan = ADC().channel(pin=self._pin, attn=ADC.ATTN_11DB)
        self._buff = [0] * (avg_samples if avg_samples > peak_samples else peak_samples)
        self._avg_samples = avg_samples
        self._peak_samples = peak_samples
        self._peak_return_time = peak_return_time
        self._peak_true = 0
        self._peak_ret = 0
        self._peak_ts = time.ticks_ms();

    def read(self):
        if self._chan is None:
            raise Exception('Not initialized')
        return self._chan()

    def sample(self):
        if self._buff is None:
            raise Exception('Not initialized')
        if self._avg_samples <= 0 and self._peak_samples <= 0:
            raise Exception('No buffer')
        s = 0
        for x in range(10):
            s += self.read()
        s /= 10
        self._buff.pop(0)
        self._buff.append(s)
        if self._peak_samples > 0:
            t = time.ticks_ms()
            dt = time.ticks_diff(self._peak_ts, t)
            val = sum(self._buff[-self._peak_samples:])/self._peak_samples
            self._peak_ret = self._peak_true * math.exp(-dt / self._peak_return_time)
            if (val > self._peak_ret):
                self._peak_ret = val
                self._peak_true = val
                self._peak_ts = t

    def avg(self):
        return int(sum(self._buff[-self._avg_samples:])/self._avg_samples)

    def peak(self):
        return int(self._peak_ret)

class Light(OPT3001):
    def __init__(self, exo, addr):
        super().__init__()
        self._exo = exo

    def init(self, range_number=0b1100, conversion_time=0b1,
            mode_of_conversion_operation=0b10, latch=0b1, polariy=0b0,
            mask_exponent=0b0, fault_count=0b0):
        super().init(self._exo._getI2C(), self._addr)
        super().configure(range_number, conversion_time,
                mode_of_conversion_operation, latch, polariy,
                mask_exponent, fault_count)

class THPA:
    def __init__(self, exo, addr):
        self._exo = exo
        self._addr = addr
        self._bme = None
        self._temperature = None
        self._humidity = None
        self._pressure = None
        self._gas_resistance = None

    def init(self, humidity_oversample=thpa_const.OS_2X,
            pressure_oversample=thpa_const.OS_4X, temperature_oversample=thpa_const.OS_8X,
            filter=thpa_const.FILTER_SIZE_3, temp_offset=0, gas_heater_temperature=320,
            gas_heater_duration=150):
        self._bme = bme680.BME680(i2c_addr=self._addr, i2c_device=self._exo._getI2C())

        self._bme.set_humidity_oversample(humidity_oversample)
        self._bme.set_pressure_oversample(pressure_oversample)
        self._bme.set_temperature_oversample(temperature_oversample)
        self._bme.set_filter(filter)
        self._bme.set_temp_offset(temp_offset)
        self._bme.set_gas_heater_temperature(gas_heater_temperature)
        self._bme.set_gas_heater_duration(gas_heater_duration)
        self._bme.select_gas_heater_profile(0)

    def read(self):
        if self._bme.get_sensor_data():
            self._temperature = self._bme.data.temperature
            self._humidity = self._bme.data.humidity
            self._pressure = self._bme.data.pressure
            if self._bme.data.heat_stable:
                self._gas_resistance = self._bme.data.gas_resistance

    def temperature(self):
        return self._temperature

    def humidity(self):
        return self._humidity

    def pressure(self):
        return self._pressure

    def gas_resistance(self):
        return self._gas_resistance

class Pir:
    # TODO
    def __init__(self, pin):
        self._pin = Pin(pin, mode=Pin.IN, pull=None)

    def init(self):
        pass

class I2CWrap(I2C):
    def read_byte_data(self, addr, register):
        return self.readfrom_mem(addr, register, 1)[0]

    def read_i2c_block_data(self, addr, register, length):
        return self.readfrom_mem(addr, register, length)

    def write_byte_data(self, addr, register, data):
        return self.writeto_mem(addr, register, data)

    def write_i2c_block_data(self, addr, register, data):
        return self.writeto_mem(addr, register, data)

class ExoSense:
    def __init__(self):
        self.PIN_DI1 = 'P18'
        self.PIN_DI2 = 'P17'
        self.PIN_TTL1 = 'P20'
        self.PIN_TTL1 = 'P19'
        self.PIN_DO1 = 'P23'
        self.PIN_TX = 'P3'
        self.PIN_RX = 'P4'
        self.PIN_TX_EN = 'P12'
        self.PIN_PIR = 'P16'
        self.PIN_BUZZER = 'P8'
        self.PIN_MIC = 'P14'

        self.DI1 = ExoPin('DI1', self.PIN_DI1, mode=Pin.IN, pull=None)
        self.DI2 = ExoPin('DI2', self.PIN_DI2, mode=Pin.IN, pull=None)
        self.DO1 = ExoPin('DO1', self.PIN_DO1, mode=Pin.OUT)

        self.buzzer = Pin(self.PIN_BUZZER, mode=Pin.OUT)
        self.pir = Pir(self.PIN_PIR)
        self.sound = Sound(self.PIN_MIC)
        self.light = Light(self, 0x44)
        self.thpa = THPA(self, 0x77)

        Pin(self.PIN_TX, mode=Pin.OUT)
        Pin(self.PIN_RX, mode=Pin.IN, pull=None)

        self._i2c = None

    def _getI2C(self):
        if self._i2c is None:
            self._i2c = I2CWrap(0, baudrate=400000)
        return self._i2c
