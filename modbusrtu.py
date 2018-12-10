from uModbus.serial import Serial
from machine import UART
import _thread

class ModbusRTU:
    def __init__(self, exo, addr, baudrate=19200, data_bits=8, stop_bits=1, parity=UART.EVEN, pins=None, ctrl_pin=None):
        self._exo = exo
        self._addr = [addr]
        self._itf = Serial(
            uart_id=1,
            baudrate=baudrate,
            data_bits=data_bits,
            stop_bits=stop_bits,
            parity=parity,
            pins=pins,
            ctrl_pin=ctrl_pin
        )

    def _beep(self, ms):
        self._exo.buzzer(1)
        time.sleep_ms(ms)
        self._exo.buzzer(0)

    def _do1_pulse(self, ms):
        self._exo.DO1(1)
        time.sleep_ms(ms)
        self._exo.DO1(0)

    def process(self):
        request = self._itf.get_request(unit_addr_list=self._addr, timeout=2000)

        if request == None:
            print("=========")
            return

        print("Got request")
        print("Unit addr: {}".format(request.unit_addr))
        print("Function: {}".format(request.function))
        print("Starting register addr: {}".format(request.register_addr))
        print("Quantity: {}".format(request.quantity))
        print("Data: {}".format(request.data))

        if request.function == ModbusConst.READ_DISCRETE_INPUTS:
            if request.register_addr >= 101 and request.register_addr <= 102:
                vals = []
                for i in range(request.register_addr, request.register_addr + request.quantity):
                    if i == 101:
                        vals.append(self._exo.DI1())
                    elif i == 102:
                        vals.append(self._exo.DI2())
                    else:
                        request.send_exception(ModbusConst.ILLEGAL_DATA_ADDRESS)
                        break
                request.send_response(vals)
            else:
                request.send_exception(ModbusConst.ILLEGAL_DATA_ADDRESS)

        elif request.function == ModbusConst.READ_COILS:
            if request.register_addr == 201:
                request.send_response([self._exo.DO1()])
            elif request.register_addr == 151:
                ttl1 = Pin(self._exo.PIN_TTL1, mode=Pin.IN, pull=None)
                request.send_response([ttl1()])
            elif request.register_addr == 152:
                ttl2 = Pin(self._exo.PIN_TTL2, mode=Pin.IN, pull=None)
                request.send_response([ttl2()])
            else:
                request.send_exception(ModbusConst.ILLEGAL_DATA_ADDRESS)

        elif request.function == ModbusConst.WRITE_SINGLE_COIL:
            if request.register_addr == 201:
                if request.data[0] == 0x00:
                    self._exo.DO1(0)
                    request.send_response()
                elif request.data[0] == 0xFF:
                    self._exo.DO1(1)
                    request.send_response()
                else:
                    request.send_exception(ModbusConst.ILLEGAL_DATA_VALUE)
            elif request.register_addr == 151:
                ttl1 = Pin(self._exo.PIN_TTL1, mode=Pin.OUT)
                if request.data[0] == 0x00:
                    ttl1(0)
                    request.send_response()
                elif request.data[0] == 0xFF:
                    ttl1(1)
                    request.send_response()
                else:
                    request.send_exception(ModbusConst.ILLEGAL_DATA_VALUE)
            elif request.register_addr == 152:
                ttl2 = Pin(self._exo.PIN_TTL2, mode=Pin.OUT)
                if request.data[0] == 0x00:
                    ttl2(0)
                    request.send_response()
                elif request.data[0] == 0xFF:
                    ttl2(1)
                    request.send_response()
                else:
                    request.send_exception(ModbusConst.ILLEGAL_DATA_VALUE)
            else:
                request.send_exception(ModbusConst.ILLEGAL_DATA_ADDRESS)

        elif request.function == ModbusConst.READ_INPUT_REGISTER:
            if request.register_addr == 301:
                request.send_response([int(self._exo.thpa.temperature() * 10)], signed=True)
            elif request.register_addr == 401:
                request.send_response([int(self._exo.thpa.humidity() * 10)], signed=False)
            elif request.register_addr == 501:
                request.send_response([int(self._exo.thpa.pressure() * 10)], signed=False)
            elif request.register_addr == 601:
                request.send_response([self._exo.thpa.gas_resistance() // 1000], signed=False)
            elif request.register_addr == 701:
                request.send_response([int(self._exo.light.lux() * 10)], signed=False)
            elif request.register_addr >= 801 and request.register_addr <= 802:
                vals = []
                for i in range(request.register_addr, request.register_addr + request.quantity):
                    if i == 801:
                        vals.append(self._exo.sound.avg())
                    elif i == 802:
                        vals.append(self._exo.sound.peak())
                    else:
                        request.send_exception(ModbusConst.ILLEGAL_DATA_ADDRESS)
                        break
                request.send_response(vals, signed=False)
            else:
                request.send_exception(ModbusConst.ILLEGAL_DATA_ADDRESS)

        elif request.function == ModbusConst.WRITE_SINGLE_REGISTER:
            if request.register_addr == 901:
                val = request.data_as_registers(signed=False)[0]
                _thread.start_new_thread(self._beep, (val,))
            if request.register_addr == 211:
                val = request.data_as_registers(signed=False)[0]
                _thread.start_new_thread(self._do1_pulse, (val,))
            else:
                request.send_exception(ModbusConst.ILLEGAL_DATA_ADDRESS)

        else:
            request.send_exception(ModbusConst.ILLEGAL_FUNCTION)
