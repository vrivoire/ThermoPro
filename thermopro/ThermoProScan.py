# start pyinstaller --onedir ThermoProScan.py --icon=ThermoPro.jpg --nowindowed --noconsole
import atexit
import json
import math
import statistics
import sys
import threading
import traceback
from datetime import datetime
from queue import Queue
from time import sleep
from typing import Any

import pandas as pd
import schedule
from pandas import DataFrame

import thermopro
from constants import COLUMNS
from thermopro import log, show_df
from thermopro.HydroQuébecPower import HydroQuébec
from thermopro.NeviwebTemperature import NeviwebTemperature
from thermopro.OpenWeather import OpenWeather
from thermopro.Rtl433Temperature2 import Rtl433Temperature2


class ThermoProScan:

    def __init__(self):
        log.info('Starting ThermoProScan')
        atexit.register(self.__cleanup_function)

    def __call_all(self) -> None:
        now: datetime = datetime.now().replace(second=0, microsecond=0)
        thermopro.sensors = None
        json_data: dict[str, Any] = {}
        threads: list[threading.Thread] = []
        result_queue: Queue = Queue()
        try:
            log.info('')
            log.info('--------------------------------------------------------------------------------')
            log.info("Start task.")

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

            sensors1: dict[str, int | float | datetime] = json_data['sensors']
            sensors2: dict[str, int | float | datetime] = dict(sensors1)
            sensors1.update(json_data)
            json_result: dict[str, int | float | str | None] = self.__get_means_and_mins(sensors1)
            json_data.update(json_result)

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

            df1: DataFrame = thermopro.load_json()
            if json_data:
                data_dict: dict[str, Any] = {}
                for col in COLUMNS:
                    if col == 'time':
                        data_dict[col] = now
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

                new_row_df = pd.DataFrame([data_dict])
                df1 = pd.concat([df1, new_row_df], ignore_index=True)

                for col in ['time', 'open_sunrise', 'open_sunset']:
                    df1 = df1.astype({col: 'datetime64[ns]'})

            self.set_kwh(kwh_dict, df1)
            thermopro.set_astype(df1)
            thermopro.save_json(df1)
            thermopro.save_sensors(now, sensors2)
            thermopro.save_bkp()
            show_df(df1, title='__call_all')
        except Exception as ex:
            log.fatal(ex)
            log.fatal(traceback.format_exc())

        thermopro.display_schedule()
        log.info(f"End task, Elapsed: {datetime.now().now() - now}")

    def __get_means_and_mins(self, json_data: dict[str, int | float | datetime]) -> dict[str, int | float | str | None]:
        json_result: dict[str, int | float | str | None] = {}
        ext_temperature_list: list[float | None] = []
        for entry in [s for s in list(json_data) if "ext_temp_" in s]:
            ext_temperature_list.append(json_data.get(entry)) if not pd.isnull(json_data.get(entry)) else None
        ext_temp: float | None = round(min(ext_temperature_list), 2) if len(ext_temperature_list) > 0 else None
        json_result['ext_temp'] = ext_temp if ext_temp else 0.0

        room_temperature_list: list[float] = []
        for entry in [s for s in list(json_data) if "int_temp_" in s]:
            room_temperature_list.append(json_data.get(entry)) if not pd.isnull(json_data.get(entry)) else None
        int_temp: float = round(statistics.mean(room_temperature_list), 2) if len(room_temperature_list) > 0 else None
        json_result['int_temp'] = int_temp if int_temp else 0.0

        ext_humidity_list: list[int] = []
        for entry in [s for s in list(json_data) if "ext_humidity_" in s]:
            ext_humidity_list.append(json_data.get(entry)) if not pd.isnull(json_data.get(entry)) else None
        ext_humidity: float = round(statistics.mean(ext_humidity_list), 2) if len(ext_humidity_list) > 0 else None
        json_result['ext_humidity'] = ext_humidity if ext_humidity else 0

        room_humidity_list: list[int | None] = []
        for entry in [s for s in list(json_data) if "int_humidity_" in s]:
            room_humidity_list.append(json_data.get(entry)) if not pd.isnull(json_data.get(entry)) else None
        int_humidity: float = round(statistics.mean(room_humidity_list), 2) if len(room_humidity_list) > 0 else 0

        json_result['int_humidity'] = int_humidity
        json_result['ext_humidex'] = self.__get_humidex(json_result['ext_temp'], json_result['ext_humidity'])
        json_result['int_humidex'] = self.__get_humidex(json_result['int_temp'], json_result['int_humidity'])

        try:
            log.info(f'>>>>>> ext_temp:     {ext_temp:<5}\tmin: {min(ext_temperature_list):<5}\tmax: {max(ext_temperature_list):<5}\t{ext_temperature_list}')
            log.info(f'>>>>>> int_temp:     {int_temp:<5}\tmin: {min(room_temperature_list):<5}\tmax: {max(room_temperature_list):<5}\t{room_temperature_list}')
            log.info(f'>>>>>> ext_humidity: {ext_humidity:<5}\tmin: {min(ext_humidity_list):<5}\tmax: {max(ext_humidity_list):<5}\t{ext_humidity_list}')
            log.info(f'>>>>>> int_humidity: {int_humidity:<5}\tmin: {min(room_humidity_list):<5}\tmax: {max(room_humidity_list):<5}\t{room_humidity_list}')
            log.info(f'>>>>>> ext_humidex:  {json_result['ext_humidex']}')
            log.info(f'>>>>>> int_humidex:  {json_result['int_humidex']}')
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
        return json_result

    def set_kwh(self, kwh_dict: dict[str, float], df: DataFrame) -> None:
        try:
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
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    def __get_humidex(self, temp: float, humidity: int) -> int | None:
        if temp is not None and humidity is not None:
            kelvin = temp + 273
            ets = pow(10, ((-2937.4 / kelvin) - 4.9283 * math.log(kelvin) / math.log(10) + 23.5471))
            etd = ets * humidity / 100
            humidex: int = round(temp + ((etd - 10) * 5 / 9))
            if humidex < temp:
                humidex = round(temp)
            return humidex
        return None

    def start(self):
        try:
            schedule.every().day.at("00:10").do(thermopro.copy_to_cloud)
            schedule.every().day.at("06:10").do(thermopro.copy_to_cloud)
            schedule.every().day.at("12:10").do(thermopro.copy_to_cloud)
            schedule.every().day.at("18:10").do(thermopro.copy_to_cloud)

            schedule.every().hour.at(":01").do(self.__call_all)

            self.__call_all()
            thermopro.copy_to_cloud()

            while True:
                schedule.run_pending()
                sleep(1)
        except KeyboardInterrupt as ki:
            pass
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
            self.__cleanup_function()

    def __cleanup_function(self):
        try:
            log.info('ThermoProScan stopping...')
            schedule.clear()
            log.info('ThermoProScan stopped')
            sys.exit()
        except SystemExit as ex:
            pass


if __name__ == '__main__':
    thermopro.set_up(__file__)
    log.info('-------------------------------------------------------------------------------------')
    log.info('|                           ThermoProScan started                                   |')
    log.info('-------------------------------------------------------------------------------------')
    thermoProScan: ThermoProScan = ThermoProScan()
    thermoProScan.start()
    sys.exit()

    # thermoProScan.save_bkp()

    # orient = 'split'
    # file_name = f'{THERMO_PRO_SCAN_OUTPUT_JSON_FILE[:THERMO_PRO_SCAN_OUTPUT_JSON_FILE.rfind('.')]}_{orient}.json.zip'
    # df: DataFrame | None = thermopro.load_json()
    # show_df(df, title='__call_all')
    # thermopro.save_json(df)

    # df = thermopro.load_json()
    # thermopro.save_json(df)
    # thermopro.show_df(df)
