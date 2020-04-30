# -*- coding: utf-8 -*-
# /*
# OpcUa server example
#
# Created on 2020/04
# @author: InHand
# */

import opcua
import time

server = opcua.Server()
end_point = "opc.tcp://127.0.0.1:53531/OPCUA/SimulationServer"
server.set_endpoint(end_point)
server.start()
try:
    name_space = "http://examples.freeopcua.github.io"
    idx = server.register_namespace(name_space)

    # get Objects node
    objects = server.get_objects_node()
    print("I got objects: ", objects)

    # now adding some object to our addresse space
    myobject = objects.add_object(idx, "NewObject")
    data_type = opcua.VariantType.INT32
    v = myobject.add_variable(idx, "MyVariable", 123, data_type)

    count = 0
    while True:
        count += 1
        v.set_value(count, data_type)
        print("Set variable(%s) value: %s" % (v, count))
        time.sleep(1)
except Exception as e:
    print("Found error %s" % e)

finally:
    server.stop()
