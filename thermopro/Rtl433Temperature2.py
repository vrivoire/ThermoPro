import ctypes
import json
import os
import subprocess
import threading
import traceback
from datetime import datetime
from queue import Queue
from time import sleep
from typing import Any

import thermopro
from constants import TIMEOUT, OUTPUT_RTL_433_FILE, SENSORS, RTL_433_EXE
from thermopro import log


# rtl_433_64bit_static.exe -R 02 -R 162 -R 245 -f 433M -f 915M
class Rtl433Temperature2:

    def __init__(self):
        log.info('       ----------------------- Start Rtl433Temperature2 -----------------------')

    def call_rtl_433(self, result_queue: Queue):
        log.info('-------------------------- call_rtl_433 --------------------------')
        json_rtl_433: dict[str, int | float] = {}
        ext_humidity_list: list[int] = []
        ext_temp_list: list[float] = []
        int_humidity_list: list[int] = []
        int_temp_list: list[float] = []
        threads: list[threading.Thread] = []
        sensors_list: dict[str, str] = {}

        try:
            self.__kill_rtl_433()
            self.__delete_json_file()

            for freq in SENSORS:
                sensors_list.update(SENSORS[freq]['sensors'])
                self.__call_sensors(list(SENSORS[freq]['args']), dict(SENSORS[freq]['sensors']), json_rtl_433, ext_humidity_list, ext_temp_list, int_humidity_list, int_temp_list, threads)

            for item in ['time', 'temperature_C', 'model', 'subtype', 'id', 'channel', 'battery_ok', 'button', 'mic', 'humidity', 'status', 'flags', 'data']:
                try:
                    json_rtl_433.pop(item)
                except KeyError:
                    pass

            for sens in sorted(sensors_list):
                log.info(f'>>>>>> {sensors_list[sens]} {sens}: {json_rtl_433.get(sensors_list[sens] + '_temp_' + sens)}°C, {json_rtl_433.get(sensors_list[sens] + '_humidity_' + sens)}%')

        except Exception as e:
            log.error(f"An unexpected error occurred: {e}")
            log.error(traceback.format_exc())

        self.__kill_rtl_433()
        self.__delete_json_file()

        result_queue.put({'sensors': json_rtl_433})

        if len(threads) > 0:
            for thread in threads:
                thread.join(60)
            log.info("Threads stopped.")

    def __call_sensors(self, args: list[str | int], sensors: dict[str, str], json_rtl_433: dict[str, Any],
            ext_humidity_list: list[int], ext_temp_list: list[float], int_humidity_list: list[int], int_temp_list: list[float],
            threads: list[threading.Thread]):
        log.info('-------------------------- __call_sensors --------------------------')
        log.info(f'args: {args}')
        log.info(f'sensors: {sensors}')
        try:
            self.__kill_rtl_433()
            self.__delete_json_file()

            thread: threading.Thread = threading.Thread(target=self.__start_rtl_433, args=(args,))
            thread.start()

            i: int = 0
            while not os.path.exists(OUTPUT_RTL_433_FILE) and i < 1000:
                i += 1
                sleep(0.2)
            if not os.path.exists(OUTPUT_RTL_433_FILE):
                raise Exception(f'File not found: {OUTPUT_RTL_433_FILE} and is_rtl_433_alive: {self.__is_rtl_433_alive()} and i: {i}')
            log.info(f"Found file {OUTPUT_RTL_433_FILE} and is_rtl_433_alive: {self.__is_rtl_433_alive()} and i: {i}")

            with open(OUTPUT_RTL_433_FILE, 'r') as f:
                f.seek(0, 2)
                while len(sensors.keys()) != 0 and self.__is_rtl_433_alive():
                    line = f.readline()
                    if not line:
                        sleep(0.1)
                        continue
                    else:
                        data: dict = json.loads(line.strip())
                        model: str = data['model']
                        log.info(f'{model}, {list(sensors.keys())}')
                        if model in sensors.keys():
                            log.info(f'>>>>>> {data.get('model')}: {data}')
                            data = self.__fill_dict(data, ext_humidity_list, ext_temp_list, int_humidity_list, int_temp_list, sensors[model])
                            self.__warn_battery(data, threads)
                            sensors.pop(model)
                            log.info(f'Removed: {model}')
                            json_rtl_433.update(data)
                    if len(sensors.keys()) == 0 or not self.__is_rtl_433_alive():
                        log.info(f'Done! keys: {list(sensors.keys())}, is alive: {self.__is_rtl_433_alive()}')
                        break

            self.__warn_not_respondig(sensors)

        except Exception as e:
            log.error(f"An unexpected error occurred: {e}")
            log.error(traceback.format_exc())
        finally:
            self.__kill_rtl_433()
            self.__delete_json_file()

    def __is_rtl_433_alive(self) -> bool | None:
        try:
            completed_process = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {RTL_433_EXE}', '/FO', 'csv', '/nh'],
                capture_output=True,
                timeout=10,
                check=False,
                shell=True,
                text=True
            )
            return RTL_433_EXE in completed_process.stdout
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    def __kill_rtl_433(self) -> None:
        try:
            if self.__is_rtl_433_alive():
                completed_process = subprocess.run(
                    ['taskkill', '/F', '/T', '/IM', RTL_433_EXE],
                    capture_output=True,
                    timeout=10,
                    check=False,
                    shell=True,
                    text=True
                )
                if completed_process.returncode == 0:
                    log.info(f'{RTL_433_EXE} killed.')
                else:
                    log.warning(f'Return code: {completed_process.returncode}, stdout: {completed_process.stdout.replace('\n', ' ')}, stderr: {completed_process.stderr.replace('\n', ' ')}')
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    def __start_rtl_433(self, args: list[str]) -> str | None:
        try:
            log.info(f'ARGS={args}')
            completed_process = subprocess.run(
                args,
                capture_output=True,
                timeout=TIMEOUT + 5,
                encoding="utf-8",
                check=False,
                shell=True,
                text=True
            )
            if completed_process.returncode == 0:
                log.info(f'{RTL_433_EXE} stopped.')
            else:
                log.warning(f'{RTL_433_EXE} return code: {completed_process.returncode}, {completed_process.stdout.replace('\n', ' ')}, {completed_process.stderr.replace('\n', ' ')}')

        except subprocess.TimeoutExpired as timeoutExpired:
            log.error(f"TimeoutExpired, returned: {timeoutExpired}")
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    def __delete_json_file(self):
        if os.path.exists(OUTPUT_RTL_433_FILE):
            try:
                os.remove(OUTPUT_RTL_433_FILE)
                log.info(f"File {OUTPUT_RTL_433_FILE} deleted.")
            except Exception as ex:
                log.error(ex)

    def __warn_not_respondig(self, sensors: dict[str, str]):
        if len(sensors) > 0:
            string: str = ' RTL 433 Warning '.center(80, '*')
            log.error(string)
            log.error('*' + f'Sensor{'s' if len(sensors) > 1 else ''} {list(sensors)} NOT responding'.center(len(string) - 2) + '*')
            log.error(string)

    def __warn_battery(self, data: dict, threads: list[threading.Thread]):
        if data.get('battery_ok') == 0:
            string: str = ' RTL 433 Warning '.center(80, '*')
            log.error(string)
            log.error('*' + f"Sensor {data.get('model')} battery is weak...".center(len(string) - 2) + '*')
            log.error(string)
            if datetime.now().strftime("%H") == '00':
                thread = threading.Thread(target=ctypes.windll.user32.MessageBoxW, args=(0, f"Sensor {data.get('model')}'s battery is weak...", "RTL 433 Warning", 0x30))
                thread.start()
                threads.append(thread)

    def __fill_dict(self, data: dict, ext_humidity_list: list[int], ext_temp_list: list[float], int_humidity_list: list[int], int_temp_list: list[float], kind: str) -> dict:
        # try:
        #     print(f'data={data['data']} --> {int(data['data'], 16)}') if data.get('data') is not None else None
        #     print(f'--> {datetime.fromtimestamp(int(data['data'], 16))}') if data.get('data') is not None else None
        # except OSError as ex:
        #     log.error(ex)
        #     log.error(traceback.format_exc())

        data[f'{kind}_temp_{data['model']}'] = round(data['temperature_C'], 2)
        data[f'{kind}_humidity_{data['model']}'] = int(data['humidity']) if data.get('humidity') else None

        if kind == 'ext':
            ext_temp_list.append(data['temperature_C']) if data.get('temperature_C') is not None else None
            ext_humidity_list.append(data['humidity']) if data.get('humidity') is not None else None
        else:
            int_temp_list.append(data['temperature_C']) if data.get('temperature_C') is not None else None
            int_humidity_list.append(data['humidity']) if data.get('humidity') is not None else None

        return data


if __name__ == "__main__":
    thermopro.set_up(__file__)
    result_queue: Queue = Queue()
    rtl433Temperature2: Rtl433Temperature2 = Rtl433Temperature2()
    rtl433Temperature2.call_rtl_433(result_queue)

    json_data: dict[str, int | float] = {}
    while not result_queue.empty():
        json_data = result_queue.get()
        print(thermopro.ppretty(json_data))

    # sensors: dict[str, str] = {}
    # for sensor in SENSORS:
    #     sensors.update(SENSORS[sensor]['sensors'])
    # for sensor in sorted(sensors):
    #     print(f'{sensors[sensor]} {sensor}: {json_data['sensors'][sensors[sensor] + '_temp_' + sensor]}°C, {json_data['sensors'][sensors[sensor] + '_humidity_' + sensor]}%')
