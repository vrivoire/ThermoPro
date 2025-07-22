# start pyinstaller --onedir ThermoProScan.py --icon=ThermoPro.jpg --nowindowed --noconsole

# C:\Users\ADELE\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup

# https://github.com/merbanan/rtl_433

import csv
import ctypes
import json
import math
import os
import os.path
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta
from tkinter import PhotoImage
from typing import Any

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas
import pandas as pd
import schedule
from matplotlib.backend_bases import FigureManagerBase
from matplotlib.dates import date2num, num2date
from matplotlib.widgets import CheckButtons, Slider, Button

import thermopro
import thermopro.Secrets as Secrets
from thermopro import HOME_PATH, log
from thermopro.NeviwebTemperature import NeviwebTemperature


class ThermoProScan:

    def __init__(self):
        schedule.clear()

    PATH = f"{HOME_PATH}GoogleDrive/PoidsPression/"
    OUTPUT_JSON_FILE = f"{PATH}ThermoProScan.json"
    OUTPUT_CSV_FILE = f"{PATH}ThermoProScan.csv"

    RTL_433_VERSION = '25.02'
    RTL_433_EXE = f"{HOME_PATH}Documents/NetBeansProjects/rtl_433-win-x64-{RTL_433_VERSION}/rtl_433_64bit_static.exe"
    SCHEDULE_DELAY = '60'
    ARGS = [RTL_433_EXE, '-T', SCHEDULE_DELAY, '-R', '162', '-F', f'json:{OUTPUT_JSON_FILE}']
    DAYS = 7 * 2

    LOCATION = f'{os.getenv('USERPROFILE')}\\Documents\\NetBeansProjects\\PycharmProjects\\ThermoPro\\'

    @staticmethod
    def load_csv() -> list[dict]:
        log.info('load_csv')
        if os.path.isfile(ThermoProScan.OUTPUT_CSV_FILE):
            result = pd.read_csv(ThermoProScan.OUTPUT_CSV_FILE)
            result = result.astype({'time': 'datetime64[ns]'})
            result = result.astype({'temp_ext': 'float'})

            result = result.astype({'temp_int': 'float'})
            result = result.astype({'open_temp': 'float'})
            result = result.astype({'open_feels_like': 'float'})
            result = result.astype({'open_humidity': 'float'})
            return result.to_dict('records')
        else:
            log.error(f'The path "{ThermoProScan.OUTPUT_CSV_FILE}" does not exit.')
        return []

    @staticmethod
    def load_neviweb() -> dict[str, Any] | None:
        neviweb_temperature: NeviwebTemperature = NeviwebTemperature(None, Secrets.NEVIWEB_EMAIL, Secrets.NEVIWEB_PASSWORD, None, None, None, None, open_weather_api_key=Secrets.OPEN_WEATHER_API_KEY)
        try:
            log.info(f'login={neviweb_temperature.login()}')
            log.info(neviweb_temperature.get_network())
            log.info(neviweb_temperature.get_gateway_data())
            data: list = [float(gateway_data2['roomTemperatureDisplay']) for gateway_data2 in neviweb_temperature.gateway_data]
            temp_int: float = sum(data) / len(data)

            data: dict[str, Any] = {'int_temp': round(temp_int, 1)}

            open_weather: dict[str, Any] | None = neviweb_temperature.get_open_weather()
            if open_weather:
                data.update(open_weather)

            log.info(f'**************** data={data}')
            return data
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
        finally:
            log.info(f'logout={neviweb_temperature.logout()}')
            neviweb_temperature.logout()

    @staticmethod
    def get_humidex(temp_ext: float, humidity: int) -> int | None:
        if temp_ext > 20.0:
            kelvin = temp_ext + 273
            ets = pow(10, ((-2937.4 / kelvin) - 4.9283 * math.log(kelvin) / math.log(10) + 23.5471))
            etd = ets * humidity / 100
            humidex: int = round(temp_ext + ((etd - 10) * 5 / 9))
            if humidex < temp_ext:
                humidex = round(temp_ext)
            return humidex
        else:
            return None

    @staticmethod
    def create_graph(popup: bool) -> None:
        log.info('create_graph')
        csv_data = ThermoProScan.load_csv()
        if bool(csv_data):
            sorted_datas = sorted(csv_data, key=lambda d: d["time"])
            df = pd.DataFrame(sorted_datas)
            df.set_index('time')
            df['humidex'] = df.apply(lambda row: ThermoProScan.get_humidex(row.temp_ext, row.humidity), axis=1)
            pandas.set_option('display.max_columns', None)
            pandas.set_option('display.width', 200)
            log.info(f'\n{df}')

            fig, ax1 = plt.subplots()
            ax2 = ax1.twinx()

            ax1.set_ylabel('Humidity %', color='xkcd:royal blue')  # we already handled the x-label with ax1
            ax1.grid(axis='y', color='blue', linewidth=0.2)
            ax1.set_yticks(list(range(0, 101, 10)))

            humidity, = ax1.plot(df["time"], df["humidity"], color='xkcd:royal blue', label='%')
            open_humidity, = ax1.plot(df["time"], df["open_humidity"], color='xkcd:sky blue', label='Open %')

            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))
            ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%d'))
            ax1.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.SU.weekday, interval=1))
            ax1.grid(axis='x', color='black', which="major", linewidth=0.2)
            ax1.grid(axis='x', color='black', which="minor", linewidth=0.1)
            ax1.tick_params(axis='both', which='minor', labelsize=8)
            plt.xticks(rotation=45, ha='right', fontsize='9')
            plt.gcf().autofmt_xdate()

            humidex, = ax2.plot(df["time"], df["humidex"], color='xkcd:pink', label='Humidex')
            open_feels_like, = ax2.plot(df["time"], df["open_feels_like"], color='xkcd:rose pink', label='OpenHumidex')

            temp_ext, = ax2.plot(df["time"], df["temp_ext"], color='xkcd:scarlet', label='Ext. °C')
            temp_int, = ax2.plot(df["time"], df["temp_int"], color='xkcd:red', label='Int. °C')
            open_temp, = ax2.plot(df["time"], df["open_temp"], color='xkcd:reddish', label='OpenTemp. °C')

            ax2.set_ylabel('Temperature °C', color='xkcd:scarlet')
            ax2.grid(axis='y', linewidth=0.2, color='xkcd:scarlet')
            ax2.set_yticks(list(range(int(df['temp_ext'].min(numeric_only=True) - 0.5),
                                      int(max(df['temp_ext'].max(numeric_only=True),
                                              df['humidex'].max(numeric_only=True) + 0.5,
                                              df['temp_int'].max(numeric_only=True))))))
            ax2.plot(df["time"], df.rolling(window=f'{ThermoProScan.DAYS}D', on='time')['temp_ext'].mean(), color='xkcd:deep red', alpha=0.3, label='°C')
            ax2.plot(df["time"], df.rolling(window=f'{ThermoProScan.DAYS}D', on='time')['temp_int'].mean(), color='xkcd:red', alpha=0.3, label='°C')
            ax1.plot(df["time"], df.rolling(window=f'{ThermoProScan.DAYS}D', on='time')['humidity'].mean(), color='xkcd:deep blue', alpha=0.3, label='%')
            plt.axhline(0, linewidth=1, color='black')

            plt.axis((
                df['time'][0] - timedelta(hours=1),
                df["time"][df["time"].size - 1] + timedelta(hours=1),
                df['temp_ext'].min(numeric_only=True) - 1,
                max(df['temp_ext'].max(numeric_only=True), df['humidex'].max(numeric_only=True), df['temp_int'].max(numeric_only=True)) + 1
            ))

            if df['temp_ext'][len(df['temp_ext']) - 1] > 20:
                m_humidex = f', Humidex: {ThermoProScan.get_humidex(df['temp_ext'][len(df['temp_ext']) - 1], df['humidity'][len(df['humidity']) - 1])}°C'
            else:
                m_humidex = ''

            plt.title(
                f"Temperature & Humidity date: {df['time'][len(df['time']) - 1].strftime('%Y/%m/%d %H:%M')}, Ext.: {df['temp_ext'][len(df['temp_ext']) - 1]}°C, Int: {df['temp_int'][len(df['temp_int']) - 1]}°C, " \
                + f"{df['humidity'][len(df['humidity']) - 1]}%{m_humidex}, " \
                + f"Open: {df['open_temp'][len(df['open_temp']) - 1]}°C, Open: {df['open_humidity'][len(df['open_humidity']) - 1]}%, Open Humidex: {df['open_feels_like'][len(df['open_feels_like']) - 1]}, " \
                + f"rolling x̄: {ThermoProScan.DAYS} days", fontsize=10)
            plt.tight_layout()
            fig.subplots_adjust(
                left=0.055,
                bottom=0.105,
                right=0.952,
                top=0.948,
                wspace=0.198,
                hspace=0.202
            )

            def callback(label):
                ln = lines_by_label[label]
                ln.set_visible(not ln.get_visible())
                ln.figure.canvas.draw_idle()

            lines_by_label = {l.get_label(): l for l in [temp_ext, temp_int, open_temp, humidity, open_humidity, humidex, open_feels_like]}
            line_colors = [l.get_color() for l in lines_by_label.values()]
            check = CheckButtons(
                ax=ax1.inset_axes((0.0, 0.0, 0.15, 0.2)),
                labels=lines_by_label.keys(),
                actives=[l.get_visible() for l in lines_by_label.values()],
                label_props={'color': line_colors},
                frame_props={'edgecolor': line_colors},
                check_props={'facecolor': line_colors},
            )
            check.on_clicked(callback)

            def update(val):
                slider_position.valtext.set_text(num2date(val).date())
                df2 = df.set_index(['time'])
                df2 = df2[num2date(val - ThermoProScan.DAYS).date():num2date(val + ThermoProScan.DAYS).date()]

                window = (
                    val - ThermoProScan.DAYS,
                    val + 0.1,
                    df2['humidity'].min(numeric_only=True) - 1,
                    df2['humidity'].max(numeric_only=True) + 1
                )
                ax1.axis(window)
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
                ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))

                window2 = (
                    val - ThermoProScan.DAYS,
                    val + 0.1,
                    df2['temp_ext'].min(numeric_only=True) - 1,
                    max(df2['temp_ext'].max(numeric_only=True), df2['humidex'].max(numeric_only=True), df2['temp_int'].max(numeric_only=True)) + 1
                )
                ax2.axis(window2)

                ax2.set_yticks(list(range(int(df2['temp_ext'].min(numeric_only=True) - 1.1),
                                          int(max(df2['temp_ext'].max(numeric_only=True),
                                                  df2['humidex'].max(numeric_only=True),
                                                  df2['temp_int'].max(numeric_only=True)
                                                  ) + 1.1), 1)))

                fig.canvas.draw_idle()

            def reset() -> None:
                slider_position.reset()
                ax1.axis((
                    df['time'][0] - timedelta(hours=1),
                    df["time"][df["time"].size - 1] + timedelta(hours=1),
                    0,
                    105
                ))
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))
                ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
                ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%d'))
                ax1.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.SU.weekday, interval=1))

                ax2.axis((
                    df['time'][0] - timedelta(hours=1),
                    df["time"][df["time"].size - 1] + timedelta(hours=1),
                    df['temp_ext'].min(numeric_only=True) - 1,
                    max(df['temp_ext'].max(numeric_only=True), df['humidex'].max(numeric_only=True), df['temp_int'].max(numeric_only=True)) + 1
                ))
                ax2.set_yticks(list(range(int(df['temp_ext'].min(numeric_only=True) - 1),
                                          int(max(df['temp_ext'].max(numeric_only=True),
                                                  df['humidex'].max(numeric_only=True),
                                                  df['temp_int'].max(numeric_only=True)
                                                  ) + 1), 1)))
                fig.canvas.draw_idle()

            slider_position = Slider(
                plt.axes(
                    (0.08, 0.01, 0.73, 0.03),
                    facecolor='White'
                ),
                'Date',
                date2num(df["time"][0]),
                date2num(df['time'][len(df['time']) - 1]),
                valstep=1,
                color='w',
                initcolor='none'
            )
            slider_position.valtext.set_text(df["time"][0].date())
            slider_position.on_changed(update)
            button = Button(fig.add_axes((0.9, 0.01, 0.055, 0.03)), 'Reset', hovercolor='0.975')
            button.on_clicked(reset)

            slider_position.set_val(date2num(df['time'][len(df['time']) - 1]))

            fig.canvas.manager.set_window_title('ThermoPro Graph')
            dpi = fig.get_dpi()
            fig.set_size_inches(1280.0 / float(dpi), 720.0 / float(dpi))
            plt.savefig(ThermoProScan.PATH + 'ThermoProScan.png')

            if popup:
                manager: FigureManagerBase = matplotlib.pyplot.get_current_fig_manager()
                img = PhotoImage(file=f'{ThermoProScan.LOCATION}ThermoPro.png')
                manager.window.tk.call('wm', 'iconphoto', manager.window._w, img)
                plt.show()

        else:
            log.warning('csv_data is empty')
            if popup:
                ctypes.windll.user32.MessageBoxW(0, "csv_data is empty", 'Error', 16)

    @staticmethod
    def clear_json_file() -> None:
        if os.path.isfile(ThermoProScan.OUTPUT_JSON_FILE):
            os.remove(ThermoProScan.OUTPUT_JSON_FILE)

    @staticmethod
    def call_rtl_433() -> None:
        log.info("Start call_rtl_433")
        try:
            ThermoProScan.clear_json_file()
            log.info(f'ARGS={ThermoProScan.ARGS}')
            completed_process = subprocess.run(
                ThermoProScan.ARGS,
                capture_output=True,
                timeout=70,
                encoding="utf-8",
                check=False,
                shell=True
            )

            log.info(f'Return code: {completed_process.returncode}')
            log.info(f'stdout: {completed_process.stdout}')
            log.error(f'stderr: {completed_process.stderr}')
            # completed_process.check_returncode()

        except subprocess.TimeoutExpired as timeoutExpired:
            log.error(f"TimeoutExpired, returned \n{timeoutExpired}")
            log.error(traceback.format_exc())

        except subprocess.CalledProcessError as calledProcessError:
            log.error(f"CalledProcessError, returned {calledProcessError.returncode}\n{calledProcessError}")
            log.error(traceback.format_exc())

        except subprocess.SubprocessError as subprocessError:
            log.error(f"SubprocessError, returned \n{subprocessError}")
            log.error(traceback.format_exc())

        except Exception as exception:
            log.error(exception)
            log.error(traceback.format_exc())

    @staticmethod
    def load_json() -> dict[str, Any]:
        log.info('load_json')

        json_data: dict[str, Any] = {}
        log.info(f'Loading file {ThermoProScan.OUTPUT_JSON_FILE}')

        if os.path.isfile(ThermoProScan.OUTPUT_JSON_FILE) and os.stat(ThermoProScan.OUTPUT_JSON_FILE).st_size > 2:
            with open(ThermoProScan.OUTPUT_JSON_FILE, 'r') as file:
                json_str = file.read()
            json_str = json_str.splitlines()[0]
            json_data = json.loads(json_str)
            json_data['temp_ext'] = json_data['temperature_C']
            del (json_data['temperature_C'])
            json_data['time'] = datetime.strptime(json_data['time'], '%Y-%m-%d %H:%M:%S')
        else:
            log.error(f'File {ThermoProScan.OUTPUT_JSON_FILE} not existing or empty.')

        return json_data

    @staticmethod
    def call_all() -> None:
        log.info('')
        log.info('--------------------------------------------------------------------------------')
        log.info("Start task")
        ThermoProScan.call_rtl_433()
        json_data: dict[str, Any] = ThermoProScan.load_json()
        log.info(f'json_data={json_data}')
        if bool(json_data):
            temp_int_open: dict[str, Any] | None = ThermoProScan.load_neviweb()

            is_new_file = False if (os.path.isfile(ThermoProScan.OUTPUT_CSV_FILE) and os.stat(ThermoProScan.OUTPUT_CSV_FILE).st_size > 0) else True
            with open(ThermoProScan.OUTPUT_CSV_FILE, "a", newline='') as csvfile:
                writer = csv.writer(csvfile)
                if is_new_file:
                    writer.writerow(["time", "temp_ext", "humidity", 'temp_int', 'open_temp', 'open_feels_like', 'open_humidity'])

                if temp_int_open:
                    writer.writerow([json_data["time"], json_data["temp_ext"], json_data["humidity"], temp_int_open.get('int_temp'), temp_int_open.get('open_temp'), temp_int_open.get('open_feels_like'), temp_int_open.get('open_humidity')])
                else:
                    writer.writerow([json_data["time"], json_data["temp_ext"], json_data["humidity"]])
                log.info("CSV file writen")

            if not is_new_file:
                ThermoProScan.save_csv()
        else:
            log.error('json_data empty')

        ThermoProScan.clear_json_file()
        log.info("End task")

    @staticmethod
    def save_csv():
        log.info('save_csv()')
        with open(ThermoProScan.OUTPUT_CSV_FILE, 'r') as r, open(ThermoProScan.OUTPUT_CSV_FILE + '.tmp', 'w') as o:
            for line in r:
                line = line.strip()
                if len(line) > 0:
                    o.write(line.strip() + '\n')
        os.remove(ThermoProScan.OUTPUT_CSV_FILE)
        os.rename(ThermoProScan.OUTPUT_CSV_FILE + '.tmp', ThermoProScan.OUTPUT_CSV_FILE)
        if os.path.isfile(ThermoProScan.OUTPUT_JSON_FILE):
            os.remove(ThermoProScan.OUTPUT_JSON_FILE)
        ThermoProScan.create_graph(False)

    @staticmethod
    def start(self):
        try:
            log.info('ThermoProScan started')
            i = 0
            while not os.path.exists(ThermoProScan.PATH) and i < 5:
                log.warning(f'The path "{ThermoProScan.PATH}" not ready.')
                i += 1
                time.sleep(10)
            if not os.path.exists(ThermoProScan.PATH):
                ctypes.windll.user32.MessageBoxW(0, "Mapping not ready.", "Warning!", 16)
                sys.exit()

            self.call_all()
            schedule.every().hour.at(":00").do(self.call_all)
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt as ki:
            pass
            # log.error(f'{ki}')
            # log.error(traceback.format_exc())

        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    @staticmethod
    def stop():
        try:
            log.info('ThermoProScan stopped')
            schedule.clear()
            sys.exit()
        except SystemExit as ex:
            pass


if __name__ == '__main__':
    thermopro.set_up(__file__)

    log.info('ThermoProScan')
    thermoProScan: ThermoProScan = ThermoProScan()

    # thermoProScan.load_neviweb()
    # sys.exit()

    thermoProScan.start(thermoProScan)
