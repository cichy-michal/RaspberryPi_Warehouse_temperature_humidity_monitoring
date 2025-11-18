#!/usr/bin/env python3

import logging
import time

from bme280 import BME280
from smbus2 import SMBus

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.info("""
weather.py - Print readings from the BME280 weather sensor.

Press Ctrl+C to exit!
""")

bucket = "magazyn"
org = "pwr"
token = "twoj_token"
url = "http://localhost:8086"

client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)

try:
    while True:
        temperature = bme280.get_temperature()
        pressure = bme280.get_pressure()
        humidity = bme280.get_humidity()

        logging.info(f"""
    Temperature: {temperature:05.2f} °C
    Pressure: {pressure:05.2f} hPa
    Relative humidity: {humidity:05.2f} %
    """)

        point = influxdb_client.Point("weather").field("temperature", temperature).field("pressure", pressure).field("humidity", humidity)
        write_api.write(bucket=bucket, org=org, record=point)
    
        time.sleep(1)
finally:
    client.close()