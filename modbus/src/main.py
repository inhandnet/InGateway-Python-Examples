# -*- coding: utf-8 -*-
'''
App example
Created on 2020/4
@author: InHand
'''
import sys
import getopt
from modbus_example import MBMaster, mbProto, mbVal

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

    mbMaster = MBMaster(mbProto, mbVal)
    mbMaster.run()
    print("App was exit.")


if __name__ == '__main__':
    main()
