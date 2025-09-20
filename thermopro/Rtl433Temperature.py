import json
import math
import subprocess
import threading
import traceback
from queue import Queue
from time import sleep
from typing import Any

import requests

import thermopro
from thermopro import log


class Rtl433Temperature:

    def __init__(self):
        log.info('Rtl433Temperature started')

    def __ping(self):
        from thermopro.ThermoProScan import ThermoProScan
        try:
            command = ['ping', '-4', '-n', '1', f'{ThermoProScan.HTTP_HOST}']
            completed_process = subprocess.run(command, text=True, capture_output=True)
            if "100%" in completed_process.stdout:
                log.info(f"{ThermoProScan.HTTP_HOST} is unreachable.")
                return False
            else:
                log.info(f"{ThermoProScan.HTTP_HOST} is reachable.")
                return True

        except subprocess.CalledProcessError as e:
            log.error(f"Error executing ping command: {e}")
        except FileNotFoundError:
            log.error("Ping command not found. Ensure it's in your system's PATH.")
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
        return False

    def __find_rtl_433(self) -> bool:
        from thermopro.ThermoProScan import ThermoProScan
        try:
            exe = ThermoProScan.RTL_433_EXE[ThermoProScan.RTL_433_EXE.rfind('/') + 1:]
            args = ['tasklist', '/FI', f'IMAGENAME eq {exe}', '/FO', 'csv', '/nh']
            completed_process = subprocess.run(
                args,
                capture_output=True,
                timeout=10,
                check=False,
                shell=True,
                text=True
            )
            log.debug(f'Return code: {completed_process.returncode}, stdout: {completed_process.stdout}, stderr: {completed_process.stderr}')
            return exe in completed_process.stdout
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
        return False

    def __kill_rtl_433(self) -> None:
        from thermopro.ThermoProScan import ThermoProScan
        exe = ThermoProScan.RTL_433_EXE[ThermoProScan.RTL_433_EXE.rfind('/') + 1:]
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
                log.info(f'Return code: {completed_process.returncode}, stdout: {completed_process.stdout}, stderr: {completed_process.stderr}')
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

    def __get_humidex(self, temp_ext: float, humidity: int) -> int | None:
        kelvin = temp_ext + 273
        ets = pow(10, ((-2937.4 / kelvin) - 4.9283 * math.log(kelvin) / math.log(10) + 23.5471))
        etd = ets * humidity / 100
        humidex: int = round(temp_ext + ((etd - 10) * 5 / 9))
        if humidex < temp_ext:
            humidex = round(temp_ext)
        return humidex

    def __stream_lines(self):
        from thermopro.ThermoProScan import ThermoProScan
        url = f'http://{ThermoProScan.HTTP_HOST}:{ThermoProScan.HTTP_PORT}/stream'
        headers = {'Accept': 'application/json'}

        response: requests.models.Response = requests.models.Response()
        response.status_code = 500
        while response.status_code != 200:
            response = requests.get(url, headers=headers, timeout=70, stream=True)
            log.info(f'Connected {response.status_code} to {url}')

        for chunk in response.iter_lines(chunk_size=64):
            yield chunk

    def __start_rtl_433(self):
        from thermopro.ThermoProScan import ThermoProScan
        args = [ThermoProScan.RTL_433_EXE, '-F', f'http:{ThermoProScan.HTTP_HOST}:{ThermoProScan.HTTP_PORT}', '-T', f'{ThermoProScan.TIMEOUT}', '-R', '02', '-R', '162']
        try:
            log.info(f'ARGS={args}')
            completed_process = subprocess.run(
                args,
                capture_output=True,
                timeout=ThermoProScan.TIMEOUT,
                encoding="utf-8",
                check=False,
                shell=True,
                text=True
            )
            log.info(f'Return code: {completed_process.returncode}, {completed_process.stdout}, {completed_process.stderr}')

        except subprocess.TimeoutExpired as timeoutExpired:
            log.error(f"TimeoutExpired, returned: {timeoutExpired}")
        #     # log.error(traceback.format_exc())
        #     # raise timeoutExpired
        #
        # except subprocess.CalledProcessError as calledProcessError:
        #     log.error(f"CalledProcessError, returned {calledProcessError.returncode}\n{calledProcessError}")
        #     log.error(traceback.format_exc())
        #
        # except subprocess.SubprocessError as subprocessError:
        #     log.error(f"SubprocessError, returned \n{subprocessError}")
        #     log.error(traceback.format_exc())
        #
        # except Exception as exception:
        #     log.error(exception)
        #     log.error(traceback.format_exc())

    def call_rtl_433(self, result_queue: Queue):
        json_rtl_433: dict[str, Any] = {}
        humidity_list: list[int] = []
        temp_ext_list: list[float] = []
        temp_ext: float | None = None
        humidity: int | None = None
        sensors: dict[str, str] = {'Thermopro-TX2': '162', 'Rubicson-Temperature': '02'}
        try:
            while not self.__ping():
                log.info(f'Ping RTL-433: {self.__ping()}')
            self.__kill_rtl_433()
            thread: threading.Thread = threading.Thread(target=self.__start_rtl_433)
            thread.start()
            sleep(5)

            log.info(f'RTL-433 started: {self.__find_rtl_433()}')

            stop: bool = False

            while not stop:
                for chunk in self.__stream_lines():
                    chunk = chunk.rstrip()
                    if not chunk:
                        continue
                    data = json.loads(chunk)
                    log.info(f'data={data}')

                    if sensors.get(data['model']):
                        data['temp_ext'] = data['temperature_C']
                        data[f'sensor_{sensors[data['model']]}'] = data['temp_ext']
                        temp_ext_list.append(data['temp_ext'])
                        humidity_list.append(data['humidity']) if data.get('humidity') else None

                        try:
                            del sensors[data['model']]
                        except KeyError as ke:
                            pass

                        for item in ['temperature_C', 'model', 'subtype', 'id', 'channel', 'battery_ok', 'button', 'mic']:
                            try:
                                del data[item]
                            except KeyError as ex:
                                pass

                        json_rtl_433.update(data)

                        if len(sensors) == 0:
                            stop = True
                            break

        except requests.ConnectionError as connectionError:
            log.error(connectionError)

        except subprocess.TimeoutExpired as timeoutExpired:
            log.error(timeoutExpired)

        except Exception as exception:
            log.error(exception)
            log.error(traceback.format_exc())

        finally:
            self.__kill_rtl_433()
            if len(temp_ext_list) > 0:
                temp_ext: float = min(temp_ext_list)
            log.info(f'temp_ext={temp_ext}, {temp_ext_list}')
            json_rtl_433['temp_ext'] = temp_ext

            if len(humidity_list) > 0:
                humidity: int = int(sum(humidity_list) / len(humidity_list))
            log.info(f'humidity={humidity}, {humidity_list}')
            json_rtl_433['humidity'] = humidity

            if json_rtl_433.get('humidity'):
                json_rtl_433['humidex'] = self.__get_humidex(json_rtl_433['temp_ext'], json_rtl_433['humidity'])
            log.info(f'json_rtl_433={json_rtl_433}')
            result_queue.put(json_rtl_433)


if __name__ == "__main__":
    from thermopro.ThermoProScan import ThermoProScan

    thermopro.set_up(__file__)
    result_queue: Queue = Queue()
    toto: Rtl433Temperature = Rtl433Temperature()
    toto.call_rtl_433(result_queue)

    while not result_queue.empty():
        print(result_queue.get())
