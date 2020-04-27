# -*- coding: utf-8 -*-
'''
Created on 2020/04
@author: InHand
'''

import logging
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp
from modbus_tk import modbus_rtu
import serial
import time
import re
import math


class Utility(object):
    """
    data format transfer
    """
    @staticmethod
    def ieee754Int2Float(a, p):
        f = ((-1) ** ((a & 0x80000000) >> 31)) * (2 ** (((abs(a) & 0x7f800000) >> 23) - 127)) * \
            (1 + ((abs(a) & 0x7fffff) * 1.0 / (2 ** 23)))
        return round(f, p)

    # ieee754
    @staticmethod
    def Float2ieee754Words(f, byte_order):
        if f == 0:
            return [0, 0]
        words = []
        signedBit = 0 if f > 0 else 1
        stepBits = int(math.floor(math.log(abs(f), 2)))
        tailBits = int(((abs(f) / (2 ** stepBits)) - 1) * (2 ** 23)) if stepBits > 0 else int(
            (abs(f) / (2 ** stepBits)) * (2 ** 23))  # int(((f/(2**stepBits))-1) * (2**23))
        dw = ((signedBit << 31) & 0x80000000) | (((stepBits + 127) << 23) & 0x7f800000) | (tailBits & 0x7fffff)
        wh = (dw & 0xffff0000) >> 16
        wl = dw & 0xffff
        if re.search(r'(^cdab$)', byte_order) is not None:
            words.append(wl)
            words.append(wh)
        elif re.search(r'(^abcd$)', byte_order) is not None:
            words.append(wh)
            words.append(wl)
        elif re.search(r'(^badc$)', byte_order) is not None:
            words.append(((wh & 0xff) << 8) | ((wh & 0xff00) >> 8))
            words.append(((wl & 0xff) << 8) | ((wl & 0xff00) >> 8))
        else:  # r'(^dcba$)'
            words.append(((wl & 0xff) << 8) | ((wl & 0xff00) >> 8))
            words.append(((wh & 0xff) << 8) | ((wh & 0xff00) >> 8))
        return words

    @staticmethod
    def ieee754Words2Float(wl, wh, p):
        a = wh << 16 | wl
        return Utility.ieee754Int2Float(a, p)

    # int -> words[2]
    @staticmethod
    def toWords(d, byte_order):
        wh = (abs(d) & 0xffff0000) >> 16
        wl = abs(d) & 0xffff
        words = []
        if d < 0:
            wh = wh | 0x8000
        if re.search(r'(^cdab$)', byte_order) is not None:
            words.append(wl)
            words.append(wh)
        elif re.search(r'(^abcd$)', byte_order) is not None:
            words.append(wh)
            words.append(wl)
        elif re.search(r'(^badc$)', byte_order) is not None:
            words.append(((wh & 0xff) << 8) | ((wh & 0xff00) >> 8))
            words.append(((wl & 0xff) << 8) | ((wl & 0xff00) >> 8))
        else:  # r'(^dcba$)'
            words.append(((wl & 0xff) << 8) | ((wl & 0xff00) >> 8))
            words.append(((wh & 0xff) << 8) | ((wh & 0xff00) >> 8))
        return words

    # bytes[2] -> word
    @staticmethod
    def toWord(value, byte_order):
        if re.search(r'(^ba($|dc$))|(^dcba$)', byte_order) is not None:
            h_byte = ((value & 0xff00) >> 8)
            l_byte = (value & 0xff)
            return ((l_byte << 8) & 0xff00) | h_byte
        return value

    # words[2] -> double words (udint)
    @staticmethod
    def toDWord(l0, h0, l1, h1, byte_order, vtype):
        if re.search(r'^dcba$', byte_order) is not None:
            t = ((l1 & 0xff) << 24) | (h1 << 16) | (l0 << 8) | h0
        elif re.search(r'^cdab$', byte_order) is not None:
            t = ((h1 & 0xff) << 24) | (l1 << 16) | (h0 << 8) | l0
        elif re.search(r'^badc$', byte_order) is not None:
            t = ((l0 & 0xff) << 24) | (h0 << 16) | (l1 << 8) | h1
        else:
            t = ((h0 & 0xff) << 24) | (l0 << 16) | (h1 << 8) | l1
        return t

    @staticmethod
    def toSint(values):
        sbit = values[0] & 0x80
        if sbit:
            value = ((~values[0]) & 0x7f) + 1
            return -1 * value
        else:
            value = values[0] & 0xff
            return value

    # words[2] -> double words (dint)
    @staticmethod
    def toDInt(l0, h0, l1, h1, byte_order, vtype):
        if re.search(r'^dcba$', byte_order) is not None:
            s = (((l1 & 0x7f) << 24) & 0xff000000) | ((h1 << 16) & 0xff0000) | ((l0 << 8) & 0xff00) | (h0 & 0xff)
            t = s if (l1 & 0x80) == 0 else (0 - s)

        elif re.search(r'^cdab$', byte_order) is not None:
            s = (((h1 & 0x7f) << 24) & 0xff000000) | ((l1 << 16) & 0xff0000) | ((h0 << 8) & 0xff00) | (l0 & 0xff)
            t = s if (h1 & 0x80) == 0 else (0 - s)

        elif re.search(r'^badc$', byte_order) is not None:
            s = (((l0 & 0x7f) << 24) & 0xff000000) | ((h0 << 16) & 0xff0000) | ((l1 << 8) & 0xff00) | (h1 & 0xff)
            t = s if (l0 & 0x80) == 0 else (0 - s)

        else:
            s = (((h0 & 0x7f) << 24) & 0xff000000) | ((l0 << 16) & 0xff0000) | ((h1 << 8) & 0xff00) | (l1 & 0xff)
            t = s if (h0 & 0x80) == 0 else (0 - s)
        return t

    # ieee754 , byte[4] -> float
    @staticmethod
    def toFloat(l0, h0, l1, h1, byte_order, vtype, float_repr):
        t = Utility.toDWord(l0, h0, l1, h1, byte_order, vtype)
        return Utility.ieee754Int2Float(t, float_repr)  # ieee754 converting, precision: default 2

    @staticmethod
    def get_bool(data, bool_index):
        """
        Get the boolean value from location in bytearray
        """
        index_value = 1 << bool_index
        current_value = data & index_value
        return current_value == index_value

    @staticmethod
    def set_bool(data, bool_index, value):
        """
        Set boolean value on location in bytearray
        """
        assert value in [0, 1, True, False]
        current_value = Utility.get_bool(data, bool_index)
        index_value = 1 << bool_index

        # check if bool already has correct value
        if current_value == value:
            return data
        else:
            return data ^ index_value


class MbValHandle(object):
    """
    Modbus handle class, for reading/writing data
    """
    def __init__(self, master, slave, name, addr, len, data_type, byte_order,
                 operation, register_bit=0, value=None):
        self.master = master
        self.slave = slave
        # self.type = type
        self.addr = addr
        self.len = len
        self.name = name
        self.data_type = data_type
        self.byte_order = byte_order
        self.operation = operation
        self.register_bit = register_bit
        self.value = value
        self.float_repr = 2
        self.command = None

    def __transfer_addr(self, address):
        """
        transter read address, it should be a integer
        :param address: modbus address
        :return: cmd , real address
        """
        var_addr = 0
        mb_type = None
        addr = int(address)
        if addr <= 10000:
            var_addr = addr - 1
            mb_type = cst.READ_COILS
        elif 10000 < addr <= 20000:
            var_addr = addr - 10001
            mb_type = cst.READ_DISCRETE_INPUTS
        elif 30000 < addr <= 40000:
            var_addr = addr - 30001
            mb_type = cst.READ_INPUT_REGISTERS
        elif 40000 < addr <= 50000:
            var_addr = addr - 40001
            mb_type = cst.READ_HOLDING_REGISTERS
        elif 100000 < addr <= 165535:
            var_addr = addr - 100001
            mb_type = cst.READ_DISCRETE_INPUTS
        elif 300000 < addr <= 365535:
            var_addr = addr - 300001
            mb_type = cst.READ_INPUT_REGISTERS
        elif 400000 < addr <= 465535:
            var_addr = addr - 400001
            mb_type = cst.READ_HOLDING_REGISTERS
        return mb_type, var_addr

    def __transfer_write_addr(self, address):
        """
        transfer write address
        :param address: modbus address, it should be a integer
        :return: cmd, real address
        """
        if address <= 10000:
            var_addr = address - 1
            mb_type = cst.WRITE_SINGLE_COIL
        elif 40000 < address <= 50000:
            var_addr = address - 40001
            mb_type = cst.WRITE_MULTIPLE_REGISTERS
        elif 400000 < address <= 465535:
            var_addr = address - 400001
            mb_type = cst.WRITE_MULTIPLE_REGISTERS
        else:
            return None, None
        return mb_type, var_addr

    def __get_mb_value(self, r, byte_order):
        """
         To give the value of according variable configuration
        :param v:
        :param r:
        :param byte_order:
        :return:
        """
        if re.match("string", self.data_type, re.M | re.I):
            var = []
            for a in r:
                h_byte = ((a & 0xff00) >> 8)
                l_byte = (a & 0xff)
                if not h_byte and not l_byte:
                    break
                h_char = chr(h_byte) if h_byte else ""
                l_char = chr(l_byte) if l_byte else ""
                if re.search(r'(^ab($|cd$))|(^cdab$)', byte_order) is not None:
                    var.append(h_char)
                    var.append(l_char)
                else:
                    var.append(l_char)
                    var.append(h_char)
            # logger.debug("get string data : %s" % ''.join(var))
            return ''.join(var)
        elif re.match("bit", self.data_type, re.M | re.I):
            data = r[0]
            if self.command == cst.READ_INPUT_REGISTERS or self.command == cst.READ_HOLDING_REGISTERS:
                data = Utility.get_bool(Utility.toWord(data, byte_order), self.register_bit)
            return 1 if data else 0
        elif re.match("bool", self.data_type, re.M | re.I):
            data = r[0]
            if self.command == cst.READ_INPUT_REGISTERS or self.command == cst.READ_HOLDING_REGISTERS:
                data = Utility.get_bool(Utility.toWord(data, byte_order), self.register_bit)
            return True if data else False
        elif re.match("dword", self.data_type, re.M | re.I) or re.match("ulong", self.data_type,
                                                                     re.M | re.I):  # unsigned 32 bit
            h0 = ((r[0] & 0xff00) >> 8)
            l0 = (r[0] & 0xff)
            h1 = ((r[1] & 0xff00) >> 8)
            l1 = (r[1] & 0xff)
            return Utility.toDWord(l0, h0, l1, h1, byte_order, self.data_type)
        elif re.match("word", self.data_type, re.M | re.I) or re.match("ushort", self.data_type,
                                                                    re.M | re.I):  # unsigned 16 bit
            h_byte = ((r[0] & 0xff00) >> 8)
            l_byte = (r[0] & 0xff)
            if re.search(r'(^ba($|dc$))|(^dcba$)', byte_order) is not None:
                t = ((l_byte << 8) & 0xff00) | h_byte
                return t
            else:
                return r[0]
        elif re.match("dint", self.data_type, re.M | re.I) or re.match("long", self.data_type,
                                                                    re.M | re.I):  # signed 32 bit
            h0 = ((r[0] & 0xff00) >> 8)
            l0 = (r[0] & 0xff)
            h1 = ((r[1] & 0xff00) >> 8)
            l1 = (r[1] & 0xff)
            return Utility.toDInt(l0, h0, l1, h1, byte_order, self.data_type)
        elif re.match("int", self.data_type, re.M | re.I) or re.match("short", self.data_type,
                                                                   re.M | re.I):  # signed 16 bit
            h_byte = ((r[0] & 0xff00) >> 8)
            l_byte = (r[0] & 0xff)
            if re.search(r'(^ba($|dc$))|(^dcba$)', byte_order) is not None:
                t = (((l_byte & 0x7f) << 8) & 0xff00) | h_byte
                return t if (l_byte & 0x80) == 0 else (t - 32768)
            else:
                return r[0] if (r[0] & 0x8000) == 0 else r[0] - 65536
        elif re.match("float", self.data_type, re.M | re.I):  # float 32 bit
            h0 = ((r[0] & 0xff00) >> 8)
            l0 = (r[0] & 0xff)
            h1 = ((r[1] & 0xff00) >> 8)
            l1 = (r[1] & 0xff)
            return Utility.toFloat(l0, h0, l1, h1, byte_order, self.data_type, self.float_repr)  # ieee754 converting
        elif re.match("sint", self.data_type, re.M | re.I):
            h_byte = ((r[0] & 0xff00) >> 8)
            l_byte = (r[0] & 0xff)
            if re.search(r'(^ba($|dc$))|(^dcba$)', byte_order) is not None:
                return [Utility.toSint(l_byte), Utility.toSint(h_byte)]
            else:
                return [Utility.toSint(h_byte), Utility.toSint(l_byte)]
        elif re.match("byte", self.data_type, re.M | re.I):
            h_byte = ((r[0] & 0xff00) >> 8)
            l_byte = (r[0] & 0xff)
            if re.search(r'(^ba($|dc$))|(^dcba$)', byte_order) is not None:
                return [l_byte, h_byte]
            else:
                return [h_byte, l_byte]
        else:
            var = []
            return var

    def read_data(self):
        """
        read each of modbus registers
        :return:
        """
        (cmd, addr) = self.__transfer_addr(self.addr)
        self.command = cmd
        try:
            val = dict()
            # print("reas slave: %s, cmd: %s, addr:%s, len: %s" % (self.slave, cmd, addr, self.len))
            var_raw_data = self.master.execute(self.slave, cmd, addr, self.len)
            if self.len == 1:
                var_raw_data = [var_raw_data[0], ]
            else:
                var_raw_data = var_raw_data[0: self.len]
            val['value'] = self.__get_mb_value(var_raw_data, self.byte_order)
            val['timestamp'] = int(time.time())
            val['name'] = self.name
            print("read data: %s" % val)
        except Exception as e:
            logging.error("read error: %s" % (e, ))
    
    def write_data(self, write_value):
        """
        write data to mosbus plc
        :param write_value: the value that will write
        :return:
        """
        try:
            byte_order = self.byte_order
            (cmd, mbAddr) = self.__transfer_write_addr(self.addr)
            if re.match("dint", self.data_type, re.M | re.I):
                value1 = int(write_value)
                if -2147483648 <= value1 <= 2147483647:
                    values = Utility.toWords(value1, byte_order)
                else:
                    raise ValueError("Invalid values: %s" % value1)
            elif re.match('dword', self.data_type, re.M | re.I):
                value1 = int(write_value)
                if 0 <= value1 <= 4294967295:
                    values = Utility.toWords(value1, byte_order)
                else:
                    raise ValueError("Invalid values: %s" % value1)
            elif re.match('float', self.data_type, re.M | re.I):
                value1 = float(write_value)
                values = Utility.Float2ieee754Words(value1, byte_order)
            elif re.match('int', self.data_type, re.M | re.I):
                value1 = int(write_value)
                if -32768 <= value1 <= 32767:
                    v = Utility.toWord(value1, byte_order)
                    values = [v, ]
                else:
                    raise ValueError("Invalid values: %s" % value1)
            elif re.match('word', self.data_type, re.M | re.I):
                value1 = int(write_value)
                if 0 <= value1 <= 65535:
                    v = Utility.toWord(value1, byte_order)
                    values = [v, ]
                else:
                    raise ValueError("Invalid values: %s" % value1)
            elif re.match('string', self.data_type, re.M | re.I):
                values = list()
                value1 = str(write_value)
                for v in [value1[i: i + 2] for i in range(0, len(value1), 2)]:
                    h_byte = ord(v[0])
                    l_byte = 0 if len(v) == 1 else ord(v[1])
                    if re.search(r'(^ab($|cd$))|(^cdab$)', byte_order) is not None:
                        values.append(((h_byte << 8) & 0xff00) | l_byte)
                    else:
                        values.append(((l_byte << 8) & 0xff00) | h_byte)
            elif re.match("bit", self.data_type, re.M | re.I) or re.match("bool", self.data_type, re.M | re.I):
                if isinstance(write_value, str):
                    write_value = eval(write_value)
                if cmd == cst.WRITE_MULTIPLE_REGISTERS:
                    s = self.master.execute(self.slave, cmd, mbAddr, self.len)
                    write_value = Utility.set_bool(Utility.toWord(s[0], byte_order), self.register_bit, write_value)
                    values = [write_value, ]
                else:
                    values = write_value
            else:
                raise ValueError("Data type %s are not supported." % self.data_type)
            print("Write var [modbus] name: %s, cmd: %s, mbAddr: %s, value: %s" % (
                self.name, cmd, mbAddr, values))
            self.master.execute(self.slave, cmd, mbAddr, output_value=values)
            print("write data: %s --> %s ok" % (values, mbAddr))
        except Exception as e:
            logging.error("write error: %s" % (e, ))


class MBMaster(object):
    def __init__(self, mbProto, mbVal):
        """
        build modbus master, read/write data
        :param mbProto: tcp/rtu settings, dict
        :param mbVal: each var settings, list
        """
        self.master = None
        self.instance_list = []
        self.mbProto = mbProto
        self.mbVal = mbVal
        self.stat = "init"

    def init(self):
        print("Found %s vars" % len(self.mbVal))
        if len(self.mbVal) == 0:
            logging.error("init modbus  error")
            return False
        if self.mbProto['type'] == 'TCP':
            try:
                self.master = modbus_tcp.TcpMaster(self.mbProto['hostname'], self.mbProto['port'],
                                                   self.mbProto['reconnect_interval'])
            except modbus_tk.modbus.ModbusError as exc:
                logging.error("error %s- Code=%d", exc, exc.get_exception_code())
                return False
        elif self.mbProto['type'] == 'RTU':
            try:
                serial_instance = serial.Serial(self.mbProto['serialPort'], self.mbProto['baudrate'],
                                                self.mbProto['bytesize'], self.mbProto['parity'],
                                                self.mbProto['stopbits'], xonxoff=0)
                self.master = modbus_rtu.RtuMaster(serial_instance)
                ret = self.master.open()
            except modbus_tk.modbus.ModbusError as exc:
                logging.error("error %s- Code=%d", exc, exc.get_exception_code())
                return False
        for mb in self.mbVal:
            try:
                reg_bit = 0
                if re.match("bit", mb['data_type'], re.M | re.I) or re.match("bool", mb['data_type'], re.M | re.I):
                    reg_bit = mb['register_bit']
            except Exception:
                pass
                # print("set bit/bool register_bit=0, %s" % e)
            write_value = mb['write_value'] if 'write_value' in mb else None
            print("init var: %s" % mb)
            mb['len'] = self.__get_block_length(mb['data_type'], mb["len"] if "len" in mb else 1)
            mbPoll = MbValHandle(self.master, self.mbProto['slave'], mb['name'], mb['addr'], mb['len'],
                                 mb['data_type'], self.mbProto['byte_order'], mb['operation'], reg_bit, write_value)
            self.instance_list.append(mbPoll)
        return True

    def __get_block_length(self, data_type, size=1):
        if re.match("bool", data_type, re.M | re.I) \
                or re.match("bit", data_type, re.M | re.I) \
                or re.match("byte", data_type, re.M | re.I) \
                or re.match("sint", data_type, re.M | re.I) \
                or re.match("word", data_type, re.M | re.I) \
                or re.match("int", data_type, re.M | re.I) \
                or re.match("ushort", data_type, re.M | re.I) \
                or re.match("short", data_type, re.M | re.I):
            return 1
        elif re.match("dword", data_type, re.M | re.I) \
                or re.match("dint", data_type, re.M | re.I) \
                or re.match("real", data_type, re.M | re.I) \
                or re.match("float", data_type, re.M | re.I) \
                or re.match("long", data_type, re.M | re.I) \
                or re.match("ulong", data_type, re.M | re.I):
            return 2
        elif re.match("bcd", data_type, re.M | re.I):
            return 2
        elif re.match("string", data_type, re.M | re.I):
            return int((size if (size % 2) == 0 else size + 1) / 2)
        else:
            print("unknown data type")
            return 0

    def run(self):
        """
        init modbus master, and then read/write data for each five seconds
        :return:
        """
        try:
            if self.init():
                if self.mbProto['type'] == 'RTU':
                    self.master.open()
            while True:
                for mbEvt in self.instance_list:
                    if "rw" in mbEvt.operation:
                        mbEvt.read_data()
                        time.sleep(5)
                        if mbEvt.value is not None:
                            mbEvt.write_data(mbEvt.value)
                    elif "wo" in mbEvt.operation:
                        if mbEvt.value is not None:
                            mbEvt.write_data(mbEvt.value)
                    else:
                        mbEvt.read_data()

                time.sleep(5)
        except Exception as e:
            print("Found error: %s" % e)


if __name__ == '__main__':
    # modbus slave settings
    # reconnect_interval only for TCP
    mbProto = {'reconnect_interval': 15.0, 'hostname': '10.5.16.234', 'type': 'TCP', 'port': 502,
               'slave': 1, 'byte_order':'abcd'}
    # mbProto = {'type': 'RTU', 'serialPort': "/dev/tty03", 'baudrate':9600, "bytesize": 8, "parity":"N", "stopbits":1,
    #            'slave': 1, 'byte_order': 'abcd'}

    # variable settings
    # if data_type is bit/bool, you should add register_bit key-word except the address
    # is between 1~10000、10001~20000、110001~165535
    # if data_type is string you should add len key-word
    # if write data to plc(operation with 'w'), you should add write_value key-word
    mbVal = [
            {'addr': 100, 'operation': 'rw', 'name': 'power', 'data_type': 'bit', 'write_value': 0},
            {'addr': 30001, 'operation': 'ro', 'name': 'model', 'data_type': "bit", 'register_bit':1},
            {'addr': 30002, 'operation': 'ro', 'name': 'temperature', 'data_type': "int"},
            {'addr': 40001, 'operation': 'rw', 'name': 'speed', 'data_type': "word", 'write_value': 20},
            {'addr': 40003, 'operation': 'rw', 'len': 4, 'name': 'pressure', 'data_type': 'string', 'write_value': 'cvbn'},
        ]

    mbMaster = MBMaster(mbProto, mbVal)
    mbMaster.run()