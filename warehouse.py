#!/usr/bin/env python3

import logging
import time
import datetime

from bme280 import BME280
from smbus2 import SMBus

from influxdb_client import InfluxDBClient, Point, WritePrecision
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

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)


while True:
    temperature = bme280.get_temperature()
    pressure = bme280.get_pressure()
    humidity = bme280.get_humidity()

    logging.info(f"""
Temperature: {temperature:05.2f} °C
Pressure: {pressure:05.2f} hPa
Relative humidity: {humidity:05.2f} %
""")

    point = (
        Point("weather")
        .field("temperature", temperature)
        .field("pressure", pressure)
        .field("humidity", humidity)
        .time(datetime.datetime.utcnow(), WritePrecision.NS)
    )
    write_api.write(bucket=bucket, org=org, record=point)

    time.sleep(1)