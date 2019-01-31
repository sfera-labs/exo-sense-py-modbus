import uModBus.functions as functions
import uModBus.const as Const
from uModBus.common import Request
from uModBus.common import ModbusException
import struct
import socket
import machine
import time

class TCP:

    def __init__(self, slave_ip, slave_port=502, timeout=5):
        self._sock = socket.socket()
        self._sock.connect(socket.getaddrinfo(slave_ip, slave_port)[0][-1])
        self._sock.settimeout(timeout)

    def _create_mbap_hdr(self, slave_id, modbus_pdu):
        trans_id = machine.rng() & 0xFFFF
        mbap_hdr = struct.pack('>HHHB', trans_id, 0, len(modbus_pdu) + 1, slave_id)

        return mbap_hdr, trans_id

    def _bytes_to_bool(self, byte_list):
        bool_list = []
        for index, byte in enumerate(byte_list):
            bool_list.extend([bool(byte & (1 << n)) for n in range(8)])

        return bool_list

    def _to_short(self, byte_array, signed=True):
        response_quantity = int(len(byte_array) / 2)
        fmt = '>' + (('h' if signed else 'H') * response_quantity)

        return struct.unpack(fmt, byte_array)

    def _validate_resp_hdr(self, response, trans_id, slave_id, function_code, count=False):
        rec_tid, rec_pid, rec_len, rec_uid, rec_fc = struct.unpack('>HHHBB', response[:Const.MBAP_HDR_LENGTH + 1])
        if (trans_id != rec_tid):
            raise ValueError('wrong transaction Id')

        if (rec_pid != 0):
            raise ValueError('invalid protocol Id')

        if (slave_id != rec_uid):
            raise ValueError('wrong slave Id')

        if (rec_fc == (function_code + Const.ERROR_BIAS)):
            raise ValueError('slave returned exception code: {:d}'.format(rec_fc))

        hdr_length = (Const.MBAP_HDR_LENGTH + 2) if count else (Const.MBAP_HDR_LENGTH + 1)

        return response[hdr_length:]

    def _send_receive(self, slave_id, modbus_pdu, count):
        mbap_hdr, trans_id = self._create_mbap_hdr(slave_id, modbus_pdu)
        self._sock.send(mbap_hdr + modbus_pdu)

        response = self._sock.recv(256)
        modbus_data = self._validate_resp_hdr(response, trans_id, slave_id, modbus_pdu[0], count)

        return modbus_data

    def read_coils(self, slave_addr, starting_addr, coil_qty):
        modbus_pdu = functions.read_coils(starting_addr, coil_qty)

        response = self._send_receive(slave_addr, modbus_pdu, True)
        status_pdu = self._bytes_to_bool(response)

        return status_pdu

    def read_discrete_inputs(self, slave_addr, starting_addr, input_qty):
        modbus_pdu = functions.read_discrete_inputs(starting_addr, input_qty)

        response = self._send_receive(slave_addr, modbus_pdu, True)
        status_pdu = self._bytes_to_bool(response)

        return status_pdu

    def read_holding_registers(self, slave_addr, starting_addr, register_qty, signed = True):
        modbus_pdu = functions.read_holding_registers(starting_addr, register_qty)

        response = self._send_receive(slave_addr, modbus_pdu, True)
        register_value = self._to_short(response, signed)

        return register_value

    def read_input_registers(self, slave_addr, starting_address, register_quantity, signed = True):
        modbus_pdu = functions.read_input_registers(starting_address, register_quantity)

        response = self._send_receive(slave_addr, modbus_pdu, True)
        register_value = self._to_short(response, signed)

        return register_value

    def write_single_coil(self, slave_addr, output_address, output_value):
        modbus_pdu = functions.write_single_coil(output_address, output_value)

        response = self._send_receive(slave_addr, modbus_pdu, False)
        operation_status = functions.validate_resp_data(response, Const.WRITE_SINGLE_COIL,
                                                        output_address, value=output_value, signed=False)

        return operation_status

    def write_single_register(self, slave_addr, register_address, register_value, signed=True):
        modbus_pdu = functions.write_single_register(register_address, register_value, signed)

        response = self._send_receive(slave_addr, modbus_pdu, False)
        operation_status = functions.validate_resp_data(response, Const.WRITE_SINGLE_REGISTER,
                                                        register_address, value=register_value, signed=signed)

        return operation_status

    def write_multiple_coils(self, slave_addr, starting_address, output_values):
        modbus_pdu = functions.write_multiple_coils(starting_address, output_values)

        response = self._send_receive(slave_addr, modbus_pdu, False)
        operation_status = functions.validate_resp_data(response, Const.WRITE_MULTIPLE_COILS,
                                                        starting_address, quantity=len(output_values))

        return operation_status

    def write_multiple_registers(self, slave_addr, starting_address, register_values, signed=True):
        modbus_pdu = functions.write_multiple_registers(starting_address, register_values, signed)

        response = self._send_receive(slave_addr, modbus_pdu, False)
        operation_status = functions.validate_resp_data(response, Const.WRITE_MULTIPLE_REGISTERS,
                                                        starting_address, quantity=len(register_values))

        return operation_status

class TCPServer:

    def __init__(self):
        self._sock = None
        self._client_sock = None

    def bind(self, local_ip, local_port=502):
        if self._client_sock:
            self._client_sock.close()
        if self._sock:
            self._sock.close()
        self._sock = socket.socket()
        self._sock.bind(socket.getaddrinfo(local_ip, local_port)[0][-1])
        self._sock.listen()

    def _send(self, modbus_pdu, slave_addr):
        size = len(modbus_pdu)
        fmt = 'B' * size
        adu = struct.pack('>HHHB' + fmt, self._req_tid, 0, size + 1, slave_addr, *modbus_pdu)
        self._client_sock.send(adu)

    def send_response(self, slave_addr, function_code, request_register_addr, request_register_qty, request_data, values=None, signed=True):
        modbus_pdu = functions.response(function_code, request_register_addr, request_register_qty, request_data, values, signed)
        self._send(modbus_pdu, slave_addr)

    def send_exception_response(self, slave_addr, function_code, exception_code):
        modbus_pdu = functions.exception_response(function_code, exception_code)
        self._send(modbus_pdu, slave_addr)

    def get_request(self, unit_addr_list=None, timeout=None):
        if self._sock == None:
            raise Exception('Modbus TCP server not bound')

        start_ms = time.ticks_ms()
        while True:
            elapsed = time.ticks_diff(start_ms, time.ticks_ms())
            if elapsed > timeout:
                return None

            if self._client_sock == None:
                accept_timeout = None if timeout == None else (timeout - elapsed) / 1000
            else:
                accept_timeout = 0
            self._sock.settimeout(accept_timeout)

            new_client_sock = None
            try:
                new_client_sock, client_address = self._sock.accept()
            except OSError as e:
                if e.args[0] != 11: # 11 = timeout expired
                    raise e

            if new_client_sock != None:
                if self._client_sock != None:
                    self._client_sock.close()
                self._client_sock = new_client_sock
                self._client_sock.settimeout(0.2) # recv() timeout

            if self._client_sock != None:
                try:
                    req = self._client_sock.recv(256)
                    if len(req) == 0:
                        # connection terminated
                        self._client_sock.close()
                        self._client_sock = None
                        continue

                    req_header_no_uid = req[:Const.MBAP_HDR_LENGTH - 1]
                    self._req_tid, req_pid, req_len = struct.unpack('>HHH', req_header_no_uid)
                    req_uid_and_pdu = req[Const.MBAP_HDR_LENGTH - 1:Const.MBAP_HDR_LENGTH + req_len - 1]

                except TimeoutError:
                    continue
                except Exception as e:
                    print("Modbus request error:", e)
                    self._client_sock.close()
                    self._client_sock = None
                    continue

                if (req_pid != 0):
                    print("Modbus request error: PID not 0")
                    self._client_sock.close()
                    self._client_sock = None
                    continue

                if unit_addr_list != None and req_uid_and_pdu[0] not in unit_addr_list:
                    continue

                try:
                    return Request(self, req_uid_and_pdu)
                except ModbusException as e:
                    self.send_exception_response(req[0], e.function_code, e.exception_code)
