import json
import math
import os
import subprocess
import threading
import traceback
from queue import Queue
from time import sleep
from typing import Any

import thermopro
from constants import TIMEOUT, SENSORS, RTL_433_EXE, OUTPUT_RTL_433_FILE
from thermopro import log


# rtl_433_64bit_static.exe -R 02 -R 162 -R 245 -f 433M -f 915M
class Rtl433Temperature2:

    def __init__(self):
        log.info('       ----------------------- Start Rtl433Temperature2 -----------------------')

    def __find_rtl_433(self) -> bool:
        alive: bool = False
        try:
            exe = RTL_433_EXE[RTL_433_EXE.rfind('/') + 1:]
            args = ['tasklist', '/FI', f'IMAGENAME eq {exe}', '/FO', 'csv', '/nh']
            completed_process = subprocess.run(
                args,
                capture_output=True,
                timeout=10,
                check=False,
                shell=True,
                text=True
            )
            # log.debug(f'Return code: {completed_process.returncode}, stdout: {completed_process.stdout}, stderr: {completed_process.stderr}')
            alive = exe in completed_process.stdout
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

        # log.info(f'rtl_433 alive is {alive}')
        return alive

    def __kill_rtl_433(self) -> None:
        exe = RTL_433_EXE[RTL_433_EXE.rfind('/') + 1:]
        try:
            if self.__find_rtl_433():
                completed_process = subprocess.run(
                    ['taskkill', '/F', '/T', '/IM', exe],
                    capture_output=True,
                    timeout=10,
                    check=False,
                    shell=True,
                    text=True
                )
                log.info(f'Return code: {completed_process.returncode}, stdout: {completed_process.stdout.replace('\n', ' ')}, stderr: {completed_process.stderr.replace('\n', ' ')}')
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    def __start_rtl_433(self, args: list[str]):
        try:
            log.info(f'ARGS={args}')
            completed_process = subprocess.run(
                args,
                capture_output=True,
                timeout=TIMEOUT,
                encoding="utf-8",
                check=False,
                shell=True,
                text=True
            )
            log.info(f'Return code: {completed_process.returncode}, {completed_process.stdout.replace('\n', ' ')}, {completed_process.stderr.replace('\n', ' ')}')

        except subprocess.TimeoutExpired as timeoutExpired:
            log.error(f"TimeoutExpired, returned: {timeoutExpired}")
            self.__kill_rtl_433()

    def __delete_json_file(self):
        if os.path.exists(OUTPUT_RTL_433_FILE):
            try:
                os.remove(OUTPUT_RTL_433_FILE)
            except Exception as ex:
                log.error(ex)

    def __get_humidex(self, ext_temp: float, humidity: int) -> int | None:
        kelvin = ext_temp + 273
        ets = pow(10, ((-2937.4 / kelvin) - 4.9283 * math.log(kelvin) / math.log(10) + 23.5471))
        etd = ets * humidity / 100
        humidex: int = round(ext_temp + ((etd - 10) * 5 / 9))
        if humidex < ext_temp:
            humidex = round(ext_temp)
        return humidex

    def __prepare_call(self) -> list[list[list[str]]]:
        sensors: list[dict[str, list[str] | dict[str, dict[str, str]]]] = list(SENSORS)
        array: list[list[list[str]]] = []
        for sensor in sensors:
            args: list[str] = sensor['args']
            name_list: list[str] = []

            for name in sensor['sensors']:
                # print(f'{name}: {sensor['sensors'][name]['protocol']}')
                name_list.append(name)
                args.append('-R')
                args.append(sensor['sensors'][name]['protocol'])
            array.append([name_list, args])
        log.info(f'sensors: {array}')
        return array

    def call_rtl_433(self, result_queue: Queue):
        json_rtl_433: dict[str, Any] = {}
        humidity_list: list[int] = []
        ext_temp_list: list[float] = []

        prepare_call: list[list[list[str]]] = self.__prepare_call()
        for toto in prepare_call:
            sensors_list: list[str] = toto[0]
            args: list[str] = toto[1]

            self.__kill_rtl_433()
            self.__delete_json_file()

            thread: threading.Thread = threading.Thread(target=self.__start_rtl_433, args=(args,))
            thread.start()
            sleep(2)
            try:
                old_file_size_bytes = 0
                while self.__find_rtl_433():
                    file_size_bytes = os.path.getsize(OUTPUT_RTL_433_FILE)
                    if file_size_bytes != old_file_size_bytes:
                        lines: list[dict] = []
                        with open(OUTPUT_RTL_433_FILE, 'r') as file:
                            while True:
                                line: str = file.readline().strip()
                                if len(line) == 0:
                                    break
                                data: dict = json.loads(line)
                                lines.append(data)
                                old_file_size_bytes = file_size_bytes

                        for data in lines:
                            if data['model'] in sensors_list:
                                log.info(f'data={data}')
                                data[f'ext_temp_{data['model']}'] = data['temperature_C']
                                data[f'ext_humidity_{data['model']}'] = data['humidity'] if data.get('humidity') else None
                                ext_temp_list.append(data['temperature_C'])
                                humidity_list.append(data['humidity']) if data.get('humidity') else None

                                try:
                                    sensors_list.remove(data['model'])
                                except KeyError:
                                    pass

                                for item in ['time', 'temperature_C', 'model', 'subtype', 'id', 'channel', 'battery_ok', 'button', 'mic', 'humidity']:
                                    try:
                                        del data[item]
                                    except KeyError:
                                        pass

                                json_rtl_433.update(data)

                        if len(sensors_list) == 0:
                            break
                        sleep(1)
            except subprocess.TimeoutExpired as timeoutExpired:
                log.error(timeoutExpired)
            except FileNotFoundError:
                log.error(f"Error: '{OUTPUT_RTL_433_FILE}' not found. Please ensure the file exists.")
            except json.JSONDecodeError:
                log.error(f"Error: Could not decode JSON from '{OUTPUT_RTL_433_FILE}'. Check file format.")
            except Exception as e:
                log.error(f"An unexpected error occurred: {e}")
                log.error(traceback.format_exc())

        self.__kill_rtl_433()
        self.__delete_json_file()

        for s in prepare_call[0][0]:
            json_rtl_433[f'ext_temp_{s}'] = None
            json_rtl_433[f'ext_humidity_{s}'] = None

        ext_temp: float | None = None
        if len(ext_temp_list) > 0:
            ext_temp: float = min(ext_temp_list)
        log.info(f'ext_temp={ext_temp}, {ext_temp_list}')
        json_rtl_433['ext_temp'] = ext_temp

        humidity: int | None = None
        if len(humidity_list) > 0:
            humidity: int = int(sum(humidity_list) / len(humidity_list))
        log.info(f'ext_humidity={humidity}, {humidity_list}')
        json_rtl_433['ext_humidity'] = humidity

        if json_rtl_433.get('ext_humidity'):
            json_rtl_433['ext_humidex'] = self.__get_humidex(json_rtl_433['ext_temp'], json_rtl_433['ext_humidity'])
        log.info(f'json_rtl_433={json_rtl_433}')
        result_queue.put(json_rtl_433)


if __name__ == "__main__":
    thermopro.set_up(__file__)
    result_queue: Queue = Queue()
    testJson: Rtl433Temperature2 = Rtl433Temperature2()
    testJson.call_rtl_433(result_queue)

    while not result_queue.empty():
        print(result_queue.get())
