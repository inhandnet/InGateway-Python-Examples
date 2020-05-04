# -*- coding: utf-8 -*-

# /*
# OpcUa client example
#
# Created on 2020/04
# @author: InHand
# */

import opcua
import time

def opcua_client_example():
    client = opcua.Client(True)

    end_point = "opc.tcp://127.0.0.1:53531/OPCUA/SimulationServer"
    client.connect(end_point)

    objects = client.get_objects_node()
    print("Children of objects(%s) are: %s" %(objects, objects.get_children()))

    while True:
        node_id = "ns=2;i=2002;"
        var = client.get_node(node_id)
        time.sleep(5)

        print("Read value of variable(%s) is: %s" % (var, var.get_value()))

    client.disconnect()


if __name__ == '__main__':
    opcua_client_example()

