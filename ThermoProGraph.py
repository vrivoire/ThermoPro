# pyinstaller --onefile ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole

import os.path
from datetime import timedelta

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from ThermoProScan import ThermoProScan


class ThermoProGraph:

    def load_csv(self):
        if os.path.isfile(ThermoProScan.OUTPUT_CSV_FILE):
            result = pd.read_csv(ThermoProScan.OUTPUT_CSV_FILE)
            result = result.rename(columns={'temperature_C': 'temp.'})
            result = result.astype({'time': 'datetime64[ns]'})
            result = result.astype({'temp.': 'float'})
            return result.to_dict('records')
        return []

    def start(self):
        csv_data = self.load_csv()
        sortedDatas = sorted(csv_data, key=lambda d: d["time"])
        df = pd.DataFrame(sortedDatas)
        print(df)

        fig, ax1 = plt.subplots()
        ax1.set_ylabel('temp.', color='tab:red')
        ax1.plot(df["time"], df["temp."], color='tab:red')
        ax1.tick_params(axis='y', labelcolor='tab:red')
        ax1.grid(which="both", color='tab:red', linewidth=0.2)

        ax2 = ax1.twinx()  # instantiate a second Axes that shares the same x-axis
        ax2.set_ylabel('humidity', color='tab:blue')  # we already handled the x-label with ax1
        ax2.plot(df["time"], df["humidity"], color='tab:blue')
        ax2.tick_params(axis='y', labelcolor='tab:blue')
        ax2.grid(which="both", color='tab:blue', linewidth=0.2)

        plt.title(f"Temperature & Humidity")
        x_min = df['time'][0] - timedelta(hours=1)
        x_max = df["time"][df["time"].size - 1] + timedelta(hours=1)
        y_max = df['humidity'].max(numeric_only=True) + 5
        y_min = df['temp.'].min(numeric_only=True)
        plt.axis((x_min, x_max, y_min, y_max))
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
        plt.gcf().autofmt_xdate()  # Rotate and align the tick labels
        plt.xticks(rotation=45, ha='right', fontsize='small')
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))

        plt.tight_layout()

        fig = plt.gcf()
        fig.canvas.manager.set_window_title('ThermoProScan')
        DPI = fig.get_dpi()
        fig.set_size_inches(1280.0 / float(DPI), 720.0 / float(DPI))
        plt.savefig(ThermoProScan.PATH + 'Temperature_Humidity.png')

        plt.show()


if __name__ == '__main__':
    thermoProGraph: ThermoProGraph = ThermoProGraph()
    thermoProGraph.start()
