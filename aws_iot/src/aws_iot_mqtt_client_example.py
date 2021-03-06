#-*- coding:utf-8 -*-

# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import time
import os
import json


# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

def aws_iot_mqtt_client_example():
    # Init AWSIoTMQTTClient
    myAWSIoTMQTTClient = AWSIoTMQTTClient("myClientID2")
    hostName = "xxxxxxx.iot.us-west-2.amazonaws.com"
    portNumber = 8883
    myAWSIoTMQTTClient.configureEndpoint(hostName, portNumber)

    base_path = os.path.split(os.path.realpath(__file__))[0] + "/"
    CAFilePath =  base_path +"rootca.crt"
    KeyPath = base_path +"15dff6cc5e-private.pem.key"
    CertificatePath = base_path +"15dff6cc5e-certificate.pem.crt"

    myAWSIoTMQTTClient.configureCredentials(CAFilePath, KeyPath, CertificatePath)

    # AWSIoTMQTTClient connection configuration
    myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
    myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
    myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

    # Custom MQTT message callback
    def customCallback(client, userdata, message):
        logger.info("Received a new message: ")
        logger.info(message.payload)
        logger.info("from topic: ")
        logger.info(message.topic)
        logger.info("--------------\n\n")

    # Connect and subscribe to AWS IoT
    myAWSIoTMQTTClient.connect()
    myAWSIoTMQTTClient.subscribe("sdk/test", 1, customCallback)
    time.sleep(2)

    # Publish to the same topic in a loop forever
    loopCount = 0
    while True:
            message = {}
            message['message'] = "hello aws iot"
            message['sequence'] = loopCount
            messageJson = json.dumps(message)
            pub_topic = 'data/published/by/client'
            qos = 1
            myAWSIoTMQTTClient.publish(pub_topic, messageJson, qos)
            logger.info('Published topic %s: %s\n' % (pub_topic, messageJson))
            loopCount += 1
            time.sleep(10)


if __name__ == '__main__':
    aws_iot_mqtt_client_example()
