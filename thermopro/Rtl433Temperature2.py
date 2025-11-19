import ctypes
import json
import math
import os
import subprocess
import threading
import traceback
from datetime import datetime
from queue import Queue
from time import sleep
from typing import Any

import thermopro
from constants import TIMEOUT, SENSORS, RTL_433_EXE, OUTPUT_RTL_433_FILE, SENSORS_TX7B
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
            log.info(f'RTL_433_EXE alive is {alive}')
            return alive
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

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
                if completed_process.returncode == 0:
                    log.info('RTL_433_EXE killed.')
                else:
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
            if completed_process.returncode == 0:
                log.info('RTL_433_EXE started.')
            else:
                log.info(f'Return code: {completed_process.returncode}, {completed_process.stdout.replace('\n', ' ')}, {completed_process.stderr.replace('\n', ' ')}')

        except subprocess.TimeoutExpired as timeoutExpired:
            log.error(f"TimeoutExpired, returned: {timeoutExpired}")
            self.__kill_rtl_433()
            raise timeoutExpired
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
            raise ex

    def __delete_json_file(self):
        if os.path.exists(OUTPUT_RTL_433_FILE):
            try:
                os.remove(OUTPUT_RTL_433_FILE)
                log.info("OUTPUT_RTL_433_FILE deleted.")
            except Exception as ex:
                log.error(ex)
        else:
            log.warning(f'The file {OUTPUT_RTL_433_FILE} not found.')

    def __get_humidex(self, ext_temp: float, humidity: int) -> int | None:
        if ext_temp and humidity:
            kelvin = ext_temp + 273
            ets = pow(10, ((-2937.4 / kelvin) - 4.9283 * math.log(kelvin) / math.log(10) + 23.5471))
            etd = ets * humidity / 100
            humidex: int = round(ext_temp + ((etd - 10) * 5 / 9))
            if humidex < ext_temp:
                humidex = round(ext_temp)
            return humidex
        return None

    def __prepare_calls(self) -> tuple[list[str], dict[str, str]]:
        data: dict[str, list[str] | dict[str, dict[str, str]]] = dict(SENSORS)
        args: list[str] = list(data['args'])
        sensors: dict[str, dict[str, str]] = dict(data['sensors'])
        for key in sensors.keys():
            sensor: dict[str, str] = dict(sensors[key])
            args.append('-R')
            args.append(sensor['protocol'])
            sensor.pop('protocol')
            sensors[key] = sensors[key]['kind']
        return (args, sensors)

    # https://stackoverflow.com/questions/12523044/how-can-i-tail-a-log-file-in-python
    def __call_sensors(self, args: list[str], sensors: dict[str, str], json_rtl_433: dict[str, Any],
            ext_humidity_list: list[int], ext_temp_list: list[float], int_humidity_list: list[int], int_temp_list: list[float],
            threads: list[threading.Thread]):
        log.info('-------------------------- __call_sensors --------------------------')
        try:
            self.__kill_rtl_433()
            self.__delete_json_file()
            thread: threading.Thread = threading.Thread(target=self.__start_rtl_433, args=(args,))
            thread.start()
            sleep(0.5)

            if self.__find_rtl_433():
                if not os.path.exists(OUTPUT_RTL_433_FILE):
                    raise Exception(f'File not found: {OUTPUT_RTL_433_FILE}')
                with open(OUTPUT_RTL_433_FILE, 'r') as f:
                    f.seek(0, 2)
                    while len(sensors.keys()) != 0:
                        line = f.readline()
                        if not line:
                            sleep(0.1)
                            continue
                        else:
                            line = line.strip()
                            data: dict = json.loads(line)
                            model: str = data['model']
                            log.info(f'{model}, {sensors.keys()}, {model in sensors.keys()}')
                            if model in sensors.keys():
                                log.info(f'>>> data: {data}')
                                data = self.fill_dict(data, ext_humidity_list, ext_temp_list, int_humidity_list, int_temp_list, sensors[model])
                                self.warn_battery(data, threads)
                                sensors.pop(model)
                                json_rtl_433.update(data)
                if len(sensors.keys()) == 0:
                    self.__kill_rtl_433()
                    self.__delete_json_file()
            else:
                raise Exception('RTL_433 not responding')

        except subprocess.TimeoutExpired as timeoutExpired:
            log.error(timeoutExpired)
        except FileNotFoundError:
            log.error(f"Error: '{OUTPUT_RTL_433_FILE}' not found. Please ensure the file exists.")
            log.error(traceback.format_exc())
        except json.JSONDecodeError:
            log.error(f"Error: Could not decode JSON from '{OUTPUT_RTL_433_FILE}'. Check file format.")
        except Exception as e:
            log.error(f"An unexpected error occurred: {e}")
            log.error(traceback.format_exc())
        finally:
            self.__kill_rtl_433()
            self.__delete_json_file()

    def call_rtl_433(self, result_queue: Queue):
        log.info('-------------------------- call_rtl_433 --------------------------')
        json_rtl_433: dict[str, Any] = {}
        ext_humidity_list: list[int] = []
        ext_temp_list: list[float] = []
        int_humidity_list: list[int] = []
        int_temp_list: list[float] = []
        threads: list[threading.Thread] = []

        self.__call_sensors(list(SENSORS_TX7B['args']), dict(SENSORS_TX7B['sensors']), json_rtl_433, ext_humidity_list, ext_temp_list, int_humidity_list, int_temp_list, threads)
        prepare_calls: tuple[list[str], dict[str, str]] = self.__prepare_calls()
        self.__call_sensors(prepare_calls[0], prepare_calls[1], json_rtl_433, ext_humidity_list, ext_temp_list, int_humidity_list, int_temp_list, threads)

        self.get_mean('ext', ext_humidity_list, ext_temp_list, json_rtl_433)
        self.get_mean('int', int_humidity_list, int_temp_list, json_rtl_433)

        if json_rtl_433.get('ext_humidity'):
            json_rtl_433['ext_humidex'] = self.__get_humidex(json_rtl_433['ext_temp'], json_rtl_433['ext_humidity'])
        if json_rtl_433.get('int_humidity'):
            json_rtl_433['int_humidex'] = self.__get_humidex(json_rtl_433['int_temp'], json_rtl_433['int_humidity'])

        for item in ['time', 'temperature_C', 'model', 'subtype', 'id', 'channel', 'battery_ok', 'button', 'mic', 'humidity', 'status', 'flags']:
            try:
                json_rtl_433.pop(item)
            except KeyError:
                pass

        log.info(f'json_rtl_433={json_rtl_433}')

        result_queue.put(json_rtl_433)

        if len(threads) > 0:
            for thread in threads:
                thread.join(60)
            log.info("Threads stopped.")

    def warn_battery(self, data1: dict, threads: list[threading.Thread]):
        if data1.get('battery_ok') == 0 and datetime.now().strftime("%H") == '00':
            thread = threading.Thread(target=ctypes.windll.user32.MessageBoxW, args=(0, f"Sensor {data1.get('model')}'s battery is weak...", "RTL 433 Warning", 0x30))
            thread.start()
            threads.append(thread)

    def fill_dict(self, data: dict, ext_humidity_list: list[int], ext_temp_list: list[float], int_humidity_list: list[int], int_temp_list: list[float], kind: str) -> dict:
        data[f'{kind}_temp_{data['model']}'] = data['temperature_C']
        data[f'{kind}_humidity_{data['model']}'] = data['humidity'] if data.get('humidity') else None

        if kind == 'ext':
            ext_temp_list.append(data['temperature_C']) if data.get('temperature_C') else None
            ext_humidity_list.append(data['humidity']) if data.get('humidity') else None
        else:
            int_temp_list.append(data['temperature_C']) if data.get('temperature_C') else None
            int_humidity_list.append(data['humidity']) if data.get('humidity') else None
        return data

    def get_mean(self, kind: str, humidity_list: list[int], temp_list: list[float], json_rtl_433: dict[str, Any]):
        temp: float | None = None
        if len(temp_list) > 0:
            temp: float = min(temp_list)
        log.info(f'{kind}_temp={temp}, {temp_list}')
        json_rtl_433[f'{kind}_temp'] = temp

        humidity: int | None = None
        if len(humidity_list) > 0:
            humidity: int = int(sum(humidity_list) / len(humidity_list))
        log.info(f'{kind}_humidity={humidity}, {humidity_list}')
        json_rtl_433[f'{kind}_humidity'] = humidity


if __name__ == "__main__":
    thermopro.set_up(__file__)
    result_queue: Queue = Queue()
    testJson: Rtl433Temperature2 = Rtl433Temperature2()
    testJson.call_rtl_433(result_queue)
    # testJson.call_rtl_433(result_queue)

    while not result_queue.empty():
        print(thermopro.ppretty(result_queue.get()))
