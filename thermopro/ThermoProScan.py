# start pyinstaller --onedir ThermoProScan.py --icon=ThermoPro.jpg --nowindowed --noconsole
import atexit
import csv
import ctypes
import json
import os
import os.path
import sys
import threading
import traceback
from collections.abc import Sequence
from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from tkinter import PhotoImage
from typing import Any

import matplotlib
import matplotlib.dates as m_dates
import matplotlib.pyplot as plt
import mplcursors
import pandas
import pandas as pd
import requests
import schedule
from matplotlib.dates import date2num, num2date
from matplotlib.lines import Line2D
from matplotlib.widgets import CheckButtons, Slider, Button
from pandas import DataFrame

import thermopro
from constants import OUTPUT_CSV_FILE, WEATHER_URL, MIN_HPA, MAX_HPA, DAYS, LOCATION, NEVIWEB_EMAIL, NEVIWEB_PASSWORD, COLUMNS
from thermopro import log, PATH
from thermopro.HydroQuébec import HydroQuébec
from thermopro.NeviwebTemperature import NeviwebTemperature
from thermopro.Rtl433Temperature2 import Rtl433Temperature2


# C:\Users\ADELE\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
# https://github.com/merbanan/rtl_433
# https://github.com/dvd-dev/hilo/


# sys.path.append(f'{HOME_PATH}/Documents//BkpScripts')
# from Secrets import OPEN_WEATHER_API_KEY, NEVIWEB_EMAIL, NEVIWEB_PASSWORD


class ThermoProScan:

    def __init__(self):
        log.info('Starting ThermoProScan')
        atexit.register(self.__cleanup_function)

    def load_csv(self) -> list[dict]:
        log.info('load_csv')
        if os.path.isfile(OUTPUT_CSV_FILE):
            result = pd.read_csv(OUTPUT_CSV_FILE)
            result = result.astype({'time': 'datetime64[ns]'})
            result = result.astype({'ext_temp': 'float'})
            result = result.astype({'int_temp': 'float'})
            result = result.astype({'open_temp': 'float'})
            result = result.astype({'open_feels_like': 'float'})
            try:
                result = result.astype({'open_humidity': 'Int64'})
            except Exception as ex:
                result = result.astype({'open_humidity': 'float'})
            try:
                result = result.astype({'open_pressure': 'Int64'})
            except Exception as ex:
                result = result.astype({'open_pressure': 'float'})

            result = result.astype({'ext_humidex': 'Int64'})
            return result.to_dict('records')
        else:
            log.error(f'The path "{OUTPUT_CSV_FILE}" does not exit.')
        return []

    # https://home.openweathermap.org/statistics/onecall_30
    def __load_open_weather(self, result_queue: Queue):
        log.info("----------------------- Start load_open_weather -----------------------")
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
                    "open_wind_gust": round(current['wind_gust'], 2) if current.get("wind_gust") else None,
                    "open_wind_deg": round(current['wind_deg'], 0),

                    "open_rain": round(current['rain']["1h"], 2) if current.get('rain') else None,  # mm/h
                    "open_snow": round(current['snow']["1h"], 2) if current.get('snow') else None,  # mm/h

                    "open_description": f"{current['weather'][0]['main']}, {current['weather'][0]['description']}" if current.get('weather') else '',
                    "open_icon": current['weather'][0]['icon'] if current.get('weather') else None,
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

    # https://stackoverflow.com/questions/7908636/how-to-add-hovering-annotations-to-a-plot

    def create_graph(self, popup: bool) -> None:
        try:
            log.info('create_graph')
            csv_data = self.load_csv()
            if bool(csv_data):
                sorted_datas = sorted(csv_data, key=lambda d: d["time"])
                df = pd.DataFrame(sorted_datas)
                df.set_index('time')

                pandas.set_option('display.max_columns', None)
                pandas.set_option('display.width', 1000)
                pandas.set_option('display.max_rows', 1000)
                log.info(f'\n{df[len(df) - 50:]}')

                fig, ax1 = plt.subplots()
                ax2 = ax1.twinx()

                ax1.set_ylabel('Humidity %', color='xkcd:royal blue')  # we already handled the x-label with ax1
                ax1.grid(axis='y', color='blue', linewidth=0.2)
                ax1.set_yticks(list(range(0, 101, 10)))

                ext_humidity, = ax1.plot(df["time"], df["ext_humidity"], color='xkcd:royal blue', label='Ext. %')
                open_humidity, = ax1.plot(df["time"], df["open_humidity"], color='xkcd:sky blue', label='Open %')
                open_pressure, = ax1.plot(df["time"], (df["open_pressure"] - MIN_HPA) / ((MAX_HPA - MIN_HPA) / 100), color='xkcd:black', label='hPa')

                ax1.xaxis.set_major_formatter(m_dates.DateFormatter('%Y/%m'))
                ax1.xaxis.set_major_locator(m_dates.MonthLocator(interval=1))
                ax1.xaxis.set_minor_formatter(m_dates.DateFormatter('%d'))
                ax1.xaxis.set_minor_locator(m_dates.WeekdayLocator(byweekday=m_dates.SU.weekday, interval=1))
                ax1.grid(axis='x', color='black', which="major", linewidth=0.2)
                ax1.grid(axis='x', color='black', which="minor", linewidth=0.1)
                ax1.tick_params(axis='both', which='minor', labelsize='small')
                plt.xticks(rotation=45, ha='right', fontsize='9')
                plt.gcf().autofmt_xdate()

                ext_humidex, = ax2.plot(df["time"], df["ext_humidex"], color='xkcd:pink', label='Humidex')
                open_feels_like, = ax2.plot(df["time"], df["open_feels_like"], color='xkcd:rose pink', label='OpenHumidex')

                ext_temp, = ax2.plot(df["time"], df["ext_temp"], color='xkcd:scarlet', label='Ext. °C')
                int_temp, = ax2.plot(df["time"], df["int_temp"], color='xkcd:red', label='Int. °C')
                open_temp, = ax2.plot(df["time"], df["open_temp"], color='xkcd:brick red', label='Open °C')

                ax2.set_ylabel('Temperature °C', color='xkcd:scarlet')
                ax2.grid(axis='y', linewidth=0.2, color='xkcd:scarlet')
                ax2.set_yticks(list(range(int(df['ext_temp'].min(numeric_only=True) - 0.5),
                                          int(max(df['ext_temp'].max(numeric_only=True) + 0.5,
                                                  df['ext_humidex'].max(numeric_only=True) + 0.5,
                                                  df['int_temp'].max(numeric_only=True) + 0.5,
                                                  df['open_temp'].max(numeric_only=True) + 0.5,
                                                  df['open_feels_like'].max(numeric_only=True) + 0.5
                                                  )))))
                ax2.plot(df["time"], df.rolling(window=f'{DAYS}D', on='time')['ext_temp'].mean(), color='xkcd:deep red', alpha=0.3, label='°C')
                ax2.plot(df["time"], df.rolling(window=f'{DAYS}D', on='time')['int_temp'].mean(), color='xkcd:red', alpha=0.3, label='°C')
                ax1.plot(df["time"], df.rolling(window=f'{DAYS}D', on='time')['ext_humidity'].mean(), color='xkcd:deep blue', alpha=0.3, label='%')
                plt.axhline(0, linewidth=1, color='black')

                plt.axis((
                    df['time'][0] - timedelta(hours=1),
                    df["time"][df["time"].size - 1] + timedelta(hours=1),
                    df['ext_temp'].min(numeric_only=True) - 1,
                    max(df['ext_temp'].max(numeric_only=True) + 0.5,
                        df['ext_humidex'].max(numeric_only=True) + 0.5,
                        df['int_temp'].max(numeric_only=True) + 0.5,
                        df['open_temp'].max(numeric_only=True) + 0.5,
                        df['open_feels_like'].max(numeric_only=True) + 0.5
                        )))

                try:
                    plt.title(
                        f"Date: {df['time'][len(df['time']) - 1].strftime('%Y/%m/%d %H:%M')}, Int: {df['int_temp'][len(df['int_temp']) - 1]}°C, Ext.: {df['ext_temp'][len(df['ext_temp']) - 1]}°C, " \
                        + f"{int(df['ext_humidity'][len(df['ext_humidity']) - 1])}%, Humidex: {(df['ext_humidex'][len(df['ext_humidex']) - 1])}, " \
                        + f"Open: {df['open_temp'][len(df['open_temp']) - 1]}°C, Open: {int(df['open_humidity'][len(df['open_humidity']) - 1])}%, Open Humidex: {int(df['open_feels_like'][len(df['open_feels_like']) - 1])}, " \
                        + f'Pressure: {int(df['open_pressure'][len(df['open_pressure']) - 1])} hPa, Rolling x̄: {DAYS} days', fontsize=10)
                except Exception as ex:
                    log.error(ex)
                    log.error(traceback.format_exc())

                plt.tight_layout()
                fig.subplots_adjust(
                    left=0.055,
                    bottom=0.105,
                    right=0.952,
                    top=0.948,
                    wspace=0.198,
                    hspace=0.202
                )

                def on_clicked(label):
                    line: Line2D | None = None
                    for line in all_lines:
                        if line.get_label() == label:
                            break
                    line.set_visible(not line.get_visible())
                    line.figure.canvas.draw_idle()

                    check.eventson = False
                    if label == 'Select All/None':
                        for i in range(len(all_lines)):
                            line2 = all_lines[i]
                            line2.set_visible(line.get_visible())
                            line2.figure.canvas.draw_idle()
                            # print(line2.get_visible())
                            check.set_active(i, line.get_visible())
                    check.eventson = True

                select: Line2D = Line2D([1], [1], label='Select All/None', color='black')
                select.set_figure(ext_temp.figure)
                select.figure.set_canvas(ext_temp.figure.canvas)

                all_lines: list[Line2D] = [select, open_pressure, int_temp, ext_temp, open_temp, ext_humidity, open_humidity, ext_humidex, open_feels_like]
                lines_label: Sequence[str] = [str(line.get_label()) for line in all_lines]
                lines_colors: Sequence[str] = [line.get_color() for line in all_lines]
                lines_actives: Sequence[bool] = [line.get_visible() for line in all_lines]
                check = CheckButtons(
                    ax=ax1.inset_axes((0.0, 0.0, 0.14, 0.3)),
                    labels=lines_label,
                    actives=lines_actives,
                    label_props={'color': lines_colors},
                    frame_props={'edgecolor': lines_colors},
                    check_props={'facecolor': lines_colors},
                )
                check.on_clicked(on_clicked)

                def on_changed(val):
                    slider_position.valtext.set_text(num2date(val).date())
                    df2 = df.set_index(['time'])
                    df2 = df2[num2date(val - DAYS).date():num2date(val + DAYS).date()]

                    window = (
                        val - DAYS,
                        val + 0.1,
                        min(df2['ext_humidity'].min(numeric_only=True), df2['open_humidity'].min(numeric_only=True)) - 1,
                        max(df2['ext_humidity'].min(numeric_only=True), df2['open_humidity'].min(numeric_only=True)) + 1
                    )
                    ax1.axis(window)
                    ax1.set_yticks(list(range(0, 101, 10)))
                    ax1.xaxis.set_major_formatter(m_dates.DateFormatter('%Y/%m/%d'))
                    ax1.xaxis.set_major_locator(m_dates.DayLocator(interval=1))

                    window2 = (
                        val - DAYS,
                        val + 0.1,
                        df2['ext_temp'].min(numeric_only=True) - 1,
                        max(
                            df2['ext_temp'].max(numeric_only=True) + 0.5,
                            df2['ext_humidex'].max(numeric_only=True) + 0.5,
                            df2['int_temp'].max(numeric_only=True) + 0.5,
                            df2['open_temp'].max(numeric_only=True) + 0.5,
                            df2['open_feels_like'].max(numeric_only=True) + 0.5
                        ) + 1
                    )
                    ax2.axis(window2)
                    ax2.set_yticks(list(range(int(df2['ext_temp'].min(numeric_only=True) - 1.1),
                                              int(max(
                                                  df2['ext_temp'].max(numeric_only=True) + 0.5,
                                                  df2['ext_humidex'].max(numeric_only=True) + 0.5,
                                                  df2['int_temp'].max(numeric_only=True) + 0.5,
                                                  df2['open_temp'].max(numeric_only=True) + 0.5,
                                                  df2['open_feels_like'].max(numeric_only=True) + 0.5
                                              ) + 1.1), 1)))

                    fig.canvas.draw_idle()

                def reset(event) -> None:
                    slider_position.reset()
                    ax1.axis((
                        df['time'][0] - timedelta(hours=1),
                        df["time"][df["time"].size - 1] + timedelta(hours=1),
                        0,
                        100
                    ))
                    ax1.xaxis.set_major_formatter(m_dates.DateFormatter('%Y/%m'))
                    ax1.xaxis.set_major_locator(m_dates.MonthLocator(interval=1))
                    ax1.xaxis.set_minor_formatter(m_dates.DateFormatter('%d'))
                    ax1.xaxis.set_minor_locator(m_dates.WeekdayLocator(byweekday=m_dates.SU.weekday, interval=1))

                    ax2.axis((
                        df['time'][0] - timedelta(hours=1),
                        df["time"][df["time"].size - 1] + timedelta(hours=1),
                        df['ext_temp'].min(numeric_only=True) - 1,
                        max(df['ext_temp'].max(numeric_only=True), df['ext_humidex'].max(numeric_only=True), df['int_temp'].max(numeric_only=True)) + 1
                    ))
                    ax2.set_yticks(list(range(int(df['ext_temp'].min(numeric_only=True) - 1),
                                              int(max(df['ext_temp'].max(numeric_only=True),
                                                      df['ext_humidex'].max(numeric_only=True),
                                                      df['int_temp'].max(numeric_only=True)
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
                    initcolor='none',
                )
                slider_position.valtext.set_text(df["time"][0].date())
                slider_position.on_changed(on_changed)
                button = Button(fig.add_axes((0.9, 0.01, 0.055, 0.03)), 'Reset', hovercolor='0.975')
                button.on_clicked(reset)
                slider_position.set_val(date2num(df['time'][len(df['time']) - 1]))

                # https://www.geeksforgeeks.org/data-visualization/adding-tooltips-to-a-timeseries-chart-hover-tool-in-python-bokeh/
                mplcursors.cursor(open_pressure, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                    f'Pression: {int(float(sel[1][1]) * float((MAX_HPA - MIN_HPA) / 100.0) + MIN_HPA)} {sel[0].get_label()}'
                ))
                # for line in all_lines:
                #     if line.get_label() != 'Select All/None' and line.get_label() != 'hPa':
                #         print(line)
                #         mplcursors.cursor(line, hover=True).connect("add", lambda sel: sel.annotation.set_text(
                #             f'{{sel[0].get_label()}}: {sel[1][1]}'
                #         ))

                fig.canvas.manager.set_window_title('ThermoPro Graph')
                dpi = fig.get_dpi()
                fig.set_size_inches(1280.0 / float(dpi), 720.0 / float(dpi))
                plt.savefig(PATH + 'ThermoProScan.png')

                if popup:
                    manager = matplotlib.pyplot.get_current_fig_manager()
                    img = PhotoImage(file=f'{LOCATION}ThermoPro.png')
                    manager.window.tk.call('wm', 'iconphoto', manager.window._w, img)
                    plt.show()

            else:
                log.warning('csv_data is empty')
                if popup:
                    ctypes.windll.user32.MessageBoxW(0, "csv_data is empty", 'ThermoProGraph Error', 16)
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
            if popup:
                ctypes.windll.user32.MessageBoxW(0, f'{ex}', "ThermoProGraph Error", 16)

    def __call_all(self) -> None:
        log.info('')
        log.info('--------------------------------------------------------------------------------')
        log.info("Start task")
        json_data: dict[str, Any] = {}
        threads: list[threading.Thread] = []
        result_queue: Queue = Queue()

        thread: threading.Thread = threading.Thread(target=Rtl433Temperature2().call_rtl_433, args=(result_queue,))
        threads.append(thread)
        thread.start()

        thread: threading.Thread = threading.Thread(target=NeviwebTemperature().load_neviweb, args=(result_queue,))
        threads.append(thread)
        thread.start()

        thread: threading.Thread = threading.Thread(target=self.__load_open_weather, args=(result_queue,))
        threads.append(thread)
        thread.start()

        thread: threading.Thread = threading.Thread(target=HydroQuébec().start, args=(result_queue,))
        threads.append(thread)
        thread.start()

        for thread in threads:
            thread.join()

        while not result_queue.empty():
            json_data.update(result_queue.get())

        kwh_list = json_data['kwh_list']
        del json_data['kwh_list']

        log.info('----------------------------------------------')
        log.info(f'Got all new data:\n{json.dumps(json_data, indent=4, sort_keys=True, default=str)}')
        log.info('----------------------------------------------')

        is_new_file = False if (os.path.isfile(OUTPUT_CSV_FILE) and os.stat(OUTPUT_CSV_FILE).st_size > 0) else True
        try:
            with open(OUTPUT_CSV_FILE, "a", newline='') as csvfile:
                writer = csv.writer(csvfile)
                if is_new_file:
                    writer.writerow(COLUMNS)

                if json_data:
                    data: list[Any] = []
                    for col in COLUMNS:
                        if col == 'time':
                            data.append(datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
                        elif type(json_data.get(col)) == datetime:
                            data.append(json_data.get(col).strftime('%Y/%m/%d %H:%M:%S')) if json_data.get(col) else data.append(None)
                        elif type(json_data.get(col)) == float and pd.isna(json_data.get(col)):
                            data.append(None)
                        else:
                            data.append(json_data.get(col)) if json_data.get(col) else data.append(None)

                    writer.writerow(data)
                log.info("line CSV file writen")

            kwh_df = self.set_kwh(kwh_list)
            self.save_csv(kwh_df)
            self.create_graph(False)
        except Exception as ex:
            log.error(ex)
            log.error(json_data)
            log.error(traceback.format_exc())
        finally:
            # kwh_df = self.set_kwh(kwh_list)
            # self.save_csv(kwh_df)
            # self.create_graph(False)
            log.info("End task")

    def save_csv(self, kwh_df: DataFrame | None) -> None:
        log.info('Saving csv file...')
        if kwh_df is None:
            log.warning('kwh_df is empty')
        else:
            with open(OUTPUT_CSV_FILE + '.tmp', 'w', newline='') as writer:
                writer = csv.writer(writer)
                writer.writerow(COLUMNS)
                for index, row in kwh_df.iterrows():
                    data: list[Any] = []
                    for col in COLUMNS:
                        if col == 'time':
                            data.append(row[col].strftime('%Y/%m/%d %H:%M:%S'))
                        elif type(row[col]) == datetime:
                            data.append(row[col].strftime('%Y/%m/%d %H:%M:%S')) if row[col] else data.append(None)
                        elif type(row[col]) == float and pd.isna(row[col]):
                            data.append(None)
                        else:
                            data.append(row[col]) if row[col] else data.append(None)
                    writer.writerow(data)

            if os.path.exists(OUTPUT_CSV_FILE):
                try:
                    os.remove(OUTPUT_CSV_FILE)
                except Exception as ex:
                    log.error(ex)
            os.renames(OUTPUT_CSV_FILE + '.tmp', OUTPUT_CSV_FILE)
            log.info('csv file saved.')

    def start(self):
        try:
            log.info('ThermoProScan started')
            i = 0
            while not os.path.exists(PATH) and i < 5:
                log.warning(f'The path "{PATH}" not ready.')
                i += 1
                sleep(10)
            if not os.path.exists(PATH):
                ctypes.windll.user32.MessageBoxW(0, "Mapping not ready.", "Warning!", 16)
                sys.exit()

            self.__call_all()
            schedule.every().hour.at(":00").do(self.__call_all)
            while True:
                schedule.run_pending()
                sleep(1)
        except KeyboardInterrupt as ki:
            pass
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    def __cleanup_function(self):
        try:
            log.info('ThermoProScan stopping...')
            schedule.clear()
            log.info('ThermoProScan stopped')
            sys.exit()
        except SystemExit as ex:
            pass

    # https://stackoverflow.com/questions/13148429/how-to-change-the-order-of-dataframe-columns
    def set_kwh(self, kwh_list: list[dict[str, Any]]) -> DataFrame | None:
        try:
            if len(kwh_list) != 0:
                csv_data = self.load_csv()
                if bool(csv_data):
                    sorted_datas = sorted(csv_data, key=lambda d: d["time"])
                    df = pd.DataFrame(sorted_datas)
                    df.set_index('time')

                    start_date = datetime.now().replace(day=datetime.now().month - 2).strftime('%Y-%m-%d')
                    end_date = datetime.now().replace(day=datetime.now().day + 1).strftime('%Y-%m-%d')
                    filtered_df = df.loc[(df['time'] >= start_date) & (df['time'] <= end_date)]

                    df['kwh_hydro_quebec'] = None
                    for index, line1 in filtered_df.iterrows():
                        day1 = line1['time'].strftime('%Y-%m-%d')
                        hour1 = line1['time'].hour
                        for line2 in kwh_list:
                            day2 = line2.get('day').replace('/', '-')
                            hour2 = datetime.strptime(line2.get('hour'), '%H:%M:%S').hour
                            if hour2 == hour1 and day2 == day1:
                                df.loc[index, 'kwh_hydro_quebec'] = line2.get('consoTotal')
                    return df
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
        return None


if __name__ == '__main__':
    thermopro.set_up(__file__)
    log.info('ThermoProScan Starting...')
    thermoProScan: ThermoProScan = ThermoProScan()
    thermoProScan.start()
    sys.exit()

    # open_snow -> open_description
    # open_description -> open_temp  open_feels_like
    # open_icon -> open_sunrise
    # int_temp_bureau -> open_visibility
    # ext_temp_Thermopro-TX2 => open_sunrise

    # open_sunset -> open_pressure
    # ext_humidity_Rubicson-Temperature -> open_sunset
    # ext_temp_Thermopro-TX2 -> open_sunrise

    #
    # 6591:8407
    sorted_datas = sorted(thermoProScan.load_csv(), key=lambda d: d["time"])
    df = pd.DataFrame(sorted_datas)
    df.set_index('time')
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_rows', None)
    # log.info(f'kwh_df:\n{df[6590 - 5:8407 + 1]}')
    # log.info(f'kwh_df:\n{df[6590 - 5:8407 + 1][['open_sunset', 'open_pressure', 'ext_humidity_Rubicson-Temperature']]}')
    for index, row in df[6590 - 5:8407 + 1].iterrows():
        # print(type(row['open_sunset']), float(row['open_sunset']))
        # df.at[index, 'open_rain'] = None
        # df.at[index, 'open_uvi'] = None
        # df.at[index, 'open_wind_gust'] = None
        # df.at[index, 'open_wind_deg'] = None
        #
        # df.at[index, 'int_temp'] = row['open_clouds']
        # df.at[index, 'open_clouds'] = None
        #
        # df.at[index, 'open_visibility'] = row['open_wind_deg']
        # df.at[index, 'int_temp_bureau'] = None
        #
        # df.at[index, 'open_visibility'] = row['int_temp_bureau']
        # df.at[index, 'int_temp_bureau'] = None
        #
        # df.at[index, 'open_description'] = row['open_snow']
        # df.at[index, 'open_snow'] = None
        #
        # df.at[index, 'open_humidity'] = float(row['open_icon'])
        # df.at[index, 'open_icon'] = None
        #
        # df.at[index, 'open_pressure'] = float(row['open_sunset'])
        # df.at[index, 'open_sunset'] = None
        #
        # df.at[index, 'open_sunset'] = row['ext_humidity_Rubicson-Temperature']
        # df.at[index, 'ext_humidity_Rubicson-Temperature'] = None
        #
        # df.at[index, 'open_sunrise'] = row['ext_temp_Thermopro-TX2']
        # df.at[index, 'ext_temp_Thermopro-TX2'] = None

        # df.at[index, 'ext_humidex'] = float(row['open_wind_speed'])
        # df.at[index, 'open_wind_speed'] = None
        df.at[index, 'ext_humidex'] = None
        pass
    # pass
    log.info(f'kwh_df:\n{df[6590 - 5:6590 + 5]}')
    log.info(f'kwh_df:\n{df[8407 - 5:8407 + 5]}')
    thermoProScan.save_csv(df)

# cols = ["time", "ext_temp", "ext_humidity", 'int_temp', 'ext_humidex', 'open_temp', 'open_feels_like', 'open_humidity', 'open_pressure', 'open_clouds', 'open_visibility',
#         'open_wind_speed', 'open_wind_gust', 'open_wind_deg', 'open_rain', 'open_snow', 'open_description', 'open_icon', 'open_sunrise', 'open_sunset', 'open_uvi',
#         'ext_temp_162', 'ext_temp_02', 'ext_humidity_162', 'ext_humidity_02', 'load_watt', 'int_temp_bureau', 'int_temp_chambre', 'int_temp_salle-de-bain', 'int_temp_salon']
# print(f'{[col for col in cols]},')
