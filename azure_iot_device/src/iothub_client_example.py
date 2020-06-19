# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

import random
import time
import threading

# Using the Python Device SDK for IoT Hub:
#   https://github.com/Azure/azure-iot-sdk-python
# The example connects to a device-specific MQTT endpoint on your IoT Hub.
from azure.iot.device import IoTHubDeviceClient, Message
from iothub_client_cert import CERTIFICATES

# The device connection string to authenticate the device with your IoT hub.
# Using the Azure CLI:
# az iot hub device-identity show-connection-string --hub-name {YourIoTHubName} --device-id MyNodeDevice --output table
CONNECTION_STRING = "{Your IoT hub device connection string}"


# Define the JSON message to send to IoT Hub.
TEMPERATURE = 20.0
HUMIDITY = 60
MSG_TXT = '{{"temperature": {temperature},"humidity": {humidity}}}'

def iothub_client_init():
    # Create an IoT Hub client
    # client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING, server_verification_cert=CERTIFICATES)
    return client


# define behavior for receiving a message
def message_listener(device_client):
    while True:
        message = device_client.receive_message()  # blocking call
        print("the data in the message received was ")
        print(message.data)
        print("custom properties are")
        print(message.custom_properties)


def iothub_client_example():

    try:
        client = iothub_client_init()
        print ( "IoT Hub device sending periodic messages, press Ctrl-C to exit" )
        # connect the client.
        client.connect()
        # Run a listener thread in the background
        listen_thread = threading.Thread(target=message_listener, args=(client,))
        listen_thread.daemon = True
        listen_thread.start()

        while True:
            # Build the message with simulated telemetry values.
            temperature = TEMPERATURE + (random.random() * 15)
            humidity = HUMIDITY + (random.random() * 20)
            msg_txt_formatted = MSG_TXT.format(temperature=temperature, humidity=humidity)
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
            time.sleep(1)

    except KeyboardInterrupt:
        # finally, disconnect
        client.disconnect()
        print ( "IoTHubClient example stopped" )

if __name__ == '__main__':
    print ( "IoT Hub Quickstart #1 - Simulated device" )
    print ( "Press Ctrl-C to exit" )
    iothub_client_example()