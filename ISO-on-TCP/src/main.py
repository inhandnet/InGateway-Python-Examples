# -*- coding: utf-8 -*-
'''
App example
Created on 2020/4
@author: InHand
'''
import sys
import getopt
from ISO_on_TCP_example import Adapter

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

    # ISO-on-TCP settings
    scanner = {'name': 'iso_on_tcp_device', 'ip': '10.5.16.73', 'port': 102, 'rack': 0, 'slot': 0}

    # variable settings
    vars = [
        {'name': 'power', 'register_type': 'Q', 'addr': 0, 'data_type': 'bool', 'operation': 'ro',
         'register_bit': 1},
        {'name': 'water', 'register_type': 'DB', 'dbnumber': 6, 'addr': 14, 'data_type': 'float',
         'operation': 'ro'},

        {'name': 'tem', 'register_type': 'Q', 'addr': 6, 'data_type': 'dword', 'operation': 'ro'},
        {'name': 'pres', 'register_type': 'DB', 'dbnumber': 6, 'addr': 274, 'data_type': 'dword',
         'operation': 'ro'},

        {'name': 'energ', 'register_type': 'M', 'addr': 6, 'data_type': 'dword', 'operation': 'rw',
         'write_value': 220},
        {'name': 'switch', 'register_type': 'DB', 'dbnumber': 6, 'addr': 18, 'data_type': 'string',
         'operation': 'ro', 'write_value': "test", 'len': 4},

    ]
    ad = Adapter(scanner, vars)
    ad.run()
    print("App was exit.")


if __name__ == '__main__':
    main()
