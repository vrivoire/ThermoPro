# pyinstaller --onefile ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole

import ctypes
import logging as log
import os.path
import sys
from datetime import timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from ThermoProScan import ThermoProScan


class ThermoProGraph:
    MEAN = 24

    @staticmethod
    def load_csv() -> list[dict]:
        if os.path.isfile(ThermoProScan.OUTPUT_CSV_FILE):
            result = pd.read_csv(ThermoProScan.OUTPUT_CSV_FILE)
            result = result.astype({'time': 'datetime64[ns]'})
            result = result.astype({'temperature': 'float'})
            return result.to_dict('records')
        return []

    @staticmethod
    def create_graph(self):
        csv_data = self.load_csv()
        if bool(csv_data):
            sortedDatas = sorted(csv_data, key=lambda d: d["time"])
            df = pd.DataFrame(sortedDatas)
            df.set_index('time')
            log.info(f'\n{df}')

            fig, ax1 = plt.subplots()
            ax1.set_ylabel('Temperature °C', color='xkcd:scarlet')
            ax1.plot(df["time"], df["temperature"], color='xkcd:scarlet')
            ax1.grid(axis='y', color='xkcd:scarlet', linewidth=0.2)
            ax1.set_yticks(list(range(int(df['temperature'].min(numeric_only=True) - 1), int(df['temperature'].max(numeric_only=True) + 2), 1)))
            plt.axhline(0, linewidth=2, color='black')
            ax1.plot(df["time"], df["temperature"].rolling(window=ThermoProGraph.MEAN).mean(), color='xkcd:deep red', alpha=0.3)

            ax2 = ax1.twinx()  # instantiate a second Axes that shares the same x-axis
            ax2.set_ylabel('Humidity %', color='xkcd:royal blue')  # we already handled the x-label with ax1
            ax2.plot(df["time"], df["humidity"], color='xkcd:royal blue')
            ax2.grid(axis='y', color='blue', linewidth=0.2)
            ax2.plot(df["time"], df["humidity"].rolling(window=ThermoProGraph.MEAN).mean(), color='xkcd:deep blue', alpha=0.3)
            ax2.set_yticks(list(range(0, 105, 5)))

            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
            ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%H'))
            ax1.xaxis.set_minor_locator(mdates.HourLocator(range(0, 25, 6)))
            ax1.grid(axis='x', color='black', which="major", linewidth=0.2)
            ax1.grid(axis='x', color='black', which="minor", linewidth=0.1)
            plt.xticks(rotation=45, ha='right', fontsize='small')
            plt.gcf().autofmt_xdate()

            plt.title(f"Temperature & Humidity")
            x_min = df['time'][0] - timedelta(hours=1)
            x_max = df["time"][df["time"].size - 1] + timedelta(hours=1)
            y_max = df['humidity'].max(numeric_only=True) + 5
            y_min = df['temperature'].min(numeric_only=True)
            plt.axis((x_min, x_max, y_min, y_max))

            plt.tight_layout()
            fig.subplots_adjust(
                left=0.055,
                bottom=0.105,
                right=0.952,
                top=0.948,
                wspace=0.198,
                hspace=0.202
            )
            fig.canvas.manager.set_window_title('ThermoPro Graph')
            DPI = fig.get_dpi()
            fig.set_size_inches(1280.0 / float(DPI), 720.0 / float(DPI))
            plt.savefig(ThermoProScan.PATH + 'ThermoProScan.png')
            plt.show()
        else:
            log.warning('csv_data is empty')
            ctypes.windll.user32.MessageBoxW(0, "csv_data is empty", 'Error', 16)


if __name__ == '__main__':
    thermoProGraph: ThermoProGraph = ThermoProGraph()
    thermoProGraph.create_graph(thermoProGraph)

    sys.exit()
