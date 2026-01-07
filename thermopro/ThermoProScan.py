# start pyinstaller --onedir ThermoProScan.py --icon=ThermoPro.jpg --nowindowed --noconsole
import atexit
import ctypes
import glob
import json
import os
import os.path
import shutil
import statistics
import sys
import threading
import traceback
import zipfile
from datetime import datetime
from queue import Queue
from time import sleep
from typing import Any

import pandas as pd
import schedule
from dateutil.relativedelta import relativedelta
from pandas import DataFrame

import thermopro
from constants import NEVIWEB_EMAIL, NEVIWEB_PASSWORD, COLUMNS, BKP_PATH, BKP_DAYS, POIDS_PRESSION_PATH
from thermopro import log, show_df
from thermopro.HydroQuébecPower import HydroQuébec
from thermopro.NeviwebTemperature import NeviwebTemperature
from thermopro.OpenWeather import OpenWeather
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

    def __call_all(self) -> None:
        json_data: dict[str, Any] = {}
        threads: list[threading.Thread] = []
        result_queue: Queue = Queue()
        try:
            log.info('')
            log.info('--------------------------------------------------------------------------------')
            log.info("Start task")

            thread: threading.Thread = threading.Thread(target=Rtl433Temperature2().call_rtl_433, args=(result_queue,))
            threads.append(thread)
            thread.start()

            thread: threading.Thread = threading.Thread(target=NeviwebTemperature().load_neviweb, args=(result_queue,))
            threads.append(thread)
            thread.start()

            thread: threading.Thread = threading.Thread(target=OpenWeather().load_open_weather, args=(result_queue,))
            threads.append(thread)
            thread.start()

            thread: threading.Thread = threading.Thread(target=HydroQuébec().start, args=(result_queue,))
            threads.append(thread)
            thread.start()

            for thread in threads:
                thread.join()

            while not result_queue.empty():
                json_data.update(result_queue.get())

            self.__get_int_means(json_data)

            kwh_dict: dict[str, float] = json_data['kwh_dict']

            for col in list(json_data.keys()):
                if col not in COLUMNS:
                    try:
                        del json_data[col]
                    except KeyError as ke:
                        log.warning(ke)

            log.info('----------------------------------------------')
            log.info(f'Got all new data:\n{json.dumps(json_data, indent=4, sort_keys=True, default=str)}')
            log.info('----------------------------------------------')

            df: DataFrame = thermopro.load_json()
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

            thermopro.save_json(df)
            self.save_bkp()

            show_df(df)
        except Exception as ex:
            log.error(ex)
            log.error(thermopro.ppretty(json_data))
            log.error(traceback.format_exc())
            thread = threading.Thread(target=ctypes.windll.user32.MessageBoxW, args=(0, f"Genaral Error\n{ex}", "Genaral Error", 0x30))
            thread.start()

        log.info("End task")

    def __get_int_means(self, json_data: dict[str, Any]):
        room_temperature_list: list[float] = []
        for entry in [s for s in list(json_data) if "int_temp_" in s]:
            room_temperature_list.append(json_data.get(entry))
        int_temp: float = round(statistics.mean(room_temperature_list), 2)
        log.info(f'Was int_temp={json_data['int_temp']}, now int_temp={int_temp}, {room_temperature_list}')
        json_data['int_temp'] = int_temp

        room_humidity_list: list[float] = []
        for entry in [s for s in list(json_data) if "int_humidity_" in s]:
            room_humidity_list.append(json_data.get(entry))
        int_humidity: float = round(statistics.mean(room_humidity_list), 2)
        log.info(f'Was int_humidity={json_data['int_humidity']}, now int_humidity={int_humidity}, {room_humidity_list}')
        json_data['int_humidity'] = int_humidity

    def start(self):
        try:
            log.info('ThermoProScan started')
            i = 0
            while not os.path.exists(POIDS_PRESSION_PATH) and i < 10:
                log.warning(f'The path "{POIDS_PRESSION_PATH}" not ready.')
                i += 1
                sleep(10)
            if not os.path.exists(POIDS_PRESSION_PATH):
                log.error(f'The path "{POIDS_PRESSION_PATH}" not ready.')
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
                    kwh: float = kwh_dict.get(key) if kwh_dict.get(key) else None
                    df.loc[index, 'kwh_hydro_quebec'] = kwh

            log.info(f'KWH: {count} rows updated.')
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    def save_bkp(self) -> None:
        try:
            in_file_list: list[str] = ([files_csv.replace('\\', '/') for files_csv in glob.glob(os.path.join(POIDS_PRESSION_PATH, '*.csv'))] +
                                       [files_json.replace('\\', '/') for files_json in glob.glob(os.path.join(POIDS_PRESSION_PATH, '*.json'))] +
                                       [files_json.replace('\\', '/') for files_json in glob.glob(os.path.join(POIDS_PRESSION_PATH, '*.zip'))])
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


if __name__ == '__main__':
    thermopro.set_up(__file__)
    log.info('ThermoProScan Starting...')
    thermoProScan: ThermoProScan = ThermoProScan()
    thermoProScan.start()
    sys.exit()

    # df = thermopro.load_json()
    # thermopro.save_json(df)
    # thermopro.show_df(df)
