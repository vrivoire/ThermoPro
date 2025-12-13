# https://www.geeksforgeeks.org/python/how-to-open-a-website-in-a-tkinter-window/
import io
import math
import tkinter
import traceback
from typing import Any

import matplotlib.dates as m_dates
import pandas as pd
import webview
from jinja2 import Template
from pandas import DataFrame

import thermopro
from thermopro import log
from thermopro.constants import DAYS_PER_MONTH

COMFORT_MATRIX = '''%,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43
100,blue,green,green,green,green,yellow,yellow,yellow,yellow,orange,orange,orange,red,red,,,,,,,,,
95,blue,green,green,green,green,green,yellow,yellow,yellow,orange,orange,orange,orange,red,red,,,,,,,,
90,blue,green,green,green,green,green,yellow,yellow,yellow,yellow,orange,orange,orange,red,red,red,,,,,,,
85,blue,blue,green,green,green,green,green,yellow,yellow,yellow,orange,orange,orange,orange,red,red,,,,,,,
80,blue,blue,green,green,green,green,green,yellow,yellow,yellow,yellow,orange,orange,orange,orange,red,red,,,,,,
75,blue,blue,blue,green,green,green,green,green,yellow,yellow,yellow,orange,orange,orange,orange,red,red,,,,,,
70,blue,blue,blue,green,green,green,green,green,yellow,yellow,yellow,yellow,orange,orange,orange,orange,red,red,,,,,
65,blue,blue,blue,blue,green,green,green,green,green,yellow,yellow,yellow,yellow,orange,orange,orange,orange,red,,,,,
60,blue,blue,blue,blue,green,green,green,green,green,green,yellow,yellow,yellow,orange,orange,orange,orange,orange,red,,,,
55,blue,blue,blue,blue,blue,green,green,green,green,green,yellow,yellow,yellow,yellow,orange,orange,orange,orange,red,red,,,
50,blue,blue,blue,blue,blue,green,green,green,green,green,green,yellow,yellow,yellow,yellow,orange,orange,orange,orange,red,red,,
45,blue,blue,blue,blue,blue,blue,green,green,green,green,green,green,yellow,yellow,yellow,yellow,orange,orange,orange,orange,red,red,
40,,,blue,blue,blue,blue,blue,green,green,green,green,green,yellow,yellow,yellow,yellow,yellow,orange,orange,orange,orange,orange,red
35,,,,blue,blue,blue,blue,green,green,green,green,green,green,yellow,yellow,yellow,yellow,yellow,orange,orange,orange,orange,orange
30,,,,,,,blue,blue,green,green,green,green,green,green,yellow,yellow,yellow,yellow,yellow,orange,orange,orange,orange
25,,,,,,,,,,green,green,green,green,green,green,yellow,yellow,yellow,yellow,yellow,orange,orange,orange
20,,,,,,,,,,,,,,,,,,yellow,yellow,yellow,yellow,yellow,orange'''

COMFORT_MATRIX_LABELS: dict[str, str] = {
    'blue': 'No discomfort',
    'green': 'Some discomfort',
    'yellow': 'Great discomfort; avoid exertion',
    'orange': 'Dangerous',
    'red': 'Heat stroke imminent'
}

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta content="text/html; charset=utf-8" http-equiv="Content-Type">
    <title>ThermoPro</title>
    <style>
        #weather-widget {
			border: 1px solid;
			color: #80808061;
			width: 300px;
			background: #80808036;
			padding: 3px;
			position: relative;
			font-family: Space Grotesk,Arial,sans-serif;
			-webkit-font-smoothing: antialiased;
			-moz-osx-font-smoothing: grayscale;
			color: #48484a;
			width: 19em;
			margin: 0;
			padding: 0;
		}
        .current-temp {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: row;
            white-space: nowrap;
            box-sizing: border-box;
            font-size: 36px;
            font-weight: 100;
            margin-right: 8pt;
        }
        .weather-items {
            font-size: 15px;
            list-style: none;
            line-height: 20px;
            border-left: 1px solid #eb6e4b;
            max-width: 60em;
            padding-left: 16pt;
            padding-right: 16pt;
            margin-top: 4pt;
            margin-bottom: 0;
            box-sizing: border-box;
            margin-right: 1pt;
            align-items: center;
        }
    </style>
</head>
<body>
<div id="weather-widget">
    <span style="color: #eb6e4b;display: block;text-align: center;font-weight: bold;margin-top: 1em;">{{time.strftime('%d %B %Y %H:%M')}}</span>
    <span class="current-temp"><img loading="eager" src="https://openweathermap.org/img/wn/{{open_icon}}@2x.png">&nbsp;{{"%.1f" | format(ext_temp)}}&deg;C</span>
    <div style="font-weight: 700;padding-left: 10px;">
        <span title="Humidex: {{ext_humidex}}&deg;C.">Feels like {{open_feels_like}}&deg;C</span><br>
        {{open_description}}
    </div>

    <ul class="weather-items">
        {% if open_rain > 0 or open_snow > 0 %}
        <li>
            {% if open_rain > 0 %}
            &#9748; {{open_rain}}mm
            {% endif %}
            &nbsp;
            {% if open_snow > 0 %}
            &#9924; {{open_snow}}mm
            {% endif %}
        </li>
        {% endif %}
        <li>&#127811;{{"%.2f" | format(open_wind_speed)}}m/s ({{open_wind_gust}}m/s) <span title="{{open_wind_deg}}&deg;">{{open_wind_deg_txt}}</span>
            &#128167;{{ext_humidity}}%
        </li>
        <li>{{open_pressure}}hPa &nbsp; &#128065; {{"%.2f" | format(open_visibility/1000)}}Km &nbsp; UV: {{"%.2f" | format(open_uvi)}}
        </li>
    </ul>
    <hr>
    <ul class="weather-items">
        <li>
            <span title="Mean: {{mean_kwh_hydro_quebec}} KWh"><img loading="eager" src="https://upload.wikimedia.org/wikipedia/commons/a/ae/Hydro-Qu%C3%A9bec_logo.svg" width="50"> {{"%.2f" | format(kwh_hydro_quebec)}} KWh</span>&nbsp;
            <img loading="eager" src="https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/7b/9b/75/7b9b754b-cc8c-5a36-3468-9ea5838af4ab/AppIcon-0-0-1x_U007epad-0-1-0-85-220.jpeg/200x200ia-75.webp" width="20"> {{"%.2f" | format(kwh_neviweb)}} KWh
        </li>
        <li><span style="color:{{comfort_color}}" title="{{comfort_text}}">&#127777; &#127968; {{int_temp}}&deg;C &nbsp; &#128167; {{int_humidity}}%</span>
        </li>
        <li>&#128186; {{int_temp_bureau}}&deg;C &nbsp; &#128719; {{int_temp_chambre}}&deg;C</li>
        <li>&#128704; {{int_temp_salle_de_bain}}&deg;C &nbsp; &#128715; {{int_temp_salon}}&deg;C</li>
    </ul>
</div>
</body>
</html>
'''

WIDTH: int = 340
HEIGHT: int = 400


class Tooltip:

    def __init__(self):
        log.info('Starting Tooltip')

    def get_matrix(self, temp: int, humidity: int):
        print(f'temp: {temp}, humidity: {humidity}')
        try:
            humidity = 5 * round(humidity / 5) if not math.isnan(humidity) else 0
            if temp < 21 or temp > 43 and humidity < 20:
                return ('black', '')
            matrix = pd.read_csv(io.StringIO(COMFORT_MATRIX))
            matrix.set_index('%')
            h = int((100 - humidity) / 5)
            # log.info(f'temp: {temp}, humidity: {humidity}, x: {temp - 20}, y: {h}, {matrix.iat[h, temp - 20] if matrix.iat[h, temp - 20] != None else 'black'}, {COMFORT_MATRIX_LABELS.get(matrix.iat[h, temp - 20]) if COMFORT_MATRIX_LABELS.get(matrix.iat[h, temp - 20]) else ''}')
            return (
                matrix.iat[h, temp - 20] if matrix.iat[h, temp - 20] != None else 'black',
                COMFORT_MATRIX_LABELS.get(matrix.iat[h, temp - 20]) if COMFORT_MATRIX_LABELS.get(matrix.iat[h, temp - 20]) else ''
            )
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
        return ('black', '')

    def degToCompass(self, num) -> str:
        val = int((num / 22.5) + .5)
        arr1 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        s = arr1[(val % 16)]
        val = int((num / 45) + .5)
        arr = ["129105", "129109", "129106", "129110", "129107", "129111", "129104", "129108"]
        return f"&#{arr[(val % 8)]}; {s}"

    # https://www.google.com/search?q=python+matplotlib.pyplot+plot+behind+webview+window&sca_esv=43ccaf06e6065102&sxsrf=AE3TifOwqr8gxh3r1DkDhvg6hhFK6rUphg%3A1763825350701&ei=xtYhaZHGKpu-0PEP4c3ZwQ0&ved=0ahUKEwiRweW7iYaRAxUbHzQIHeFmNtgQ4dUDCBE&uact=5&oq=python+matplotlib.pyplot+plot+behind+webview+window&gs_lp=Egxnd3Mtd2l6LXNlcnAiM3B5dGhvbiBtYXRwbG90bGliLnB5cGxvdCBwbG90IGJlaGluZCB3ZWJ2aWV3IHdpbmRvdzIEECEYFUieZVCODFjWY3ABeAGQAQCYAcgBoAHEFqoBBjAuMTguMbgBA8gBAPgBAZgCEqAC3RTCAgoQABiwAxjWBBhHwgIIEAAYgAQYogTCAgUQABjvBcICChAhGKABGMMEGArCAggQIRigARjDBJgDAIgGAZAGCJIHBjEuMTYuMaAH_DGyBwYwLjE2LjG4B9kUwgcEMTQuNMgHEA&sclient=gws-wiz-serp
    def render(self, df: DataFrame, xdata: float, x: int, y: int, SCREEN_WIDTH: int, SCREEN_HEIGHT: int, mean: int):
        log.info(f'xdata: {xdata}, x: {x}, y: {y}')

        x = x if (SCREEN_WIDTH - WIDTH) > x else SCREEN_WIDTH - WIDTH
        y = x if (SCREEN_HEIGHT - HEIGHT) > y else SCREEN_HEIGHT - HEIGHT
        log.info(f"Screen Resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT} ---> {x}, {y}")

        try:
            data: dict[str, Any] = df.loc[df['time'] >= m_dates.num2date(xdata).strftime('%Y/%m/%d %H:00')].iloc[0].to_dict()

            data['open_wind_deg_txt'] = self.degToCompass(data.get('open_wind_deg')) if data.get('open_wind_deg') else ''
            data['int_temp_salle_de_bain'] = data['int_temp_salle-de-bain']
            comfort = self.get_matrix(int(data.get('int_temp')), data.get('int_humidity'))
            print(comfort)
            data['comfort_color'] = comfort[0]
            data['comfort_text'] = comfort[1]
            data['mean_kwh_hydro_quebec'] = round(df.rolling(window=f'{mean}D', on='time')['kwh_hydro_quebec'].mean().iloc[-1], 3)
            data['int_humidity'] = data['int_humidity'] if not math.isnan(data.get('int_humidity')) else 0
            data['open_rain'] = data['open_rain'] if not data.get('open_rain') is None else 0.0
            data['open_snow'] = data['open_snow'] if not data.get('open_snow') is None else 0.0
            data['open_wind_speed'] = data['open_wind_speed'] if not data.get('open_wind_speed') is None else 0.0
            data['open_wind_gust'] = data['open_wind_gust'] if not data.get('open_wind_gust') is None else 0.0
            data['open_wind_deg'] = data['open_wind_deg'] if not data.get('open_wind_deg') is None else 0

            # print(thermopro.ppretty(data))

            template = Template(HTML)
            rendered = template.render(data)

            webview.create_window('Thernopro', html=rendered, width=WIDTH, height=HEIGHT, on_top=True, frameless=False, x=x, y=y)
            webview.start()
        except IndexError as ie:
            pass  # ignore
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())


if __name__ == '__main__':
    thermopro.set_up(__file__)
    root = tkinter.Tk()
    SCREEN_WIDTH: int = root.winfo_screenwidth()
    SCREEN_HEIGHT: int = root.winfo_screenheight()
    root.destroy()
    tooltip: Tooltip = Tooltip()
    tooltip.render(thermopro.load_json(), 20434.166062978064, 2323, 1327, SCREEN_WIDTH, SCREEN_HEIGHT, DAYS_PER_MONTH)
