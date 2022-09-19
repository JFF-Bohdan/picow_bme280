import time


class UptimeCounter(object):
    def __init__(self):
        self._uptime = time.ticks_ms()

    def uptime_ms(self) -> int:
        return time.ticks_ms() - self._uptime
