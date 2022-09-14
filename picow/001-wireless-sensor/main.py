import functools
import gc
import machine
import network
import os
import time
import ntptime
import ubinascii
import ujson
from retry_exception import retry_exception
from ucollections import namedtuple

import bme280

from umqtt.simple2 import MQTTClient

import secrets
from internal_temperature_sensor import InternalTemperatureSensor
from misc import get_machine_unique_id
import consts

try:
    from typing import Callable, Dict, Tuple
except ImportError:
    pass


Bme280Data = namedtuple("Bme280Data", ("temperature", "pressure", "humidity"))

i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400_000)
bme = bme280.BME280(i2c=i2c)
led = machine.Pin("LED", machine.Pin.OUT)


def blink_hello_sequence() -> None:
    sequence = (0, 1, 0, 1, 0, 1, 0, 1, 0)

    for value in sequence:
        led.value(value)
        time.sleep(0.100)


def set_led_state(desired_state) -> None:
    led.value(desired_state)


@retry_exception(attempts=3, delay_seconds=5)
def setup_current_timestamp() -> None:
    try:
        ntptime.settime()
    except Exception as e:
        print(f"Error configuring current timestamp: {e}")
        raise


def get_current_timestamp_iso() -> str:
    localtime = time.localtime()
    return f"{localtime[0]}-{localtime[1]:02}-{localtime[2]:02} {localtime[3]:02}:{localtime[4]:02}:{localtime[5]:02}"


def read_bme280_values() -> Bme280Data:
    return Bme280Data(
        temperature=bme.values[0],
        pressure=bme.values[1],
        humidity=bme.values[2]
    )


def connect_to_wifi() -> Tuple[str, str]:
    """
    Connects to Wi-Fi and returns IP and adapter MAC address
    """

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    print(f"Trying connect to WiFi (SSID = {secrets.WIFI_SSID})")
    wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
    
    MAX_OPERATION_TIME_MSECS = 60 * 1000
    CONNECTION_POLLING_INTERVAL_SECS = 1
    
    ticks_start = time.ticks_ms()
    while not wlan.isconnected():
        print("Waitinig for WiFi connection ... ")
        led.toggle()
        now = time.ticks_ms()
        if time.ticks_diff(now, ticks_start) > MAX_OPERATION_TIME_MSECS:
            raise Exception("Can't connect to Wi-Fi")
        
        time.sleep(CONNECTION_POLLING_INTERVAL_SECS)

    ip = wlan.ifconfig()[0]
    print(f"Connected on {ip}")
    print(f"Full config: {wlan.ifconfig()}")

    mac_address = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    return ip, mac_address


@retry_exception(attempts=5, delay_seconds=5)
def mqtt_connect() -> MQTTClient:
    print(f"Trying connect to MQTT server - {secrets.MQTT_SERVER}")
    client = MQTTClient(
        secrets.MQTT_CLIENT_ID,
        secrets.MQTT_SERVER,
        user=secrets.MQTT_USER,
        password=secrets.MQTT_PASSWORD,
        keepalive=60,
        ssl=False,
        ssl_params={}
    )
    client.connect(clean_session=True)
    print(f'Connected to MQTT Broker {secrets.MQTT_SERVER}...')
    return client


def get_fs_free_space_in_bytes() -> int:
    fs_stat = os.statvfs("/")
    assert fs_stat[0] == fs_stat[1], "Unknown FS stat response, sorry"
    return fs_stat[0] * fs_stat[3]





def enrich_metadata(
        packet: Dict,
        mac_address: str,
        internal_temp_sensor: InternalTemperatureSensor
):
    """
    Enriches payload with additional metadata
    """

    packet["metadata"] = {
        "wifi_mac_address": mac_address,
        "machine_unique_id": get_machine_unique_id(),
        "measurement_time": get_current_timestamp_iso(),
        "machine_metrics": {
            "cpu_temperature": internal_temp_sensor.current_temperature(),
            "mem_free": gc.mem_free(),
            "flash_free_space_bytes": get_fs_free_space_in_bytes()
        }
    }


def send_measurements(
        client: MQTTClient,
        measurements: Bme280Data,
        enricher: Callable
) -> None:
    payload = {
        "payload": {
            "bme280": {
                "temperature": measurements.temperature,
                "pressure": measurements.pressure,
                "humidity": measurements.humidity
            },
        },

    }
    enricher(payload)
    payload = ujson.dumps(payload)

    print(f"Sending measurements via MQTT: {payload}")
    client.publish(secrets.MQTT_TOPIC_PUB, msg=payload)


def send_measurements_in_loop(client: MQTTClient, enricher: Callable) -> None:
    wdt_interval = min(consts.WDT_MAX_INTERVAL_IN_SECONDS, consts.MAX_WDT_INTERVAL_FOR_RP2040)
    wdt = machine. WDT(timeout=wdt_interval)
    
    last_measurement = None
    while True:
        now = time.ticks_ms()
        if (
            (not last_measurement) or
            (time.ticks_diff(now, last_measurement) >= consts.SLEEP_INTERVAL_BETWEEN_MEASUREMENTS_TRANSMISSION_SECONDS)
        ):
            bme280_data = read_bme280_values()
            send_measurements(client=client, measurements=bme280_data, enricher=enricher)
            last_measurement = time.ticks_ms()
            
        time.sleep(min(5000, consts.MAX_WDT_INTERVAL_FOR_RP2040) / 1000);
        wdt.feed()


def main():
    internal_temp_sensor = InternalTemperatureSensor()

    blink_hello_sequence()
    print(f"Current timestamp is: {get_current_timestamp_iso()}")
    
    while True:
        try:
            _, mac_address = connect_to_wifi()
            set_led_state(1)

            print("Trying to setup current timestamp")
            setup_current_timestamp()
            print(f"Current timestamp is: {get_current_timestamp_iso()}")

            client = mqtt_connect()
            enricher = functools.partial(
                enrich_metadata,
                mac_address=mac_address,
                internal_temp_sensor=internal_temp_sensor
            )

            send_measurements_in_loop(
                client,
                enricher=enricher
            )
        except Exception as e:
            print(f"Error in main loop: {e}")
            import sys
            sys.print_exception(e)
            time.sleep(consts.SLEEP_INTERVAL_ON_ERROR_IN_MAIN_LOOP)
            machine.reset()


if __name__ == "__main__":
    main()
