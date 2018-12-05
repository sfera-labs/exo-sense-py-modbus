class OPT3001:
    def __init__(self, i2c_device=None, addr=0x44):
        self._i2c = i2c_device
        self._addr = addr

    def init(self, i2c_device, addr=0x44):
        self._i2c = i2c_device
        self._addr = addr

    def configure(self, range_number=0b1100, conversion_time=0b1,
            mode_of_conversion_operation=0b10, latch=0b1, polariy=0b0,
            mask_exponent=0b0, fault_count=0b0):
        hb = range_number << 4
        hb |= conversion_time << 3
        hb |= mode_of_conversion_operation << 1
        hb |= mode_of_conversion_operation << 1
        lb = latch << 4
        lb |= polariy << 3
        lb |= mask_exponent << 2
        lb |= fault_count
        self._write_register(0x01, hb, lb)

    def read_configuration_register(self):
        return self._read_register(0x01)

    def set_low_limit(self, exp=0, result=0):
        hb = exp << 4
        hb |= (result >> 8) & 0x0F
        lb = result & 0xFF
        self._write_register(0x02, hb, lb)

    def set_high_limit(self, exp=0xB, result=0xFFF):
        hb = exp << 4
        hb |= (result >> 8) & 0x0F
        lb = result & 0xFF
        self._write_register(0x03, hb, lb)

    def manufacturer_id(self):
        return self._read_register(0x7E)

    def device_id(self):
        return self._read_register(0x7F)

    def lux(self):
        v = self._read_register(0x00)
        man = v & 0x0FFF
        exp = (v & 0xF000) >> 12
        return man * 0.01 * (2 ** exp)

    def _read_register(self, addr):
        bb = self._i2c.readfrom_mem(self._addr, addr, 2)
        return (bb[0] << 8) | bb[1]

    def _write_register(self, addr, hb, lb):
        return self._i2c.writeto_mem(self._addr, addr, bytes([hb, lb]))
