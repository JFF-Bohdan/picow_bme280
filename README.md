# picow_bme280

Tutorial for integration of BME280 with Pico W.

In this tutorial we would go through a set of examples where we would start from Pico W with BME 280 sensor 
sending information to our host system via MQTT, considering external power support then we improve our 
setup to have dashboards and battery power supply for our Pico W.

## Initialization on a host system

### Virtual environment

Check installed version of Python:

```commandline
python --version
```

Note: on some Linux version you may need to use `python3 --version` instead

This tutorial was tested on `Python 3.9.1`

Install virtual environment via:

```commandline
python -m venv venv
```

And activate it via:

```commandline
venv\Scripts\activate.bat
```

(see [documentation](https://docs.python.org/3/tutorial/venv.html) for more details)

### Additional tools

To install additional tools please run:

```commandline
pip install -r requirements.txt
```

This command will install additional tools that would be used in this tutorial, 
including [rshell](https://github.com/dhylands/rshell) which may be used to transmit 
files to Pico W board. You also may want to install IDE [Thonny](https://thonny.org/) 
to have ability edit files using GUI.

# Pico W firmwares and documentation

Entry point for excellent documentation about Pico W can be found 
[here](https://www.raspberrypi.com/documentation/microcontrollers/). There you will find latest version of 
Micro Python firmware.

Also, sometime you may found yourself in a situation when your PicoW got stuck and chip freezes and unable to show 
up as a disk. In this case you may try to flash a firmware which would erase internal flash.

You can find this nuke flash in this repository [here](/data/flash_nuke.uf2) or download following links on a 
[page](https://learn.adafruit.com/getting-started-with-raspberry-pi-pico-circuitpython/circuitpython) 

## Examples

### Example 1 - simple wireless (Wi-Fi) sensor with external power supply sending data via MQTT

In this example we are going to develop wireless sensor which would be able to transmit data with temperature, 
humidity and pressure to a host station via MQTT. In this example host system setup will be very simple 
and will print received information to the console.

Please follow [Example-1](./docs/example_01.md)
