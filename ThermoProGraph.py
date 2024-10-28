# pyinstaller --onefile ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole
import logging
import os.path
from datetime import timedelta
import logging as log
import logging.handlers
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from ThermoProScan import ThermoProScan


class ThermoProGraph:
    log.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] [%(lineno)d] %(message)s",
        handlers=[
            logging.handlers.TimedRotatingFileHandler(ThermoProScan.LOG_PATH, when='midnight', interval=1, backupCount=7, encoding=None, delay=False, utc=False, atTime=None, errors=None),
            logging.StreamHandler()
        ]
    )

    @staticmethod
    def load_csv(self) -> list[dict]:
        if os.path.isfile(ThermoProScan.OUTPUT_CSV_FILE):
            result = pd.read_csv(ThermoProScan.OUTPUT_CSV_FILE)
            result = result.rename(columns={'temperature_C': 'temp.'})
            result = result.astype({'time': 'datetime64[ns]'})
            result = result.astype({'temp.': 'float'})
            return result.to_dict('records')
        return []

    @staticmethod
    def create_graph(self):
        csv_data = self.load_csv(self)
        if bool(csv_data):
            sortedDatas = sorted(csv_data, key=lambda d: d["time"])
            df = pd.DataFrame(sortedDatas)
            print(df)

            fig, ax1 = plt.subplots()
            ax1.set_ylabel('Temperature °C', color='tab:red')
            ax1.plot(df["time"], df["temp."], color='tab:red')
            # ax1.tick_params(axis='y', labelcolor='tab:red')
            ax1.grid(color='tab:red', linewidth=0.2)
            yticks = []
            count = int(df['temp.'].min(numeric_only=True) - 1)
            while count <= int(df['temp.'].max(numeric_only=True) + 1):
                yticks.append(count)
                count += 1
            plt.yticks(yticks)
            # ax1.minorticks_on()

            ax2 = ax1.twinx()  # instantiate a second Axes that shares the same x-axis
            ax2.set_ylabel('Humidity %', color='tab:blue')  # we already handled the x-label with ax1
            ax2.plot(df["time"], df["humidity"], color='tab:blue')
            # ax2.tick_params(axis='y', labelcolor='tab:blue')
            ax2.grid(color='tab:blue', linewidth=0.2)

            # plt.tick_params(axis='x',color='black')
            # plt.gca().xaxis.grid(color='black')

            # plt.gca().xaxis.set_major_locator(color='black')
            # Rotate and align the tick labels , color='black'

            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
            ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))

            plt.xticks(rotation=45, ha='right', fontsize='small', color='black')
            # plt.xticks(minor=True, rotation=45, ha='right', fontsize='small', color='black')
            plt.gcf().autofmt_xdate()

            ax2.xaxis.set_minor_formatter(mdates.DateFormatter('%H'))
            ax2.xaxis.set_minor_locator(mdates.HourLocator(range(0, 25, 6)))

            # ax2.grid(color='black', linestyle = '--', linewidth = 10)
            # plt.gca().grid(which='minor', axis='both', linestyle='--')
            # ax2.grid(which='minor', color='black')
            # ax2.set_xticks(minor=True)

            plt.title(f"Temperature & Humidity")
            x_min = df['time'][0] - timedelta(hours=1)
            x_max = df["time"][df["time"].size - 1] + timedelta(hours=1)
            y_max = df['humidity'].max(numeric_only=True) + 5
            y_min = df['temp.'].min(numeric_only=True)
            plt.axis((x_min, x_max, y_min, y_max))

            plt.tight_layout()

            # fig = plt.gcf()
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
