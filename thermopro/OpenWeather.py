import json
import traceback
from datetime import datetime
from queue import Queue
from typing import Any

import requests

import thermopro
from constants import WEATHER_URL, NEVIWEB_EMAIL, NEVIWEB_PASSWORD
from thermopro import log


class OpenWeather:

    def __init__(self):
        log.info('       ----------------------- Start OpenWeather -----------------------')

    # https://home.openweathermap.org/statistics/onecall_30
    def load_open_weather(self, result_queue: Queue):
        log.info("   ----------------------- Start load_open_weather -----------------------")
        try:
            response = requests.get(WEATHER_URL)
            resp = response.json()

            log.info(json.dumps(resp, indent=4, sort_keys=True))

            if "cod" in resp:
                log.error(json.dumps(resp, indent=4, sort_keys=True))
            elif "current" in resp:
                current = resp['current']
                data: dict[str, Any] = {
                    'open_temp': round(current['temp'], 2),
                    'open_feels_like': round(current['feels_like'], 2),
                    'open_humidity': int(current['humidity']),
                    "open_pressure": int(current['pressure']),
                    "open_clouds": round(current['clouds'], 0),
                    "open_visibility": round(current['visibility'], 0),
                    "open_wind_speed": round(current['wind_speed'], 2),
                    "open_wind_gust": round(current['wind_gust'], 2) if current.get("wind_gust") else 0.0,
                    "open_wind_deg": round(current['wind_deg'], 0),

                    "open_rain": round(current['rain']["1h"], 2) if current.get('rain') else 0.0,  # mm/h
                    "open_snow": round(current['snow']["1h"], 2) if current.get('snow') else 0.0,  # mm/h

                    "open_description": f"{current['weather'][0]['main']}, {current['weather'][0]['description']}" if current.get('weather') else '',
                    "open_icon": current['weather'][0]['icon'] if current.get('weather') else '',
                    'open_sunrise': datetime.fromtimestamp(current['sunrise']),
                    'open_sunset': datetime.fromtimestamp(current['sunset']),
                    'open_uvi': round(current['uvi'], 2)  # https://fr.wikipedia.org/wiki/Indice_UV
                }

                result_queue.put(data)
            else:
                log.error(json.dumps(resp, indent=4, sort_keys=True))
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())


if __name__ == "__main__":
    thermopro.set_up(__file__)
    result_queue: Queue = Queue()
    openWeather: OpenWeather = OpenWeather()
    openWeather.load_open_weather(result_queue)

    while not result_queue.empty():
        json_data: dict[str, Any] = result_queue.get()
        print(thermopro.ppretty(json_data))
