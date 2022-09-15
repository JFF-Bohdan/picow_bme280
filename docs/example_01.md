# Example 1 - simple wireless (Wi-Fi) sensor with external power supply sending data via MQTT

## Host system setup

### MQTT installation

We can use any Linux computer to have MQTT installed. In this example we are going to 
install [Eclipse Mosquitto](https://mosquitto.org/) to Raspbian OS running on 
Raspberry Pi. Also, we would talk about Mosquitto used in a Docker. 

#### Installing Mosquitto on Raspbian OS

**Installation**

```commandline
sudo apt install mosquitto mosquitto-clients
```

Then we can validate that it's running by issuing:

```commandline
sudo systemctl status mosquitto
```

You should see something like:

```commandline
pi@raspi:~ $ sudo systemctl status mosquitto
● mosquitto.service - Mosquitto MQTT Broker
     Loaded: loaded (/lib/systemd/system/mosquitto.service; enabled; vendor preset: enabled)
     Active: active (running) since Sat 2000-01-01 00:00:20 GMT; 22 years 8 months ago
...
```

Where the most important part would be `Active: active (running)` which means that our
MQTT server Mosquitto is up and running.

Let's allow anonymous connections to our MQTT server on this stage, later we will do security hardening. To do this,
please open `/etc/mosquitto/mosquitto.conf` and two lines:

```
listener 1883
allow_anonymous true
```
And then restart Mosquitto server by executing:

```commandline
sudo systemctl restart mosquitto 
```

**Testing**

We need to open two consoles: on one console we will subscribe for events and second will be used to subscribe 
for events and print them to console.

To subscribe for events we need to run:

```commandline
mosquitto_sub -h localhost -t "mqtt/pi"
```

And then on second console we need to run:

```commandline
mosquitto_pub -h localhost -t "mqtt/pi" -m "Hello world"
```

If everything works fine we will see `Hello world` on a console which has subscriber running.

As additional step, I can recommend to learn how to use [tmux](https://github.com/tmux/tmux/wiki) to be able to split
console for two tmux-screens for more effective use. This [wiki](https://github.com/tmux/tmux/wiki/Getting-Started) 
can be good starting point to learn about `tmux`.

#### Running Mosquitto in a Docker

We need to prepare configuration with name `mosquitto.conf` file which may look like:

```
listener 1883
allow_anonymous true
```

And then we can 
```commandline
docker run -it --rm --name mosquitto -p 1883:1883 -p 9001:9001 -v s:/eclipse-mosquitto/config:/mosquitto/config eclipse-mosquitto
```

Here we are telling Docker to use our `s:/eclipse-mosquitto/config` file from our host OS as `/mosquitto/config` 
file inside our Docker container.

This configuration would allow Mosquitto to accept anonymous connections.

## Hardware setup

### Materials needed:

1. Pico W ( https://shop.pimoroni.com/products/raspberry-pi-pico-w?variant=40059369619539 )
2. BME280 sensor ( https://shop.pimoroni.com/products/bme280-breakout?variant=29420960677971 )
3. Power supply cable (micro USB cable)
4. Connection wires (Dupont female-female for example)

### Wiring

| BME280 | Pico W              |
|--------|---------------------|
| SDA    | I2C0 SDA - PIN1/GP0 |
| SCL    | I2C0 SCL - PIN2/GP1 |
| GND    | GND - PIN38         |
| VIN    | 3V3 (OUT) - PIN36   |

See pinout:

![PicoW pinout](./images/picow-pinout.svg)

Optionally you can solder reset button. For example called "Captain Resetti" which can be 
found [here](https://shop.pimoroni.com/products/captain-resetti-pico-reset-button). This will give you 
ability to perform hardware restart without plugging out and plugging in USB cable which 
connects your host system to your Pico W. 

### Configuring firmware

To achieve our goal we will to:

1. Install Micro Python on your board. Both instructions and firmware can be found
   [here](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html)
2. Generate configuration file
3. Upload MicroPython application into the Raspberry Pi Pico W

**Installing MicroPython firmware**

Please follow instructions from https://www.raspberrypi.com/documentation/microcontrollers/micropython.html and 
upload the latest firmware for Raspberry Pi Pico W.

**Configuration file**

You will need to create file `secrets.py` in a folder `001-wireless-sensor` which would look like:

```python
WIFI_SSID = "<censored>"  # <-- your Wi-Fi SSID goes here
WIFI_PASSWORD = "<censored>"  # <-- your Wi-Fi password goes here 

MQTT_SERVER = "<censored>"  # <-- here goes IP address of your MQTT server
MQTT_CLIENT_ID = 'PicoW'  # <-- keep it as is for this example
MQTT_TOPIC_PUB = 'PICOW_DATA'  # <-- keep it as is for this example
MQTT_USER = None  # <-- keep it as is for this example
MQTT_PASSWORD = None  # <-- keep it as is for this example
```

**Our application uploading**

As it was mentioned in `README.md` we can use [`rshell`](https://github.com/dhylands/rshell). To upload all Python
files from `001-wireless-sensor` please execute (from repository root) command below:

```commandline
rshell rsync ./picow/001-wireless-sensor/ /pyboard
```

It will upload all files (including `secrets.py` that you created manually) into your Pico W.

After that you can restart 

## Combining all together

### Testing via `mosquitto_sub`

On a host system which runs your Mosquitto server you can run:

```commandline
mosquitto_sub -h localhost -t "PICOW_DATA" --pretty -F "%J"  
```

This will connect subscriber to the topic `"PICOW_DATA"`, please be sure that constant
`MQTT_TOPIC_PUB` in your `secrets.py` on a Pico will have same value.

### Testing using custom Python script

First you need to create a configuration file. You need to create a 
file `secrets.py` in folder `host/001-wireless-sensor` which  should look like:

```python
MQTT_BROKER = "<censored>>"  # <-- here goes IP address of your MQTT server
TOPIC = "PICOW_DATA"
CLIENT_NAME = "HOST_PC_RECEIVER"

USER_NAME = None
PASSWORD = None
```

Then you can run `host/001-wireless-sensor/events_receiver.py` by executing

```commandline
python host\001-wireless-sensor\events_receiver.py
```