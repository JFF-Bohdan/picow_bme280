# Securing Mosquitto


## Changing Mosquitto service configuration

Let's improve our security posture and will add authentication by username and password.

To do this, we need to edit our `/etc/mosquitto/mosquitto.conf`, then please comment/remove lines that 
we added before and add additional configuration. So, at the end file will look like:


```
# listener 1883
# allow_anonymous true

allow_anonymous false
password_file /etc/mosquitto/pwfile
listener 1883
```

Now we need to add our users and passwords, let's add user `pico_weather` which will be used by Pico W:

```commandline
sudo mosquitto_passwd -c /etc/mosquitto/pwfile pico_weather
```

Please note that `-c` will erase existing `/etc/mosquitto/pwfile` file and will create new one.

And then let's add user `host_weather` which will be used on a host system which would listen for all 
events:

```
sudo mosquitto_passwd /etc/mosquitto/pwfile host_weather
```

Then you need to restart your Mosquitto server by using:

```commandline
sudo systemctl restart mosquitto
```

You can check your user/password by running:

```commandline
mosquitto_sub -h localhost -t "PICOW_DATA" --pretty -F "%J" -u host_weather -P "<censored>"
```

# Changing Pico W `secrets.py`

```python
WIFI_SSID = "<censored>"  # <-- your Wi-Fi SSID goes here
WIFI_PASSWORD = "<censored>"  # <-- your Wi-Fi password goes here 

MQTT_SERVER = "<censored>"  # <-- here goes IP address of your MQTT server
MQTT_CLIENT_ID = 'PicoW'  # <-- keep it as is for this example
MQTT_TOPIC_PUB = 'PICOW_DATA'  # <-- keep it as is for this example
MQTT_USER = "<censored>"  # Your Pico W user goes here
MQTT_PASSWORD = "<censored>"  # Password of your Pico W user goes here
```

# Changing Host system receiver configuration

You also will need to change `secrets.py` of yor host receiver

