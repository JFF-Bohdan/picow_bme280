import gc
import os
import sys
import time

import bme280
import machine
import network
import ntptime
import ubinascii
import ujson
from ucollections import namedtuple
from umqtt.simple import MQTTClient

import consts
import functools
import secrets
from battery_info import PicoWBatteryInfo
from internal_temperature_sensor import InternalTemperatureSensor
from misc import get_machine_unique_id
from retry_exception import retry_exception
from uptime_counter import UptimeCounter

try:
    from typing import Callable, Dict, Tuple
except ImportError:
    pass

Bme280Data = namedtuple("Bme280Data", ("temperature", "pressure", "humidity"))

i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400_000)
bme = bme280.BME280(i2c=i2c)


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


@retry_exception(attempts=2, delay_seconds=5)
def read_bme280_values() -> Bme280Data:
    return Bme280Data(
        temperature=bme.values[0],
        pressure=bme.values[1],
        humidity=bme.values[2]
    )


@retry_exception(attempts=3, delay_seconds=5)
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
        # led.toggle()
        now = time.ticks_ms()
        if time.ticks_diff(now, ticks_start) > MAX_OPERATION_TIME_MSECS:
            raise Exception("Can't connect to Wi-Fi")

        time.sleep(CONNECTION_POLLING_INTERVAL_SECS)

    ip = wlan.ifconfig()[0]
    print(f"Connected on {ip}")
    print(f"Full config: {wlan.ifconfig()}")

    mac_address = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    return ip, mac_address


@retry_exception(attempts=2, delay_seconds=5)
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


def get_python_version() -> str:
    v = sys.version_info
    return f"{v[0]}.{v[1]}.{v[2]}"


def enrich_metadata(
        packet: Dict,
        mac_address: str,
        internal_temp_sensor: InternalTemperatureSensor,
        uptime_counter: UptimeCounter,
        current_voltage: float = None,
        charge_percentage: float = None
):
    """
    Enriches payload with additional metadata
    """

    packet["metadata"] = {
        "wifi_mac_address": mac_address,
        "machine_unique_id": get_machine_unique_id(),
        "measurement_time": get_current_timestamp_iso(),
        "machine_metrics": {
            "uptime": uptime_counter.uptime_ms(),
            "python_version": get_python_version(),
            "cpu_temperature": internal_temp_sensor.current_temperature(),
            "mem_free": gc.mem_free(),
            "frequency": machine.freq(),
            "flash_free_space_bytes": get_fs_free_space_in_bytes(),
            "power": {
                "current_voltage": current_voltage,
                "charge_percentage": charge_percentage
            }
        }
    }


def send_measurements(client: MQTTClient, enricher: Callable) -> None:
    bme280_data = read_bme280_values()

    payload = {
        "payload": {
            "bme280": {
                "temperature": bme280_data.temperature,
                "pressure": bme280_data.pressure,
                "humidity": bme280_data.humidity
            },
        },

    }
    enricher(payload)
    payload = ujson.dumps(payload)

    print(f"Sending measurements via MQTT: {payload}")
    client.publish(secrets.MQTT_TOPIC_PUB, msg=payload)


def deactivate_wifi() -> None:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)


def main():
    try:
        uptime_counter = UptimeCounter()
        print(f"Current timestamp is: {get_current_timestamp_iso()}")

        print("Measuring battery charge level")
        battery_info = PicoWBatteryInfo()
        current_voltage = battery_info.current_voltage
        charge_percentage = battery_info.calculate_percentage(current_voltage)
        print(f"Current battery voltage level: {current_voltage}")
        print(f"Battery charge percentage level: {charge_percentage}")

        print("Connecting to Wi-Fi")
        _, mac_address = connect_to_wifi()

        print("Confuguring current timestamp")
        # setup_current_timestamp()

        mqtt_client = mqtt_connect()

        internal_temp_sensor = InternalTemperatureSensor()
        enricher = functools.partial(
            enrich_metadata,
            mac_address=mac_address,
            internal_temp_sensor=internal_temp_sensor,
            current_voltage=current_voltage,
            charge_percentage=charge_percentage,
            uptime_counter=uptime_counter
        )

        send_measurements(
            mqtt_client,
            enricher=enricher
        )

        mqtt_client.disconnect()
        deactivate_wifi()
        time.sleep(1)

        machine.Pin("WL_GPIO1", machine.Pin.OUT).low()
        machine.Pin(23, machine.Pin.OUT).low()
        machine.deepsleep(consts.SLEEP_INTERVAL_BETWEEN_MEASUREMENTS_SECS * 1000)
        machine.reset()
    except Exception as e:
        print(f"Error in main loop: {e}")
        import sys
        sys.print_exception(e)
        machine.deepsleep(consts.SLEEP_INTERVAL_ON_ERROR_SECS * 1000)
        machine.reset()


if __name__ == "__main__":
    main()
