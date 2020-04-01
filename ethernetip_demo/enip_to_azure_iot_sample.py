#! /usr/bin/env python

import random
import time

# Using the Python Device SDK for IoT Hub:
#   https://github.com/Azure/azure-iot-sdk-python
# The sample connects to a device-specific MQTT endpoint on your IoT Hub.
from azure.iot.device import IoTHubDeviceClient, Message
from enip_to_azure_iot_cert import CERTIFICATES

# The device connection string to authenticate the device with your IoT hub.
# Using the Azure CLI:
# az iot hub device-identity show-connection-string --hub-name {YourIoTHubName} --device-id MyNodeDevice --output table
CONNECTION_STRING = "{Your IoT hub device connection string}"

# Using the Python cpppo for EtherNet/IP:
#   https://github.com/pjkundert/cpppo
import sys
import threading
import cpppo
from cpppo.server.enip import poll
from cpppo.server.enip.get_attribute import proxy as device

hostname = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
# Parameters valid for device; for *Logix, others, try:
params = ['INHAND:I.Data[0]', 'T1']

def failure(exc):
    failure.string.append(str(exc))
failure.string = []  # [ <exc>, ... ]

def process(par, val):
    process.values[par] = val
process.done = False
process.values = {}  # { <parameter>: <value>, ... }

poller				= threading.Thread(
    target=poll.poll, kwargs={
        'proxy_class':  device,
        'address': 	(hostname, 44818),
        'cycle':	1.0,
        'timeout':	0.5,
        'process':	process,
        'failure':	failure,
        'params':	params,
    })
poller.start()

# Define the JSON message to send to IoT Hub.
MSG_TXT = '{{"temperature": {temperature}}}'

def iothub_client_init():
    # Create an IoT Hub client
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING, server_verification_cert=CERTIFICATES)
    return client

def iothub_client_telemetry_sample_run():

    try:
        client = iothub_client_init()
        print ( "IoT Hub device sending periodic messages, press Ctrl-C to exit" )

        while True:
            # Build the message with telemetry values.
            temperature = None
            while process.values:
                par,val		= process.values.popitem()
                print( "%s: %16s == %r" % ( time.ctime(), par, val ))
                if par == 'INHAND:I.Data[0]':
                    temperature = val[0]            
                    msg_txt_formatted = MSG_TXT.format(temperature=temperature)
                    message = Message(msg_txt_formatted)

                    # Add a custom application property to the message.
                    # An IoT hub can filter on these properties without access to the message body.
                    if temperature > 30:
                        message.custom_properties["temperatureAlert"] = "true"
                    else:
                        message.custom_properties["temperatureAlert"] = "false"

                    # Send the message.
                    print( "Sending message: {}".format(message) )
                    client.send_message(message)
                    print ( "Message successfully sent" )

            while failure.string:
                exc			= failure.string.pop( 0 )
                print( "%s: %s" %( time.ctime(), exc ))

            time.sleep(1)

    except KeyboardInterrupt:
        print ( "IoTHubClient sample stopped" )
    process.done		= True
    poller.join()

if __name__ == '__main__':
    print ( "IoT Hub Quickstart #1 - PLC device" )
    print ( "Press Ctrl-C to exit" )
    iothub_client_telemetry_sample_run()
