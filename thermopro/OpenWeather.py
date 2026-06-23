import json
import traceback
from datetime import datetime
from queue import Queue
from typing import Any

import requests
from pandas import DataFrame

import thermopro
from constants import WEATHER_URL, NEVIWEB_EMAIL, NEVIWEB_PASSWORD
from thermopro import log


class OpenWeather:

    def __init__(self):
        log.info(' Start OpenWeather '.center(100, '*'))

    # https://home.openweathermap.org/statistics/onecall_30
    def load_open_weather(self, result_queue: Queue):
        log.info(' Start load_open_weather '.center(100, '*'))
        resp: dict | None = None
        try:
            response = requests.get(WEATHER_URL)
            resp = response.json()

        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
            resp = {
                "current": {
                    "clouds": None,
                    "dew_point": None,
                    "dt": None,
                    "feels_like": None,
                    "humidity": None,
                    "pressure": None,
                    "sunrise": None,
                    "sunset": None,
                    "temp": None,
                    "uvi": None,
                    "visibility": None,
                    "weather": [
                        {
                            "description": None,
                            "icon": None,
                            "id": None,
                            "main": None
                        }
                    ],
                    "wind_deg": None,
                    "wind_gust": None,
                    "wind_speed": None
                }
            }
            # print(resp)

        try:
            df: DataFrame = thermopro.load_json()
            last_row_series = df.iloc[-1]
            log.info(json.dumps(resp, indent=4, sort_keys=True))

            if "cod" in resp:
                log.error(json.dumps(resp, indent=4, sort_keys=True))
            elif "current" in resp:
                current = resp['current']
                data: dict[str, Any] = {
                    'open_temp': round(current['temp'], 2) if current.get("temp") else last_row_series['open_temp'],
                    'open_feels_like': round(current['feels_like'], 2) if current.get("feels_like") else last_row_series['open_feels_like'],
                    'open_humidity': int(current['humidity']) if current.get("humidity") else last_row_series['open_humidity'],
                    "open_pressure": int(current['pressure']) if current.get("pressure") else last_row_series['open_pressure'],
                    "open_clouds": round(current['clouds'], 0) if current.get("pressure") else last_row_series['open_clouds'],
                    "open_visibility": round(current['visibility'], 0) if current.get("pressure") else last_row_series['open_visibility'],
                    "open_wind_speed": round(current['wind_speed'], 2) if current.get("pressure") else last_row_series['open_wind_speed'],
                    "open_wind_gust": round(current['wind_gust'], 2) if current.get("pressure") else last_row_series['open_wind_gust'],
                    "open_wind_deg": round(current['wind_deg'], 0) if current.get("pressure") else last_row_series['open_wind_deg'],

                    "open_rain": round(current['rain']["1h"], 2) if current.get('rain') else last_row_series['open_rain'],  # mm/h
                    "open_snow": round(current['snow']["1h"], 2) if current.get('snow') else last_row_series['open_snow'],  # mm/h

                    "open_description": f"{current['weather'][0]['main']}, {current['weather'][0]['description']}" if current.get('weather') else last_row_series['open_description'],
                    "open_icon": current['weather'][0]['icon'] if current.get('weather') else last_row_series['open_icon'],
                    'open_sunrise': datetime.fromtimestamp(current['sunrise']) if current.get('sunrise') else last_row_series['open_sunrise'],
                    'open_sunset': datetime.fromtimestamp(current['sunset']) if current.get('sunset') else last_row_series['open_sunset'],
                    'open_uvi': round(current['uvi'], 2) if current.get('uvi') else last_row_series['open_uvi'],  # https://fr.wikipedia.org/wiki/Indice_UV
                }

                result_queue.put(data)
            else:
                log.error(json.dumps(resp, indent=4, sort_keys=True))
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
        log.info(' End load_open_weather '.center(100, '*'))


if __name__ == "__main__":
    thermopro.set_up(__file__)
    result_queue: Queue = Queue()
    openWeather: OpenWeather = OpenWeather()
    openWeather.load_open_weather(result_queue)

    while not result_queue.empty():
        json_data: dict[str, Any] = result_queue.get()
        print(thermopro.ppretty(json_data))
