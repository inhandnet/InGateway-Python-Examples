#! /usr/bin/env python

from cpppo.server.enip.get_attribute import proxy as device
from cpppo.server.enip import poll
import cpppo
import threading
import sys
import random
import time
import json

# Using the Python Device SDK for IoT Hub:
#   https://github.com/Azure/azure-iot-sdk-python
# The example connects to a device-specific MQTT endpoint on your IoT Hub.
from azure.iot.device import IoTHubDeviceClient, Message
from enip_to_azure_iot_cert import CERTIFICATES

# The device connection string to authenticate the device with your IoT hub.
# Using the Azure CLI:
# az iot hub device-identity show-connection-string --hub-name {YourIoTHubName} --device-id MyNodeDevice --output table
CONNECTION_STRING = "{Your IoT hub device connection string}"

# Using the Python cpppo for EtherNet/IP:
#   https://github.com/pjkundert/cpppo

address = (sys.argv[1] if len(sys.argv) > 1 else 'localhost', 44818)
# Parameters valid for device; for *Logix, others, try:
params = ['INHAND:O.Data[0-1]']


def failure(exc):
    failure.string.append(str(exc))


def process(par, val):
    process.values[par] = val


failure.string = []  # [ <exc>, ... ]
process.done = False
process.values = {}  # { <parameter>: <value>, ... }
# Initialize an EtherNet/IP CIP proxy instance
via = device(host=address[0], port=address[1], timeout=1)
poller = threading.Thread(
    target=poll.poll, kwargs={
        'via': 	via,
        'cycle':	1.0,
        'process':	process,
        'failure':	failure,
        'params':	params,
    })
poller.start()

# Define the JSON message to send to IoT Hub.
MSG_TXT = '{{"temperature": {temperature},"humidity": {humidity}}}'


def iothub_client_init():
    # Create an IoT Hub client
    client = IoTHubDeviceClient.create_from_connection_string(
        CONNECTION_STRING, server_verification_cert=CERTIFICATES)
    return client

# define behavior for receiving a message


def message_listener(device_client):
    while True:
        message = device_client.receive_message()  # blocking call
        print("the data in the message received was ")
        print(message.data)
        # eg. {"symbol": "T1", "value": 123, "data_type": "DINT"}
        # Write parameter
        try:
            write_msg = json.loads(message.data)
            if not isinstance(write_msg, dict):
                print(type(write_msg))
                raise json.decoder.JSONDecodeError("Unsupported message.")
            if "symbol" not in write_msg or "value" not in write_msg or "data_type" not in write_msg:
                print("Missing required field 'symbol' or 'value' or 'data_type'.")
                continue
            # Write a data to plc, # format: '<symbol>=(<data type>)<value>'
            param = '%s = (%s)%s' % (
                write_msg["symbol"], write_msg["data_type"].upper(), write_msg["value"])
            with via:  # Establish gateway, detects Exception (closing gateway)
                val, = via.write(
                    via.parameter_substitution(param), checking=True)
                print("%s: %-32s == %s" % (time.ctime(), param, val))
        except json.decoder.JSONDecodeError as exc:
            print(
                'Unsupported message, need format is {"symbol": "xxx", "value": xxx, "data_type": "xxx"}, %s' % exc)
        except Exception as exc:
            print("Exception writing Parameter: %s", exc)
            failure(exc)
        print("custom properties are")
        print(message.custom_properties)
        time.sleep(1)


def iothub_client_telemetry_example_run():
    try:
        client = iothub_client_init()
        print("IoT Hub device sending periodic messages, press Ctrl-C to exit")

        # connect the client.
        client.connect()
        # Run a listener thread in the background
        listen_thread = threading.Thread(
            target=message_listener, args=(client,))
        listen_thread.daemon = True
        listen_thread.start()

        while True:
            # Build the message with telemetry values.
            temperature = None
            while process.values:
                par, val = process.values.popitem()
                print("%s: %16s == %r" % (time.ctime(), par, val))
                temperature = val[0]
                humidity = val[1]
                msg_txt_formatted = MSG_TXT.format(
                    temperature=temperature, humidity=humidity)
                message = Message(msg_txt_formatted)

                # Send the message.
                print("Sending message: {}".format(message))
                client.send_message(message)
                print("Message successfully sent")

            while failure.string:
                exc = failure.string.pop(0)
                print("%s: %s" % (time.ctime(), exc))

            time.sleep(1)

    except KeyboardInterrupt:
        print("IoTHubClient example stopped")
    process.done = True
    poller.join()
    # finally, disconnect
    client.disconnect()


if __name__ == '__main__':
    print("IoT Hub Quickstart #1 - PLC device")
    print("Press Ctrl-C to exit")
    iothub_client_telemetry_example_run()
