# Low Power Measurements

## Baseline

Our first version which was based on `time.sleep()` power consumption looks like:

At 01:28 4.26 Volts (coarse measurement), what is about 100%
At 20:52 (same day) it was about 3.74 Volts, what is about 65%.

So, in 19 hours and 24 minutes we lost about 35% of our 2200 mAh battery power. As a result, for 24 
hours we will need about 43% of our battery which is about 946 mA. So, we can consider that our average 
consumption is about 39.4 mAh.

## Improvements

Let's tune some stuff, we will:

1. Transmit data every 5 minutes (300 seconds) instead of 30 seconds
2. We will do proper MQTT disconnect before going to sleep
3. Turn off our radio (Wi-Fi) before going to sleep
4. Use `machine.deepsleep()` instead of `time.sleep()`

We can assume, that in deep sleep we are going to consume about 2 mA and then during transmission we can consume 
up to 90-150 mA during our data transmission.
