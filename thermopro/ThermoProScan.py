# start pyinstaller --onedir ThermoProScan.py --icon=ThermoPro.jpg --nowindowed --noconsole
import atexit
import csv
import ctypes
import glob
import json
import os
import os.path
import shutil
import sys
import threading
import traceback
import zipfile
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
from dateutil.relativedelta import relativedelta
from matplotlib.dates import date2num, num2date
from matplotlib.lines import Line2D
from matplotlib.widgets import CheckButtons, Slider, Button
from pandas import DataFrame

import thermopro
from constants import OUTPUT_CSV_FILE, WEATHER_URL, MIN_HPA, MAX_HPA, DAYS, LOCATION, NEVIWEB_EMAIL, NEVIWEB_PASSWORD, COLUMNS, BKP_PATH, OUTPUT_JSON_FILE, BKP_DAYS
from thermopro import log, POIDS_PRESSION_PATH
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
            # csv_data = self.load_csv()
            # if bool(csv_data):
            # sorted_datas = sorted(csv_data, key=lambda d: d["time"])
            # df = pd.DataFrame(sorted_datas)
            # df.set_index('time')

            df = self.load_json()

            pandas.set_option('display.max_columns', None)
            pandas.set_option('display.width', 1000)
            pandas.set_option('display.max_rows', 50)
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
            kwh_hydro_quebec, = ax2.plot(df["time"], (df["kwh_hydro_quebec"] * 10), color='gray', label='KWh')

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
                        check.set_active(i, line.get_visible())
                check.eventson = True

            select: Line2D = Line2D([1], [1], label='Select All/None', color='black')
            select.set_figure(ext_temp.figure)
            select.figure.set_canvas(ext_temp.figure.canvas)

            all_lines: list[Line2D] = [select, kwh_hydro_quebec, open_pressure, int_temp, ext_temp, open_temp, ext_humidity, open_humidity, ext_humidex, open_feels_like]
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
                df2: DataFrame = df.set_index(['time'])
                df2 = df2[num2date(val - DAYS).date():num2date(val + DAYS).date()]
                window = (
                    val - DAYS,
                    val + 0.1,
                    0,
                    100
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

            # https://mplcursors.readthedocs.io/en/stable/index.html
            mplcursors.cursor(open_pressure, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}:  {int(float(sel[1][1]) * float((MAX_HPA - MIN_HPA) / 100.0) + MIN_HPA)} {sel[0].get_label()}'
            ))
            mplcursors.cursor(kwh_hydro_quebec, hover=2).connect("add", lambda sel: sel.annotation.set_text(
                f'{m_dates.num2date(sel.target[0]).strftime('%Y/%m/%d %H:00')}: {round(float(sel[1][1]) / 10, 3)} {sel[0].get_label()}'
            ))

            fig.canvas.manager.set_window_title('ThermoPro Graph')
            dpi = fig.get_dpi()
            fig.set_size_inches(1280.0 / float(dpi), 720.0 / float(dpi))
            plt.savefig(POIDS_PRESSION_PATH + 'ThermoProScan.png')

            if popup:
                manager = matplotlib.pyplot.get_current_fig_manager()
                img = PhotoImage(file=f'{LOCATION}ThermoPro.png')
                manager.window.tk.call('wm', 'iconphoto', manager.window._w, img)
                plt.show()

            # else:
            #     log.warning('csv_data is empty')
            #     if popup:
            #         ctypes.windll.user32.MessageBoxW(0, "csv_data is empty", 'ThermoProGraph Error', 16)
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

        thread: threading.Thread = threading.Thread(target=self.load_open_weather, args=(result_queue,))
        threads.append(thread)
        thread.start()

        thread: threading.Thread = threading.Thread(target=HydroQuébec().start, args=(result_queue,))
        threads.append(thread)
        thread.start()

        for thread in threads:
            thread.join()

        while not result_queue.empty():
            json_data.update(result_queue.get())

        kwh_dict: dict[str, float] = json_data['kwh_dict']

        for col in list(json_data.keys()):
            if col not in COLUMNS:
                try:
                    del json_data[col]
                except KeyError:
                    pass

        log.info('----------------------------------------------')
        log.info(f'Got all new data:\n{json.dumps(json_data, indent=4, sort_keys=True, default=str)}')
        log.info('----------------------------------------------')

        try:
            df: DataFrame = self.load_json()
            if json_data:
                # data: list[Any] = []
                data_dict: dict[str, Any] = {}
                for col in COLUMNS:
                    if col == 'time':
                        data_dict[col] = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                    elif type(json_data.get(col)) == datetime:
                        data_dict[col] = json_data.get(col).strftime('%Y/%m/%d %H:%M:%S')
                    elif type(json_data.get(col)) == float and pd.isna(json_data.get(col)):
                        pass
                    elif json_data.get(col) is None:
                        pass
                    else:
                        if type(json_data.get(col)) == float:
                            data_dict[col] = round(json_data.get(col), 2)
                        elif type(json_data.get(col)) == int:
                            data_dict[col] = int(json_data.get(col))
                        else:
                            data_dict[col] = json_data.get(col)

                df.loc[len(df)] = data_dict
                for col in ['time', 'open_sunrise', 'open_sunset']:
                    df = df.astype({col: 'datetime64[ns]'})

                for col in ['ext_humidity', 'open_humidity']:
                    pass

            self.set_kwh(kwh_dict, df)

            self.save_csv(df)
            self.save_json(df)

            self.create_graph(False)
        except Exception as ex:
            log.error(ex)
            log.error(thermopro.ppretty(json_data))
            log.error(traceback.format_exc())
        finally:
            try:
                self.save_bkp(df)
            except Exception as ex:
                log.error(ex)
                log.error(traceback.format_exc())
            log.info("End task")

    def save_json(self, df: DataFrame):
        df.to_json(OUTPUT_JSON_FILE, orient='records', indent=4, date_format='iso')
        log.info('JSON saved')

    def save_csv(self, df: DataFrame | None) -> bool:
        log.info('Saving csv file...')
        if df is None:
            log.warning('kwh_df is empty')
            return False
        else:
            columns = list(COLUMNS)
            # NE PAS EFFACER
            # columns = sorted(columns)
            # columns.remove('time')
            # columns = ['time'] + columns
            # print(columns)

            with open(OUTPUT_CSV_FILE + '.tmp', 'w', newline='') as writer:
                writer = csv.writer(writer)
                writer.writerow(columns)
                for index, row in df.iterrows():
                    data: list[Any] = []
                    for col in columns:
                        if col == 'time':
                            data.append(row[col].strftime('%Y/%m/%d %H:%M:%S'))
                        elif type(row[col]) == datetime:
                            data.append(row[col].strftime('%Y/%m/%d %H:%M:%S')) if row[col] else data.append(None)
                        elif type(row[col]) == float and pd.isna(row[col]):
                            data.append(None)
                        else:
                            # print(col, type(row[col]), pd.isna(row[col]), row[col] is None, row[col])
                            data.append(row[col]) if not pd.isna(row[col]) or not row[col] is None else data.append(None)
                    writer.writerow(data)

            if os.path.exists(OUTPUT_CSV_FILE):
                try:
                    os.remove(OUTPUT_CSV_FILE)
                except Exception as ex:
                    log.error(ex)
            os.renames(OUTPUT_CSV_FILE + '.tmp', OUTPUT_CSV_FILE)
            log.info('csv file saved.')
            return True

    def start(self):
        try:
            log.info('ThermoProScan started')
            i = 0
            while not os.path.exists(POIDS_PRESSION_PATH) and i < 5:
                log.warning(f'The path "{POIDS_PRESSION_PATH}" not ready.')
                i += 1
                sleep(10)
            if not os.path.exists(POIDS_PRESSION_PATH):
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
    def set_kwh(self, kwh_dict: dict[str, float], df: DataFrame) -> None:
        try:
            count: int = 0
            if kwh_dict:
                keys: list[str] = sorted(kwh_dict.keys())
                start_date = datetime.strptime(keys[0][0:10], "%Y-%m-%d")
                end_date = datetime.now()
                log.info(f'Setting hydro KWH, kwh_list size: {len(keys)}, first: {keys[0][0:10]}, last: {keys[len(keys) - 1][0:10]}')
                filtered_df = df.loc[(df['time'] >= start_date) & (df['time'] <= end_date)]
                filtered_df['time'].astype('datetime64[ns]')
                filtered_df.set_index('time')
                filtered_df = filtered_df.sort_values(by='time', ascending=True)
                log.info(f'DataFrame size: {len(filtered_df)}')

                df['kwh_hydro_quebec'] = df['kwh_hydro_quebec'].astype('float64')

                for index, line1 in filtered_df.iterrows():
                    key = f'{line1['time'].strftime('%Y-%m-%d')} {line1['time'].strftime('%H')}'
                    kwh: float = kwh_dict.get(key)
                    if kwh:
                        count += 1
                        df.loc[index, 'kwh_hydro_quebec'] = kwh

            log.info(f'KWH: {count} rows updated.')
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    def save_bkp(self, df: DataFrame) -> None:
        try:
            file_name: str = OUTPUT_CSV_FILE[OUTPUT_CSV_FILE.rfind('/') + 1: OUTPUT_CSV_FILE.rfind('.csv')]

            out_file_csv: str = BKP_PATH + file_name + datetime.now().strftime('_%Y-%m-%d_%H-%M-%S') + '.csv'
            out_file_json: str = BKP_PATH + file_name + datetime.now().strftime('_%Y-%m-%d_%H-%M-%S') + '.json'
            log.info(f'copy from: {OUTPUT_CSV_FILE} to {out_file_csv}')
            shutil.copy2(OUTPUT_CSV_FILE, out_file_csv)
            log.info(f'copy from: {OUTPUT_JSON_FILE} to {out_file_json}')
            shutil.copy2(OUTPUT_JSON_FILE, out_file_json)

            matching_files_csv: list[str] = glob.glob(os.path.join(BKP_PATH, file_name + '*.csv'))
            matching_files_json: list[str] = glob.glob(os.path.join(BKP_PATH, file_name + '*.json'))
            zip_file_name = f'{BKP_PATH}{file_name}_{datetime.now().strftime("%Y-%m-%d")}.zip'
            with zipfile.ZipFile(zip_file_name, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
                for file in matching_files_csv:
                    zip_file.write(file, arcname=file[file.replace('\\', '/').rfind('/') + 1:])
                for file in matching_files_json:
                    zip_file.write(file, arcname=file[file.replace('\\', '/').rfind('/') + 1:])

                original: float = 0.0
                compressed: float = 0.0
                for info in zip_file.infolist():
                    original += info.file_size / 1024
                    compressed += info.compress_size / 1024
                log.info(f"Zipped {len(zip_file.infolist())} files, original: {round(original, 2)} Ko, compressed: {round(compressed, 2)} Ko. ratio: {round(100 - (compressed / original) * 100, 2)}%")

            log.info(f"Zip file created at: {zip_file_name}, files deleted: {[file[file.replace('\\', '/').rfind('/') + 1:] for file in matching_files_csv]} | {[file[file.replace('\\', '/').rfind('/') + 1:] for file in matching_files_json]}")

            try:
                [os.remove(matching_file) for matching_file in matching_files_csv]
                [os.remove(matching_file) for matching_file in matching_files_json]
                old_zip_file_name = f'{BKP_PATH}{file_name}_{(datetime.now() - relativedelta(days=BKP_DAYS)).strftime('%Y-%m-%d')}.zip'
                if os.path.isfile(old_zip_file_name):
                    log.info(f'Deleting {BKP_DAYS} days old: {old_zip_file_name}')
                    os.remove(old_zip_file_name)
            except Exception as ex:
                log.error(ex)
                log.error(traceback.format_exc())

        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    # def load_csv(self) -> list[dict[str, Any]] | None:
    def load_csv(self) -> DataFrame | None:
        log.info(f'load_csv, columns ({len(COLUMNS)}): {COLUMNS}')
        try:
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
                result = result.astype({'kwh_hydro_quebec': 'float'})
                result = result.astype({'ext_humidex': 'Int64'})
                # return result.to_dict('records')
                return result
            else:
                log.error(f'The path "{OUTPUT_CSV_FILE}" does not exit.')
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
        return None

    def load_json(self) -> DataFrame | None:
        try:
            if os.path.exists(OUTPUT_JSON_FILE):
                log.info(f'Loading file {OUTPUT_JSON_FILE}')
                df2: DataFrame = pandas.read_json(OUTPUT_JSON_FILE)
            elif os.path.exists(OUTPUT_CSV_FILE):
                log.info(f'Loading file {OUTPUT_CSV_FILE}')
                df2: DataFrame = pandas.read_csv(OUTPUT_CSV_FILE)
            else:
                raise f"The files {OUTPUT_JSON_FILE} and {OUTPUT_CSV_FILE} do not exist."

            columns = list(COLUMNS)
            # for col in columns:
            #     df2[col] = df2[col].fillna(None)
            for col in ['time', 'open_sunrise', 'open_sunset']:
                df2 = df2.astype({col: 'datetime64[ns]'})
                columns.remove(col)
            for col in ['ext_humidity', 'ext_humidity_Acurite-609TXC', 'ext_humidity_Thermopro-TX2', 'open_humidity', 'open_pressure', 'open_wind_deg']:
                df2[col] = df2[col].round().astype('Int64')
                columns.remove(col)
            for col in ['open_description', 'open_icon']:
                df2[col] = df2[col].astype(str)
                columns.remove(col)
            for col in columns:
                df2[col] = df2[col].astype('float64')

            df2.set_index('time')
            all_columns2: list[str] = sorted(df2.columns.tolist())
            all_columns2.remove('time')
            all_columns2 = ['time'] + all_columns2
            df2 = df2[all_columns2]
            df2 = df2.sort_values(by='time', ascending=True)
            return df2
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
        return None


# def compare_df():
#     # https://www.google.com/search?q=python+compare+2+dataframes&oq=python+compare+2+dataframs&gs_lcrp=EgZjaHJvbWUqCQgBEAAYDRiABDIGCAAQRRg5MgkIARAAGA0YgAQyCAgCEAAYFhgeMggIAxAAGBYYHjIICAQQABgWGB4yCAgFEAAYFhge0gEJMTQ4MjNqMGo3qAIAsAIA&sourceid=chrome&ie=UTF-8
#     log.info('comparing df')
#     pandas.set_option('display.max_columns', None)
#     pandas.set_option('display.width', 1000)
#     pandas.set_option('display.max_rows', 1000)
#
#     df_json: DataFrame = self.load_json()
#     df_csv: DataFrame = self.load_csv()
#
#     all_columns2: list[str] = sorted(df_json.columns.tolist())
#     all_columns2.remove('time')
#     all_columns2 = ['time'] + all_columns2
#     df_json = df_json[all_columns2]
#     df_csv = df_csv[all_columns2]
#
#     print(df_csv.columns.tolist())
#     print('')
#     print(df_json.columns.tolist())
#     print('')
#     #
#     # print(f'equals: {df_csv.equals(df_json)}')
#     # print('')
#     # merged_df = pd.merge(df_json, df_csv, on='time', how='outer', indicator=True)
#     # differences = merged_df[merged_df['_merge'] != 'both']
#     # print(f'differences:\n{differences}')
#     # print('')
#     comparison_result = (df_json == df_csv)
#     print(f'comparison_result:\n{comparison_result}')
#     print('')
#     col1_diff = df_json['time'] != df_json['time']
#     print(f'Differences in Specific Columns:\n{df_json[col1_diff]}')


if __name__ == '__main__':
    thermopro.set_up(__file__)
    log.info('ThermoProScan Starting...')
    thermoProScan: ThermoProScan = ThermoProScan()
    thermoProScan.start()
    sys.exit()

    try:
        pandas.set_option('display.max_columns', None)
        pandas.set_option('display.width', 1000)
        pandas.set_option('display.max_rows', 1000)

        thermoProScan.save_bkp()
        # compare_df()
        sys.exit()

        df: DataFrame = thermoProScan.load_json()
        print(df.columns)
        print(df.info())
        print(df)
        df.to_json(OUTPUT_JSON_FILE, orient='records', indent=4, date_format='iso')

        # for orient in ['index', 'split', 'values', 'table']:
        #     output_json_file = OUTPUT_JSON_FILE[0:len(OUTPUT_JSON_FILE) - 5] + '_' + orient + '.json'
        #     print(output_json_file)
        #     df.to_json(output_json_file, orient=orient, indent=4, date_format='iso')
        sys.exit()

        # data: list[dict[str, Any]] = thermoProScan.load_csv()
        # df = pd.DataFrame(data)

        # df = pandas.read_csv(OUTPUT_CSV_FILE)
        # print(df)
        # # df = pandas.read_json(OUTPUT_JSON_FILE)
        #
        for col in ['time', 'open_sunrise', 'open_sunset']:
            df = df.astype({col: 'datetime64[ns]'})
        for col in ['ext_humidity', 'ext_humidity_Acurite-609TXC', 'ext_humidity_Thermopro-TX2', 'open_humidity', 'open_pressure', 'open_wind_deg']:
            df[col] = df[col].round().astype('Int64')

        df.set_index('time')
        all_columns: list[str] = sorted(df.columns.tolist())
        all_columns.remove('time')
        all_columns = ['time'] + all_columns
        df = df[all_columns]
        df = df.sort_values(by=all_columns, ascending=True)

        # df = thermoProScan.load_json()

        df.to_json(OUTPUT_JSON_FILE, orient='records', indent=4, date_format='iso')

        print(df)

    except Exception as ex:
        log.error(ex)
        log.error(traceback.format_exc())

    # result_queue: Queue = Queue()
    # thermoProScan.load_open_weather(result_queue)
    #
    # while not result_queue.empty():
    #     print(result_queue.get())

    # bkp dans git
