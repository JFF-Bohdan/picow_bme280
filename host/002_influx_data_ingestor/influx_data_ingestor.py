import json
import signal
import time
import typing
from datetime import datetime

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from loguru import logger

import secrets

mqtt_client = None


def ctrl_c_handler(signum, frame):
    print("Exiting...")
    mqtt_client.loop_stop()
    logger.info("Application finished")
    exit()


def send_data_to_influx(payload: typing.Dict) -> None:
    MACHINES = {
        "e6:61:41:04:03:24:ab:36": "PicoW-Sensor-1"
    }

    bme_data = payload["payload"]["bme280"]

    temperature = bme_data["temperature"]
    temperature = str(temperature).replace("C", "")
    temperature = float(temperature)

    humidity = bme_data["humidity"]
    humidity = str(humidity).replace("%", "")
    humidity = float(humidity)

    pressure = bme_data["pressure"]
    pressure = str(pressure).replace("hPa", "")
    pressure = float(pressure)

    metadata = payload["metadata"]
    machine_unique_id = metadata["machine_unique_id"]
    machine_metrics = metadata["machine_metrics"]

    machine_power = machine_metrics["power"]

    logger.info(f"Data received from '{machine_unique_id}': temp - {temperature:.02f} humidity - {humidity:.02f}")

    logger.info("Sending data to Influx...")
    with InfluxDBClient(url=secrets.INFLUX_URL, token=secrets.TOKEN, org=secrets.ORG) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)

        point = Point("PicoWData") \
            .tag("host", MACHINES[machine_unique_id]) \
            .field("temperature", temperature) \
            .field("humidity", humidity) \
            .field("pressure", pressure) \
            .field("current_voltage", machine_power["current_voltage"]) \
            .field("charge_percentage", machine_power["charge_percentage"]) \
            .field("cpu_temperature", machine_metrics["cpu_temperature"]) \
            .field("mem_free", machine_metrics["mem_free"]) \
            .time(datetime.utcnow(), WritePrecision.NS)

        write_api.write(secrets.BUCKET, secrets.ORG, point)


def on_message(client, userdata, message):
    payload = str(message.payload.decode("utf-8"))

    try:
        payload = json.loads(payload)
    except:
        return

    send_data_to_influx(payload)

    payload = json.dumps(payload, sort_keys=True, indent=4)
    logger.info(f"Received message (userdata={userdata}): {payload}")


def connect_to_mqtt() -> mqtt.Client:
    logger.info(
        f"Connecting to '{secrets.MQTT_BROKER}' as client '{secrets.CLIENT_NAME}' "
        f"(user '{secrets.USER_NAME}') to listen topic '{secrets.TOPIC}'"
    )
    client = mqtt.Client(secrets.CLIENT_NAME)
    client.username_pw_set(secrets.USER_NAME, secrets.PASSWORD)
    client.connect(secrets.MQTT_BROKER)

    return client


def main():

    global mqtt_client
    logger.info("Application started")
    signal.signal(signal.SIGINT, ctrl_c_handler)

    mqtt_client = connect_to_mqtt()
    mqtt_client.subscribe(secrets.TOPIC)
    mqtt_client.on_message = on_message

    mqtt_client.loop_start()

    while True:
        time.sleep(0.2)


if __name__ == "__main__":
    main()
