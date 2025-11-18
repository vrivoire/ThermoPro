# https://www.geeksforgeeks.org/python/how-to-open-a-website-in-a-tkinter-window/
import importlib.resources
from typing import Any

import webview
from jinja2 import Template

import thermopro
from thermopro import log
from thermopro.ThermoProScan import ThermoProScan
from thermopro.constants import DAYS


class Tooltip:

    def __init__(self):
        log.info('Starting Tooltip')

    def load(self) -> dict[str, Any]:
        df = ThermoProScan.load_json()
        data: dict[str, Any] = df.iloc[-1].to_dict()
        print(data)

        last_kwh_hydro_quebec: float = 0.0
        for index, row in df[::-1].iterrows():
            if row['kwh_hydro_quebec'] > 0.0:
                last_kwh_hydro_quebec = row['kwh_hydro_quebec']
                break
        data['last_kwh_hydro_quebec'] = last_kwh_hydro_quebec
        data['mean_kwh_hydro_quebec'] = round(df.rolling(window=f'{DAYS}D', on='time')['kwh_hydro_quebec'].mean().iloc[-1], 3)
        return data

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
