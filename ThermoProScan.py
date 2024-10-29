# pyinstaller --onefile ThermoProScan.py --icon=ThermoPro.jpg --nowindowed --noconsole

from datetime import datetime
import csv
import json
import logging as log
import logging.handlers
import os
import schedule
import subprocess
import sys
import time
import traceback


class ThermoProScan:
    HOME_PATH = "C:/Users/rivoi/"
    PATH = f"{HOME_PATH}GoogleDrive/PoidsPression/"
    OUTPUT_JSON_FILE = f"{PATH}ThermoProScan.json"
    OUTPUT_CSV_FILE = f"{PATH}ThermoProScan.csv"
    LOG_PATH = f"{PATH}ThermoProScan.log"
    RTL_433_VERSION = '23.11'
    RTL_433_EXE = f'{HOME_PATH}Documents/NetBeansProjects/rtl_433-win-x64-{RTL_433_VERSION}/rtl_433_64bit_static.exe'
    SCHEDULE_DELAY = '60'
    ARGS = [RTL_433_EXE, '-T', SCHEDULE_DELAY, '-R', '162', '-F', f'json:{OUTPUT_JSON_FILE}']

    log.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] [%(lineno)d] %(message)s",
        handlers=[
            logging.handlers.TimedRotatingFileHandler(LOG_PATH, when='midnight', interval=1, backupCount=7, encoding=None, delay=False, utc=False, atTime=None, errors=None),
            logging.StreamHandler()
        ]
    )

    @staticmethod
    def call_rtl_433() -> None:
        log.info("Start call_rtl_433")
        try:
            if os.path.isfile(ThermoProScan.OUTPUT_JSON_FILE):
                os.remove(ThermoProScan.OUTPUT_JSON_FILE)

            completed_process = subprocess.run(
                ThermoProScan.ARGS,
                capture_output=True,
                timeout=70,
                encoding="utf-8",
                check=False,
                shell=True
            )
            log.info(f'ARGS: {completed_process.args}')
            log.info(f'Return code: {completed_process.returncode}')
            log.info(f'stdout: {completed_process.stdout}')
            log.info(f'stderr: {completed_process.stderr}')

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
    def load_json() -> dict[str, any]:
        log.info("load_json")

        json_data: dict[str, any] = {}
        log.info(f'Loading file {ThermoProScan.OUTPUT_JSON_FILE}')

        if os.path.isfile(ThermoProScan.OUTPUT_JSON_FILE) and os.stat(ThermoProScan.OUTPUT_JSON_FILE).st_size > 0:
            with open(ThermoProScan.OUTPUT_JSON_FILE, 'r') as file:
                json_str = file.read()
            json_str = json_str.splitlines()[0]
            json_data = json.loads(json_str)
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
        json_data: dict[str, any] = ThermoProScan.load_json()
        log.info(json_data)
        if bool(json_data):
            is_new_file = False if (os.path.isfile(ThermoProScan.OUTPUT_CSV_FILE) and os.stat(ThermoProScan.OUTPUT_CSV_FILE).st_size > 0) else True
            with open(ThermoProScan.OUTPUT_CSV_FILE, "a", newline='') as csvfile:
                writer = csv.writer(csvfile)
                if is_new_file:
                    writer.writerow(["time", "temperature_C", "humidity"])
                writer.writerow([json_data["time"], json_data["temperature_C"], json_data["humidity"]])

            if not is_new_file:
                with open(ThermoProScan.OUTPUT_CSV_FILE, 'r') as r, open(ThermoProScan.OUTPUT_CSV_FILE + '.tmp', 'w') as o:
                    for line in r:
                        line = line.strip()
                        if len(line) > 0:
                            o.write(line.strip() + '\n')
                os.remove(ThermoProScan.OUTPUT_CSV_FILE)
                os.rename(ThermoProScan.OUTPUT_CSV_FILE + '.tmp', ThermoProScan.OUTPUT_CSV_FILE)
                os.remove(ThermoProScan.OUTPUT_JSON_FILE)
        else:
            log.error('json_data empty')

        log.info("End task")

    @staticmethod
    def start(self):
        log.info('ThermoProScan started')
        # self.call_all(self)
        schedule.every().hour.at(":00").do(self.call_all)
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt as ki:
            log.error(f'{ki}')
            log.error(traceback.format_exc())

        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())

        thermoProScan.stop()


    @staticmethod
    def stop():
        log.info('ThermoProScan stopped')
        schedule.clear()
        sys.exit()

if __name__ == '__main__':
    thermoProScan: ThermoProScan = ThermoProScan()
    thermoProScan.start(thermoProScan)
