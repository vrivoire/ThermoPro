# https://www.geeksforgeeks.org/python/how-to-open-a-website-in-a-tkinter-window/
import importlib.resources
import io
import json
from typing import Any

import pandas as pd
import webview
from jinja2 import Template

import thermopro
from thermopro import log
from thermopro.constants import DAYS

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


class Tooltip:

    def __init__(self):
        log.info('Starting Tooltip')

    def load(self) -> dict[str, Any]:
        df = thermopro.load_json()
        data: dict[str, Any] = df.iloc[-1].to_dict()

        last_kwh_hydro_quebec: float = 0.0
        for index, row in df[::-1].iterrows():
            if row['kwh_hydro_quebec'] > 0.0:
                last_kwh_hydro_quebec = row['kwh_hydro_quebec']
                break
        data['last_kwh_hydro_quebec'] = last_kwh_hydro_quebec
        data['mean_kwh_hydro_quebec'] = round(df.rolling(window=f'{DAYS}D', on='time')['kwh_hydro_quebec'].mean().iloc[-1], 3)

        return data

    def get_matrix(self, temp: int, humidity: int):
        temp = 23
        humidity = 5 * round(humidity / 5)
        log.info(f'{temp}, {humidity}')

        if temp < 21 or temp > 43 and humidity < 20:
            return ('black', '')

        matrix = pd.read_csv(io.StringIO(COMFORT_MATRIX))
        matrix.set_index('%')
        # thermopro.show_df(matrix)
        h = int((100 - humidity) / 5)
        log.info(f'temp: {temp}, humidity: {humidity}, x: {temp - 20}, y: {h}, {matrix.iat[h, temp - 20] if matrix.iat[h, temp - 20] != None else 'black'}, {COMFORT_MATRIX_LABELS.get(matrix.iat[h, temp - 20]) if COMFORT_MATRIX_LABELS.get(matrix.iat[h, temp - 20]) else ''}')
        return (
            matrix.iat[h, temp - 20] if matrix.iat[h, temp - 20] != None else 'black',
            COMFORT_MATRIX_LABELS.get(matrix.iat[h, temp - 20]) if COMFORT_MATRIX_LABELS.get(matrix.iat[h, temp - 20]) else ''
        )

    def degToCompass(self, num) -> str:
        val = int((num / 22.5) + .5)
        arr1 = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        s = arr1[(val % 16)]
        val = int((num / 45) + .5)
        arr = ["129105", "129109", "129106", "129110", "129107", "129111", "129104", "129108"]
        return f"&#{arr[(val % 8)]}; {s}"

    def render(self, data: dict[str, Any]):
        package_resources = importlib.resources.files("thermopro")
        resource_path = package_resources.joinpath("", "Tooltip.html")
        html_str = resource_path.read_text()

        template = Template(html_str)
        data['open_wind_deg_txt'] = self.degToCompass(data.get('open_wind_deg'))
        data['int_temp_salle_de_bain'] = data['int_temp_salle-de-bain']
        comfort = self.get_matrix(int(data['int_temp']), data['int_humidity'])
        data['comfort_color'] = comfort[0]
        data['comfort_text'] = comfort[1]

        log.info(json.dumps(data, indent=4, sort_keys=True, default=str))

        rendered = template.render(data)
        print(rendered)

        # tk = Tk()
        # tk.geometry("200x200")
        webview.create_window('Thernopro', html=rendered, width=340, height=380, )
        webview.start()


if __name__ == '__main__':
    thermopro.set_up(__file__)
    tooltip: Tooltip = Tooltip()

    data: dict[str, Any] = tooltip.load()
    tooltip.render(data)
