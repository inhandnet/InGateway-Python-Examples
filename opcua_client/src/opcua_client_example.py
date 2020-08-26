# -*- coding: utf-8 -*-

# /*
# OpcUa client example
#
# Created on 2020/04
# @author: InHand
# */
# for detail info, see https://pypi.org/project/opcua/
import opcua
import time

def opcua_client_example():
    end_point = "opc.tcp://10.5.16.234:53530/OPCUA/SimulationServer"
    client = opcua.Client(end_point)

    client.connect()

    while True:
        node_id = "ns=6;s=DataItem_0000"
        var = client.get_node(node_id)

        print("Read value of variable(%s) is: %s" % (var, var.get_value()))
        time.sleep(5)

    client.disconnect()


if __name__ == '__main__':
    opcua_client_example()

