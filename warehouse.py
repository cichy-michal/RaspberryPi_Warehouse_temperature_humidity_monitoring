#!/usr/bin/env python3

import logging
import time
import requests
import json

from bme280 import BME280
from smbus2 import SMBus

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

bucket = 'magazyn'
org = 'pwr'
token = 'api'
url = 'http://localhost:8086'

client = influxdb_client.InfluxDBClient(url = url, token = token, org = org)
write_api = client.write_api(write_options=SYNCHRONOUS)

THINGSPEAK_ALERTS_API_KEY = 'api'
ALERT_URL = 'https://api.thingspeak.com/alerts/send'

TEMP_WARNING = 25.0
TEMP_ALARM   = 27.0
HUM_WARNING  = 60.0
HUM_ALARM    = 70.0
TEMP_MIN_PHYSICAL = -40.0
TEMP_MAX_PHYSICAL = 85.0
HUM_MIN_PHYSICAL  = 0.0
HUM_MAX_PHYSICAL  = 100.0

def determine_state(temperature: float, humidity: float) -> str:

    if (
        temperature is None
        or humidity is None
        or not (TEMP_MIN_PHYSICAL <= temperature <= TEMP_MAX_PHYSICAL)
        or not (HUM_MIN_PHYSICAL <= humidity <= HUM_MAX_PHYSICAL)
    ):
        return "failure"

    if temperature >= TEMP_ALARM or humidity >= HUM_ALARM:
        return "alarm"

    if temperature >= TEMP_WARNING or humidity >= HUM_WARNING:
        return "warning"

    return "normal"
    
def send_thingspeak_alert(subject, body):
    headers = {
        'Thingspeak-Alerts-API-Key': THINGSPEAK_ALERTS_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        "subject": subject,
        "body": body
    }
    response = requests.post(ALERT_URL, headers=headers, data=json.dumps(payload))
    return response.status_code, response.text

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S")

logging.info("""weather.py - Print readings from the BME280 weather sensor.

Press Ctrl+C to exit!

""")

bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)

try:
    while True:
        try:
            temperature = bme280.get_temperature()
            humidity = bme280.get_humidity()
            logging.info(f"""Temperature: {temperature:05.2f} °C
            Relative humidity: {humidity:05.2f} %
            """)

            point = influxdb_client.Point('weather').field('temperature', temperature).field('humidity', humidity)

            write_api.write(bucket = bucket, org = org, record = point)
            
            if temperature > TEMP_WARNING and temperature < TEMP_ALARM:
                send_thingspeak_alert("ALERT: Temperatura blisko progu alarmowego", f"Temperatura: {temperature:.2f} °C")
            
            if temperature > TEMP_ALARM:
                send_thingspeak_alert("ALERT: Temperatura przekroczyla prog alarmowy", f"Temperatura: {temperature:.2f} °C")
                
            if humidity > HUM_WARNING and humidity < HUM_ALARM:
                send_thingspeak_alert("ALERT: Wilgotnosc powietrza blisko progu alarmowego", f"Wilgotnosc powietrza: {humidity:.2f} %")
            
            if humidity > HUM_ALARM:
                send_thingspeak_alert("ALERT: Wilgotnosc powietrza przekroczyla prog alarmowy", f"Wilgotnosc powietrza: {humidity:.2f} %")

        except Exception as e:
                logging.error(f"Błąd odczytu/zapisu: {e}")
                failure_point = (
                    influxdb_client.Point("weather")
                    .tag("state", "failure")
                    .field("temperature", 0.0)
                    .field("pressure", 0.0)
                    .field("humidity", 0.0)
                )
                try:
                    write_api.write(bucket=BUCKET, org=ORG, record=failure_point)
                except Exception as e2:
                    logging.error(f"Nie udało się zapisać stanu awarii: {e2}")

        time.sleep(1)
finally:
    client.close()