import uModBus.const as Const
import struct

class Request:
    def __init__(self, interface, data):
        self._itf = interface
        self.unit_addr = data[0]
        self.function, self.register_addr = struct.unpack_from('>BH', data, 1)

        if self.function in [Const.READ_COILS, Const.READ_DISCRETE_INPUTS]:
            self.quantity = struct.unpack_from('>H', data, 4)[0]
            if self.quantity < 0x0001 or self.quantity > 0x07D0:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)
            self.data = None

        elif self.function in [Const.READ_HOLDING_REGISTERS, Const.READ_INPUT_REGISTER]:
            self.quantity = struct.unpack_from('>H', data, 4)[0]
            if self.quantity < 0x0001 or self.quantity > 0x007D:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)
            self.data = None

        elif self.function == Const.WRITE_SINGLE_COIL:
            self.quantity = None
            self.data = data[4:6]
            # allowed values: 0x0000 or 0xFF00
            if (self.data[0] not in [0x00, 0xFF]) or self.data[1] != 0x00:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)

        elif self.function == Const.WRITE_SINGLE_REGISTER:
            self.quantity = None
            self.data = data[4:6]
            # all values allowed

        elif self.function == Const.WRITE_MULTIPLE_COILS:
            self.quantity = struct.unpack_from('>H', data, 4)[0]
            if self.quantity < 0x0001 or self.quantity > 0x07D0:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)
            self.data = data[7:]
            if len(self.data) != ((self.quantity - 1) // 8) + 1:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)

        elif self.function == Const.WRITE_MULTIPLE_REGISTERS:
            self.quantity = struct.unpack_from('>H', data, 4)[0]
            if self.quantity < 0x0001 or self.quantity > 0x007B:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)
            self.data = data[7:]
            if len(self.data) != self.quantity * 2:
                raise ModbusException(self.function, Const.ILLEGAL_DATA_VALUE)

        else:
            # Not implemented functions
            self.quantity = None
            self.data = data[4:]

    def send_response(self, values=None, signed=True):
        self._itf.send_response(self.unit_addr, self.function, self.register_addr, self.quantity, self.data, values, signed)

    def send_exception(self, exception_code):
        self._itf.send_exception_response(self.unit_addr, self.function, exception_code)

    def data_as_bits(self):
        bits = []
        for byte in self.data:
            for i in range(0, 8):
                bits.append((byte >> i) & 1)
                if len(bits) == self.quantity:
                    return bits

    def data_as_registers(self, signed=True):
        qty = self.quantity if (self.quantity != None) else 1
        fmt = ('h' if signed else 'H') * qty
        return struct.unpack('>' + fmt, self.data)

class ModbusException(Exception):
    def __init__(self, function_code, exception_code):
        self.function_code = function_code
        self.exception_code = exception_code
