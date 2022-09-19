import machine


class PicoWBatteryInfo(object):
    CONVERSION_FACTOR = 3 * 3.3 / 65535

    # Full battery voltage (volts)
    FULL_BATTERY = 4.2

    # Low battery voltage (volts)
    EMPTY_BATTERY = 2.8

    def __init__(
            self,
            vsys_pin: int = 29
    ):
        self.vsys_pin = vsys_pin

        self._vsys_adc = None
        self._spi_cs_control = None  # Controls SPI CS used by Wi-Fi module
        self._initialized = False

    @property
    def current_voltage(self) -> float:
        try:
            if not self._initialized:
                self._init()

            self._disable_wifi()

            return self._vsys_adc.read_u16() * PicoWBatteryInfo.CONVERSION_FACTOR
        finally:
            self._enable_wifi()

    @property
    def charge_percentage(self) -> float:
        percentage = 100 * (
                (self.current_voltage - PicoWBatteryInfo.EMPTY_BATTERY) /
                (PicoWBatteryInfo.FULL_BATTERY - PicoWBatteryInfo.EMPTY_BATTERY)
        )
        if percentage > 100:
            percentage = 100.00

        return percentage

    def calculate_percentage(self, current_voltage: float) -> float:
        percentage = 100 * (
                (current_voltage - PicoWBatteryInfo.EMPTY_BATTERY) /
                (PicoWBatteryInfo.FULL_BATTERY - PicoWBatteryInfo.EMPTY_BATTERY)
        )
        if percentage > 100:
            percentage = 100.00

        return percentage

    def _disable_wifi(self):
        if not self._spi_cs_control:
            return

        self._spi_cs_control.value(1)

    def _enable_wifi(self):
        if not self._spi_cs_control:
            return

        self._spi_cs_control.value(0)

    def _init(self):
        self._vsys_adc = machine.ADC(self.vsys_pin)  # reads the system input voltage

        # machine.Pin.PULL_UP
        self._spi_cs_control = machine.Pin(25, machine.Pin.OUT)
        self._initialized = True
