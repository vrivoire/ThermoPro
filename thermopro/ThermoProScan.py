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
from datetime import datetime
from queue import Queue
from time import sleep
from typing import Any

import pandas
import pandas as pd
import requests
import schedule
from dateutil.relativedelta import relativedelta
from pandas import DataFrame

import thermopro
from constants import OUTPUT_CSV_FILE, WEATHER_URL, NEVIWEB_EMAIL, NEVIWEB_PASSWORD, COLUMNS, BKP_PATH, OUTPUT_JSON_FILE, BKP_DAYS
from thermopro import log, show_df, POIDS_PRESSION_PATH
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
                    "open_wind_gust": round(current['wind_gust'], 2) if current.get("wind_gust") else 0.0,
                    "open_wind_deg": round(current['wind_deg'], 0),

                    "open_rain": round(current['rain']["1h"], 2) if current.get('rain') else 0.0,  # mm/h
                    "open_snow": round(current['snow']["1h"], 2) if current.get('snow') else 0.0,  # mm/h

                    "open_description": f"{current['weather'][0]['main']}, {current['weather'][0]['description']}" if current.get('weather') else '',
                    "open_icon": current['weather'][0]['icon'] if current.get('weather') else '',
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

    def __call_all(self) -> None:
        json_data: dict[str, Any] = {}
        try:
            log.info('')
            log.info('--------------------------------------------------------------------------------')
            log.info("Start task")

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
            room_temperature_display_list: list = json_data.get('room_temperature_display_list')
            if room_temperature_display_list is not None and len(room_temperature_display_list) > 0:
                if json_data['int_temp'] is not None:
                    room_temperature_display_list.append(json_data['int_temp'])
                int_temp: float = round(sum(room_temperature_display_list) / len(room_temperature_display_list), 1)
                log.info(f'Was int_temp={json_data['int_temp']}, now int_temp={int_temp}, {room_temperature_display_list}')
                json_data['int_temp'] = int_temp

            for col in list(json_data.keys()):
                if col not in COLUMNS:
                    try:
                        del json_data[col]
                    except KeyError as ke:
                        log.warning(ke)

            log.info('----------------------------------------------')
            log.info(f'Got all new data:\n{json.dumps(json_data, indent=4, sort_keys=True, default=str)}')
            log.info('----------------------------------------------')

            df: DataFrame = self.load_json()
            if json_data:
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

            self.set_kwh(kwh_dict, df)

            self.save_csv(df)
            self.save_json(df)
            self.save_bkp(df)

            show_df(df)
        except Exception as ex:
            log.error(ex)
            log.error(thermopro.ppretty(json_data))
            log.error(traceback.format_exc())
            thread = threading.Thread(target=ctypes.windll.user32.MessageBoxW, args=(0, f"Genaral Error\n{ex}", "Genaral Error", 0x30))
            thread.start()
            threads.append(thread)
        log.info("End task")

    def save_json(self, df: DataFrame):
        df = ThermoProScan.set_astype(df)
        df.to_json(OUTPUT_JSON_FILE, orient='records', indent=4, date_format='iso')
        # for orient in ['columns', 'index', 'split', 'table']:
        #     print(f'{OUTPUT_JSON_FILE[:OUTPUT_JSON_FILE.rfind('.')]}_{orient}.json')
        #     df.to_json(f'{OUTPUT_JSON_FILE[:OUTPUT_JSON_FILE.rfind('.')]}_{orient}.json', orient=orient, indent=4, date_format='iso')
        log.info('JSON saved')

    def save_csv(self, df: DataFrame | None) -> bool:
        df = ThermoProScan.set_astype(df)
        if df is None:
            log.warning('df is empty')
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
                            data.append(row[col]) if not pd.isna(row[col]) or not row[col] is None else data.append(None)
                    writer.writerow(data)

            if os.path.exists(OUTPUT_CSV_FILE):
                try:
                    os.remove(OUTPUT_CSV_FILE)
                except Exception as ex:
                    log.error(ex)
            os.renames(OUTPUT_CSV_FILE + '.tmp', OUTPUT_CSV_FILE)
            log.info('CSV saved.')
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

                for index, line1 in filtered_df.iterrows():
                    key = f'{line1['time'].strftime('%Y-%m-%d')} {line1['time'].strftime('%H')}'
                    kwh: float = kwh_dict.get(key) if kwh_dict.get(key) else 0.0
                    df.loc[index, 'kwh_hydro_quebec'] = kwh

            log.info(f'KWH: {count} rows updated.')
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    def save_bkp(self, df: DataFrame) -> None:
        try:
            in_file_list: list[str] = [files_csv.replace('\\', '/') for files_csv in glob.glob(os.path.join(POIDS_PRESSION_PATH, '*.csv'))] + [files_json.replace('\\', '/') for files_json in glob.glob(os.path.join(POIDS_PRESSION_PATH, '*.json'))]
            log.info(f'Files to bkp: {in_file_list}')

            out_file_list: list[str] = [BKP_PATH + file[file.rindex('/') + 1:file.rindex('.')] + datetime.now().strftime('_%Y-%m-%d_%H-%M-%S') + file[file.rindex('.'):] for file in in_file_list]

            for i, name in enumerate(in_file_list):
                shutil.copy2(in_file_list[i], out_file_list[i])

            file_name = 'ThermoProScan'
            zip_file_name = f'{BKP_PATH}{file_name}_{datetime.now().strftime("%Y-%m-%d")}.zip'
            with zipfile.ZipFile(zip_file_name, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
                for file in out_file_list:
                    zip_file.write(file, arcname=file[file.replace('\\', '/').rfind('/') + 1:])

                    original: float = 0.0
                    compressed: float = 0.0
                    for info in zip_file.infolist():
                        original += info.file_size / 1024
                        compressed += info.compress_size / 1024
                log.info(f"Zipped files, original: {round(original, 2)} Ko, compressed: {round(compressed, 2)} Ko. ratio: {round(100 - (compressed / original) * 100, 2)}%")
                log.info(f"Zip file created at: {zip_file_name}")

            try:
                [os.remove(out_file) for out_file in out_file_list]
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
                result = result.astype({'ext_temp': 'Float64'})
                result = result.astype({'int_temp': 'Float64'})
                result = result.astype({'open_temp': 'Float64'})
                result = result.astype({'open_feels_like': 'Float64'})
                try:
                    result = result.astype({'open_humidity': 'Int64'})
                except Exception as ex:
                    result = result.astype({'open_humidity': 'Float64'})
                try:
                    result = result.astype({'open_pressure': 'Int64'})
                except Exception as ex:
                    result = result.astype({'open_pressure': 'Float64'})
                result = result.astype({'kwh_hydro_quebec': 'Float64'})
                result = result.astype({'ext_humidex': 'Int64'})
                # return result.to_dict('records')
                return result
            else:
                log.error(f'The path "{OUTPUT_CSV_FILE}" does not exit.')
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
        return None

    @staticmethod
    def load_json() -> DataFrame:
        try:
            df: DataFrame
            if os.path.exists(OUTPUT_JSON_FILE):
                log.info(f'Loading file {OUTPUT_JSON_FILE}')
                df: DataFrame = pandas.read_json(OUTPUT_JSON_FILE)
            elif os.path.exists(OUTPUT_CSV_FILE):
                log.info(f'Loading file {OUTPUT_CSV_FILE}')
                df: DataFrame = pandas.read_csv(OUTPUT_CSV_FILE)
            else:
                raise f"The files {OUTPUT_JSON_FILE} and {OUTPUT_CSV_FILE} do not exist."

            # df = df.drop('ext_humidity_Acurite-609TXC', axis=1)
            # df = df.drop('ext_temp_Acurite-609TXC', axis=1)

            df = ThermoProScan.set_astype(df)

            df_conditional_drop = df.drop(df[
                                              (df['time'].dt.minute >= 6) &
                                              (df['time'].dt.minute <= 59) &
                                              (df['time'] <= (datetime.now() - relativedelta(weeks=1)))
                                              ].index)
            log.info(f'Purged {len(df) - len(df_conditional_drop)} rows {len(df)}, {len(df_conditional_drop)}.')
            df = df_conditional_drop.reset_index(drop=True)

            df = df[COLUMNS]
            return df
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
            raise ex

    @staticmethod
    def set_astype(df: DataFrame) -> DataFrame:
        columns = list(COLUMNS)
        for col in ['time', 'open_sunrise', 'open_sunset']:
            df = df.astype({col: 'datetime64[ns]'})
            columns.remove(col)
        for col in ['ext_humidex', 'ext_humidity', 'int_humidity', 'ext_humidity_Thermopro-TX2', 'int_humidity_Acurite-609TXC', 'open_clouds', 'open_humidity', 'open_pressure', 'open_visibility', 'open_wind_deg']:
            try:
                df[col] = df[col].round().astype('Int64')
            except KeyError as ex:
                log.error(df[col].dtypes)
                log.error(ex)
                log.error(traceback.format_exc())
            columns.remove(col)
        for col in ['open_description', 'open_icon']:
            df[col] = df[col].astype(str)
            columns.remove(col)
        for col in columns:
            try:
                df[col] = df[col].astype('Float64')
            except KeyError as ex:
                log.error(df[col].dtypes)
                log.error(ex)
                log.error(traceback.format_exc())

        df.set_index('time')
        all_columns2: list[str] = sorted(df.columns.tolist())
        all_columns2.remove('time')
        all_columns2 = ['time'] + all_columns2
        df = df[all_columns2]
        df = df.sort_values(by='time', ascending=True)
        return df


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

    df = thermoProScan.load_json()
    # thermoProScan.save_json(df)
