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
        if avg_samples < 0 or peak_samples < 0 or peak_return_time < 0:
            raise Exception('Illegal arguments')
        self._chan = ADC().channel(pin=self._pin, attn=ADC.ATTN_11DB)
        self._avg_samples = int(avg_samples)
        self._avg_val = self._chan()
        self._peak_samples = int(peak_samples)
        self._peak_return_time = int(peak_return_time)
        self._peak_val = self._avg_val
        self._peak_true = self._avg_val
        self._peak_ret = self._avg_val
        self._peak_ts = time.ticks_ms();

    def read(self):
        if self._chan is None:
            raise Exception('Not initialized')
        return self._chan()

    def sample(self):
        if self._chan is None:
            raise Exception('Not initialized')
        s = 0
        for _ in range(5):
            s += self._chan()
        s //= 5
        if self._avg_samples > 0:
            self._avg_val = (self._avg_val * (self._avg_samples - 1) + s) // self._avg_samples
        if self._peak_samples > 0:
            t = time.ticks_ms()
            dt = time.ticks_diff(self._peak_ts, t)
            self._peak_val = (self._peak_val * (self._peak_samples - 1) + s) // self._peak_samples
            if dt < 0:
                self._peak_ret = self._peak_val
                self._peak_true = self._peak_val
                self._peak_ts = t
            else:
                self._peak_ret = self._peak_true * math.exp(-dt / self._peak_return_time)
                if (self._peak_val > self._peak_ret):
                    self._peak_ret = self._peak_val
                    self._peak_true = self._peak_val
                    self._peak_ts = t

    def avg(self):
        return self._avg_val

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
        self._iaq_score = None
        self._hum_avg = None
        self._gas_avg = None
        self._iaq_trend = None
        self._temp_offset = 0
        self._elevation = 0

    def init(self, humidity_oversample=thpa_const.OS_2X,
            pressure_oversample=thpa_const.OS_4X, temperature_oversample=thpa_const.OS_8X,
            filter=thpa_const.FILTER_SIZE_3, temp_offset=0, gas_heater_temperature=320,
            gas_heater_duration=150, elevation=0, iaq_gas_ref=150000, iaq_humidity_ref=40,
            iaq_gas_weight=75, iaq_samples=100):
        self._bme = bme680.BME680(i2c_addr=self._addr, i2c_device=self._exo._getI2C())
        self._bme.set_humidity_oversample(humidity_oversample)
        self._bme.set_pressure_oversample(pressure_oversample)
        self._bme.set_temperature_oversample(temperature_oversample)
        self._bme.set_filter(filter)
        self._bme.set_gas_heater_temperature(gas_heater_temperature)
        self._bme.set_gas_heater_duration(gas_heater_duration)
        self._bme.select_gas_heater_profile(0)
        self._temp_offset = temp_offset
        self._elevation = elevation
        self._iaq_gas_ref = iaq_gas_ref
        self._iaq_hum_ref = iaq_humidity_ref
        self._iaq_gas_weight = iaq_gas_weight
        self._iaq_hum_weight = 100 - iaq_gas_weight
        self._iaq_samples = iaq_samples

    def _process_iaq(self):
        # humidity
        if self._hum_avg is None:
            self._hum_avg = self._humidity
        else:
            self._hum_avg = (self._hum_avg * (self._iaq_samples - 1) + self._humidity) / self._iaq_samples

        hum_affinity = 100 - abs(self._hum_avg - self._iaq_hum_ref)
        hum_weighted_score = hum_affinity * self._iaq_hum_weight / 100

        # gas
        if self._gas_avg is None:
            self._gas_avg = self._gas_resistance
        else:
            self._gas_avg = (self._gas_avg * (self._iaq_samples - 1) + self._gas_resistance) / self._iaq_samples

        gas_weighted_score = self._gas_avg * self._iaq_gas_weight / self._iaq_gas_ref
        if gas_weighted_score > self._iaq_gas_weight:
            gas_weighted_score_lim = self._iaq_gas_weight
        else:
            gas_weighted_score_lim = gas_weighted_score

        # iaq
        self._iaq_score = int((100 - (hum_weighted_score + gas_weighted_score_lim)) * 5)

        # trend
        self._iaq_trend_score = hum_weighted_score + gas_weighted_score

        if self._iaq_trend is None:
            self._iaq_trend = 0
            self._iaq_trend_score_stable = self._iaq_trend_score
        else:
            iaq_trend = (self._iaq_trend_score - self._iaq_trend_score_prev) * 100
            self._iaq_trend = (self._iaq_trend_prev * 9 + iaq_trend) / 10
            if self._iaq_trend == 0 or (self._iaq_trend * self._iaq_trend_prev) < 0: # sign inversion
                self._iaq_trend_score_stable = self._iaq_trend_score

        self._iaq_trend_score_prev = self._iaq_trend_score
        self._iaq_trend_prev = self._iaq_trend

        if (0 < self._iaq_trend < 1) and (self._iaq_trend_score > self._iaq_trend_score_stable + 1):
            self._iaq_trend = 1
        elif (-1 < self._iaq_trend < 0) and (self._iaq_trend_score < self._iaq_trend_score_stable - 1):
            self._iaq_trend = -1

    def read(self):
        if self._bme.get_sensor_data():
            self._temperature = self._bme.data.temperature + self._temp_offset
            hum = self._bme.data.humidity / (10 ** (0.032 * self._temp_offset))
            if hum > 100:
                hum = 100
            self._humidity = hum
            self._pressure = self._bme.data.pressure / math.exp(-self._elevation / 8400)
            if self._bme.data.heat_stable:
                self._gas_resistance = self._bme.data.gas_resistance
                self._process_iaq()
            return True
        return False

    def temperature(self):
        return self._temperature

    def humidity(self):
        return self._humidity

    def pressure(self):
        return self._pressure

    def gas_resistance(self):
        return self._gas_resistance

    def iaq(self):
        return self._iaq_score

    def iaq_trend(self):
        if self._iaq_trend is None:
            return None
        return int(self._iaq_trend)

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
        self.PIN_TTL2 = 'P19'
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
