# -*- coding: utf-8 -*-
'''
App example
Created on 2020/4
@author: InHand
'''
import sys
import getopt
from modbus_example import MBMaster

def usage(cmd):
    print("usage: ")
    print("\t%s -[h]" % cmd)
    print("\t\t-h|--help\tprint this help info")
    sys.exit(255)

def main(argv=sys.argv):
    short_args = "h:c"
    long_args = [
        "help",
    ]

    arguments = argv[1:]
    try:
        opts, args = getopt.getopt(arguments, short_args, long_args)
    except:
        usage(argv[0])
    for option, value in opts:
        if option in ('-h', '--help'):
            usage(argv[0])

    # modbus slave settings
    # reconnect_interval only for TCP
    mbProto = {'reconnect_interval': 15.0, 'hostname': '10.5.16.234', 'type': 'TCP', 'port': 502,
               'slave': 1, 'byte_order': 'abcd'}
    # mbProto = {'type': 'RTU', 'serialPort': "/dev/tty03", 'baudrate':9600, "bytesize": 8, "parity":"N", "stopbits":1,
    #            'slave': 1, 'byte_order': 'abcd'}

    # variable settings
    # if data_type is bit/bool, you should add register_bit key-word except the address
    # is between 1~10000、10001~20000、110001~165535
    # if data_type is string you should add len key-word
    # if write data to plc(operation with 'w'), you should add write_value key-word
    mbVal = [
        {'addr': 100, 'operation': 'rw', 'name': 'power', 'data_type': 'bit', 'write_value': 0},
        {'addr': 30001, 'operation': 'ro', 'name': 'model', 'data_type': "bit", 'register_bit': 1},
        {'addr': 30002, 'operation': 'ro', 'name': 'temperature', 'data_type': "int"},
        {'addr': 40001, 'operation': 'rw', 'name': 'speed', 'data_type': "word", 'write_value': 20},
        {'addr': 40011, 'operation': 'rw', 'name': 'speed222', 'data_type': "bit", 'register_bit': 10,
         'write_value': 1},
        {'addr': 40003, 'operation': 'rw', 'len': 4, 'name': 'pressure', 'data_type': 'string',
         'write_value': 'cvbn'},
    ]

    mbMaster = MBMaster(mbProto, mbVal)
    mbMaster.run()
    print("App was exit.")


if __name__ == '__main__':
    main()
