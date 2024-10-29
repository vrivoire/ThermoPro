# pyinstaller --onefile ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole

from ThermoProScan import ThermoProScan
from datetime import timedelta
import logging as log
import logging.handlers
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import os.path
import pandas as pd
import sys


class ThermoProGraph:
    MEAN = 24

    log.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] [%(lineno)d] %(message)s",
        handlers=[
            logging.handlers.TimedRotatingFileHandler(ThermoProScan.LOG_PATH, when='midnight', interval=1, backupCount=7, encoding=None, delay=False, utc=False, atTime=None, errors=None),
            logging.StreamHandler()
        ]
    )

    @staticmethod
    def load_csv() -> list[dict]:
        if os.path.isfile(ThermoProScan.OUTPUT_CSV_FILE):
            result = pd.read_csv(ThermoProScan.OUTPUT_CSV_FILE)
            result = result.rename(columns={'temperature_C': 'temp.'})
            result = result.astype({'time': 'datetime64[ns]'})
            result = result.astype({'temp.': 'float'})
            return result.to_dict('records')
        return []

    @staticmethod
    def create_graph(self):
        csv_data = self.load_csv()
        if bool(csv_data):
            sortedDatas = sorted(csv_data, key=lambda d: d["time"])
            df = pd.DataFrame(sortedDatas)
            log.info(f'\n{df}')

            fig, ax1 = plt.subplots()
            ax1.set_ylabel('Temperature °C', color='xkcd:scarlet')
            ax1.plot(df["time"], df["temp."], color='xkcd:scarlet')
            ax1.grid(axis='y', color='xkcd:scarlet', linewidth=0.2)
            ax1.set_yticks(list(range(int(df['temp.'].min(numeric_only=True) - 1), int(df['temp.'].max(numeric_only=True) + 2), 1)))
            plt.axhline(0, linewidth=2, color='black')

            ax1.plot(df["time"], df["temp."].rolling(window=ThermoProGraph.MEAN).mean(), color='xkcd:deep red', alpha=0.3)

            ax2 = ax1.twinx()  # instantiate a second Axes that shares the same x-axis
            ax2.set_ylabel('Humidity %', color='xkcd:royal blue')  # we already handled the x-label with ax1
            ax2.plot(df["time"], df["humidity"], color='xkcd:royal blue')
            ax2.grid(axis='y', color='blue', linewidth=0.2)

            ax2.plot(df["time"], df["humidity"].rolling(window=ThermoProGraph.MEAN).mean(), color='xkcd:deep blue', alpha=0.3)

            # min_humidity = int((df['humidity'].min(numeric_only=True) - 1)/10)*10
            # max_humidity = int(df['humidity'].max(numeric_only=True) - 1)
            # log.info(list(range(min_humidity, max_humidity, 5)))
            # ax2.set_yticks(list(range(min_humidity, max_humidity, 5)))
            ax2.set_yticks(list(range(0, 105, 5)))

            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
            plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
            plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter('%H'))
            plt.gca().xaxis.set_minor_locator(mdates.HourLocator(range(0, 25, 6)))
            ax1.grid(axis='x', color='black', which="major", linewidth=0.2)
            ax1.grid(axis='x', color='black', which="minor", linewidth=0.1)
            plt.xticks(rotation=45, ha='right', fontsize='small')
            plt.gcf().autofmt_xdate()

            plt.title(f"Temperature & Humidity")
            x_min = df['time'][0] - timedelta(hours=1)
            x_max = df["time"][df["time"].size - 1] + timedelta(hours=1)
            y_max = df['humidity'].max(numeric_only=True) + 5
            y_min = df['temp.'].min(numeric_only=True)
            plt.axis((x_min, x_max, y_min, y_max))

            plt.tight_layout()

            fig.canvas.manager.set_window_title('ThermoPro Graph')
            DPI = fig.get_dpi()
            fig.set_size_inches(1280.0 / float(DPI), 720.0 / float(DPI))
            plt.savefig(ThermoProScan.PATH + 'ThermoProScan.png')
        else:
            log.warn('csv_data is empty')


if __name__ == '__main__':
    thermoProGraph: ThermoProGraph = ThermoProGraph()
    thermoProGraph.create_graph(thermoProGraph)
    plt.show()
    sys.exit()
