import json
import signal
import time

import paho.mqtt.client as mqtt
from loguru import logger

from secrets import CLIENT_NAME, MQTT_BROKER, TOPIC, USER_NAME, PASSWORD


def ctrl_c_handler(signum, frame):
    print("Exiting...")
    client.loop_stop()
    logger.info("Application finished")
    exit()


def on_message(client, userdata, message):
    payload = str(message.payload.decode("utf-8"))

    try:
        payload = json.loads(payload)
    except:
        return

    payload = json.dumps(payload, sort_keys=True, indent=4)
    logger.info(f"Received message (userdata={userdata}): {payload}")


def main():
    global client

    logger.info("Application started")

    print(f"Connecting to '{MQTT_BROKER}' as client '{CLIENT_NAME}' (user '{USER_NAME}') to listen topic '{TOPIC}'")
    client = mqtt.Client(CLIENT_NAME)
    client.username_pw_set(USER_NAME, PASSWORD)
    client.connect(MQTT_BROKER)

    client.loop_start()

    client.subscribe(TOPIC)
    client.on_message = on_message

    while True:
        time.sleep(0.2)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, ctrl_c_handler)
    main()
