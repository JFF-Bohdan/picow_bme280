import machine


class InternalTemperatureSensor(object):
    def __init__(self, pin_number: int = 4):
        self._pin_number = pin_number

    def current_temperature(self) -> float:
        sensor_temp = machine.ADC(self._pin_number)
        conversion_factor = 3.3 / 65535
        reading = sensor_temp.read_u16() * conversion_factor
        temperature = 27 - (reading - 0.706) / 0.001721
        return temperature

