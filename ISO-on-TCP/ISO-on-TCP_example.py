# -*- coding: utf-8 -*-
'''
Created on 2020/04
@author: InHand
'''

import time
import snap7
from snap7.snap7exceptions import Snap7Exception
import logging
import re
import struct

AREA_CODE_MAP = {
                    "I": snap7.snap7types.S7AreaPE,
                    "Q": snap7.snap7types.S7AreaPA,
                    "M": snap7.snap7types.S7AreaMK,
                    "DB": snap7.snap7types.S7AreaDB,
                    "C": snap7.snap7types.S7AreaCT,
                    "T": snap7.snap7types.S7AreaTM
                }


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(filename)s %(lineno)d]: %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

class VarHandle(object):
    """
    reading/writing data
    """

    def __init__(self, scanner, var):
        self.scanner = scanner
        self.var_dict = var
        self.addr = self.var_dict['addr']
        self.len = 1
        self.name = self.var_dict["name"]
        self.data_type = self.var_dict["data_type"]
        self.operation = self.var_dict["operation"]
        self.register_bit = 0
        self.value = None
        self.dbnumber = 0
        self.polling_maps = dict()
        self.float_repr = 2
        self.area_code = None
        self.register_type  = self.var_dict['register_type']
        self._update_var()

    def _update_var(self):
        """
        update attribute or var info
        :return:
        """
        try:
            if re.match("bit", self.var_dict['data_type'], re.M | re.I) or re.match("bool", self.var_dict['data_type'], re.M | re.I):
                self.register_bit = self.var_dict['register_bit']
            else:
                self.register_bit = 0
            self.value = self.var_dict['write_value'] if 'write_value' in self.var_dict else None
            self.dbnumber = int(self.var_dict['dbnumber']) if 'dbnumber' in self.var_dict else 0

            self.float_repr = int(self.var_dict['float_repr']) if 'float_repr' in self.var_dict else 2

            self.area_code = AREA_CODE_MAP[self.var_dict['register_type']]

            if 'len' in self.var_dict:
                self.len = int(self.var_dict['len']) if re.match("string", self.var_dict['data_type'], re.M | re.I) else 1
            len = self.get_type_length(self.var_dict['data_type']) * self.len
            self.fmt = self.get_unpack_fmt(self.data_type.upper(), self.len)
            self.len = len
        except Exception as e:
            print("set bit/bool register_bit=0, %s" % e)

    @staticmethod
    def get_unpack_fmt(dtype, number):
        """
        build fmt when unpack data from bytes
        :param dtype: data type
        :param number: length
        :return:
        """
        if "BYTE" in dtype:  # unsigned 8 bit
            return "%s" % "B" * number
        elif "SINT" in dtype:  # signed 8 bit
            return "%s" % "b" * number
        elif "DWORD" in dtype or "ULONG" in dtype:  # unsigned 32 bit
            return "%s" % "I" * number
        elif "WORD" in dtype or "USHORT" in dtype:  # unsigned 16 bit
            return "%s" % "H" * number
        elif "DINT" in dtype or "LONG" in dtype:  # signed 32 bit
            return "%s" % "l" * number
        elif "INT" in dtype or "SHORT" in dtype:  # signed 16 bit
            return "%s" % "h" * number
        elif "FLOAT" in dtype or "REAL" in dtype:  # float 32 bit
            return "%s" % "f" * number
        elif "STRING" in dtype:
            return "%s" % "s" * number
        elif "BCD" in dtype:  # BCD 16 bit
            return "%s" % "bb" * number
        else:
            return "None"

    @staticmethod
    def get_type_length(type):
        if re.match("bool", type, re.M | re.I) \
                or re.match("bit", type, re.M | re.I) \
                or re.match("byte", type, re.M | re.I) \
                or re.match("sint", type, re.M | re.I) \
                or re.match("string", type, re.M | re.I):
            return 1

        elif re.match("word", type, re.M | re.I) \
                or re.match("int", type, re.M | re.I) \
                or re.match("ushort", type, re.M | re.I) \
                or re.match("short", type, re.M | re.I):
            return 2

        elif re.match("dword", type, re.M | re.I) \
                or re.match("dint", type, re.M | re.I) \
                or re.match("real", type, re.M | re.I) \
                or re.match("float", type, re.M | re.I) \
                or re.match("long", type, re.M | re.I) \
                or re.match("ulong", type, re.M | re.I):
            return 4

        elif re.match("bcd", type, re.M | re.I):
            return 2

        else:
            logging.error("unknown data type")
            return 0

    def bytes_to_raw_data(self, var, data):
        """
        transfer bytes data to raw data
        :param var:
        :param data:
        :return:
        """
        if re.match("bool", var.data_type, re.M | re.I):
            data = snap7.util.get_bool(data, 0, var.register_bit)
        elif re.match("bit", var.data_type, re.M | re.I):
            data = 1 if snap7.util.get_bool(data, 0, var.register_bit) else 0
        elif re.match("string", var.data_type, re.M | re.I):
            if re.match("db", var.register_type, re.M | re.I):
                length = int(data[1])
                data = data[2:] if len(data[2:]) < length else data[2: length + 2]
            else:
                valid_index = 65535
                if 0 in data:
                    valid_index = data.index(0)
                data = bytearray(b'') if valid_index == 0 else data[0: valid_index]
            data = data.decode("utf-8")
        else:
            # logging.debug("fmt: %s, data: %s" % (var.fmt, data))
            data = struct.unpack("!" + var.fmt, data)
            logging.debug("data: %s" % (data, ))

            if re.match("bcd", var.data_type, re.M | re.I):
                native_bcd_list = [(data[x], data[x + 1]) for x in range(0, len(data), 2)]
                data = list()
                for native_bcd in native_bcd_list:
                    bcd = "".join([str((native_bcd[0] & 0xf0) >> 4), str(native_bcd[0] & 0xf),
                                   str((native_bcd[1] & 0xf0) >> 4), str(native_bcd[1] & 0xf)])
                    data.append(int(bcd))

            if len(data) == 1:
                data = data[0]

            if isinstance(data, float):
                data = round(data, var.float_repr)
        return data

    def read_data(self):
        """
        read each of modbus registers
        :return:
        """
        try:
            if self.scanner:
                if re.match("db", self.register_type, re.I) and re.match("string", self.data_type,
                                                                           re.I):
                    data = self.scanner.read_area(self.area_code,
                                                  self.dbnumber,
                                                  self.addr,
                                                  self.len + 2)
                else:
                    data = self.scanner.read_area(self.area_code,
                                                  self.dbnumber,
                                                  self.addr,
                                                  self.len)
                # logger.debug("### read data : %s" % data)
                if re.match("string", self.data_type, re.M | re.I):
                    bytes_data = data
                else:
                    bytes_data = data[0:self.len]
                # logger.debug("###  bytes_data : %s, self.len: %s" % (bytes_data, self.len))
                raw_data = self.bytes_to_raw_data(self, bytes_data)
                logger.info("\n ### Got %s -> %s, %s \n" % (self.name, raw_data, type(raw_data)))
        except Snap7Exception as se:
            logger.error("Read error [ISO-on-TCP] : %s" % se)
        except Exception as e:
            logger.error("Read error [ISO-on-TCP] @ %s" % e.__str__())

    def write_data(self, write_value):
        """
        write data to plc
        :param write_value: the value that will write
        :return:
        """
        try:
            data = write_value
            if re.match("bool", self.data_type, re.M | re.I) or re.match("bit", self.data_type,
                                                                        re.M | re.I):
                rdata = self.scanner.read_area(self.area_code,
                                                        self.dbnumber,
                                                        self.addr, self.len)
                if isinstance(data, str):
                    if data in ["0", "1", "True", "False"]:
                        data = eval(data)
                    elif "true" == data.lower():
                        data = True
                    elif "false" == data.lower():
                        data = False
                snap7.util.set_bool(rdata, 0, self.register_bit, data)
                wdata = rdata
            elif re.match("string", self.data_type, re.M | re.I):
                if len(data) > self.len:
                    raise ValueError("String exceeded limit. %s " % self.len)
                if re.match("db", self.register_type, re.M | re.I):
                    length = struct.pack("!B", len(data))
                    header = struct.pack("!B", 254)
                    wdata = header + length + bytearray(data, 'utf-8')
                else:
                    wdata = bytearray(data, 'utf-8')
            elif re.match("bcd", self.data_type, re.M | re.I):
                data = str(data).zfill(4)
                h8bit = ((int(data[0]) & 0xf) << 4) | int(data[1])
                l8bit = ((int(data[2]) & 0xf) << 4) | int(data[3])
                wdata = bytearray(chr(h8bit) + chr(l8bit))
            else:
                if isinstance(data, str):
                    data = eval(data)
                wdata = struct.pack("!" + self.fmt, data)

            self.scanner.write_area(self.area_code, self.dbnumber, self.addr, wdata)
            logger.info("\n ### write data: %s to var: %s OK \n" % (wdata, self.name))
            return True
        except Exception as e:
            logger.error("Write error [ISO-on-TCP] @ %s: %s" % (self.name, e))
            return False


class Adapter(object):
    def __init__(self, scanner, vars):
        """
        build client, read/write data
        :param scanner: tcp settings, dict
        :param vars: each var settings, list
        """
        self.scanner = scanner
        self.instance_list = []
        self.vars = vars
        self.stat = "init"
        self.client = snap7.client.Client()
        self.variables = dict()

    def init(self):
        if len(self.vars) == 0:
            logger.error("init Adapter error, invalid vars")
            return False
        if isinstance(self.scanner, dict):
            try:
                self.client.connect(self.scanner["ip"], self.scanner['rack'], self.scanner['slot'], self.scanner['port'])
            except Exception as exc:
                logger.error("error %s", exc)
                return False
        else:
            raise KeyError("invalid scanner")
        
        for mb in self.vars:
            vh = VarHandle(self.client, mb)
            self.instance_list.append(vh)
        return True

    def run(self):
        """
        init modbus master, and then read/write data for each five seconds
        :return:
        """
        try:
            if self.init():
                while True:
                    for vh in self.instance_list:
                        if "rw" in vh.operation:
                            vh.read_data()
                            time.sleep(5)
                            if vh.value is not None:
                                vh.write_data(vh.value)
                        elif "wo" in vh.operation:
                            if vh.value is not None:
                                vh.write_data(vh.value)
                        else:
                            vh.read_data()
    
                    time.sleep(5)
        except Exception as e:
            logger.error("Found error: %s" % e)


if __name__ == '__main__':
    # ISO-on-TCP settings
    scanner = {'name':'iso_on_tcp_device', 'ip': '10.5.16.73', 'port': 102, 'rack': 0, 'slot': 0}

    # variable settings
    vars = [
        {'name': 'power', 'register_type': 'Q', 'addr': 0, 'data_type': 'bool', 'operation': 'ro', 'register_bit': 1},
        {'name': 'water', 'register_type': 'DB', 'dbnumber': 6, 'addr': 14, 'data_type': 'float', 'operation': 'ro'},

        {'name': 'tem', 'register_type': 'Q', 'addr': 6, 'data_type': 'dword', 'operation': 'ro'},
        {'name': 'pres', 'register_type': 'DB', 'dbnumber': 6, 'addr': 274, 'data_type': 'dword', 'operation': 'ro'},

        {'name': 'energ', 'register_type': 'M', 'addr': 6, 'data_type': 'dword', 'operation': 'rw', 'write_value': 220},
        {'name': 'switch', 'register_type': 'DB', 'dbnumber': 6, 'addr': 18, 'data_type': 'string', 'operation': 'ro', 'write_value': "test", 'len': 4},

    ]

    Adapter = Adapter(scanner, vars)
    Adapter.run()