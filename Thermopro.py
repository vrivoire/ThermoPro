# pyinstaller --onefile Thermopro.py --icon=Thermoro.jpg --nowindowed --noconsole

import logging as log
import logging.handlers
import subprocess
import os
import sys
import schedule
import time
from datetime import datetime
import json
import csv

RTL_433_VERSION = '23.11'
RTL_433_EXE = f'C:/Users/rivoi/Documents/NetBeansProjects/rtl_433-win-x64-{RTL_433_VERSION}/rtl_433_64bit_static.exe'
PATH = "C:/Users/rivoi/GoogleDrive/PoidsPression/"
OUTPUT_JSON_FILE = f"{PATH}ThermoPro.json"
OUTPUT_CSV_FILE = f"{PATH}ThermoPro.csv"
ARGS = [RTL_433_EXE, '-T', '60', '-R', '162', '-F', f'json:{OUTPUT_JSON_FILE}']
SCHEDULE_DELAY = 60

log.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.handlers.TimedRotatingFileHandler(f'{PATH}ThermoPro.log', when='midnight', interval=1, backupCount=7, encoding=None, delay=False, utc=False, atTime=None, errors=None),
        logging.StreamHandler()
    ]
)


def call_rtl_433():
    log.info(f"Executing call_rtl_433 at {datetime.now()}")
    try:
        if os.path.isfile(OUTPUT_JSON_FILE):
            os.remove(OUTPUT_JSON_FILE)

        completed_process = subprocess.run(
            ARGS,
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
    except subprocess.CalledProcessError as calledProcessError:
        log.error(f"CalledProcessError, returned {calledProcessError.returncode}\n{calledProcessError}")
    except subprocess.SubprocessError as subprocessError:
        log.error(f"SubprocessError, returned \n{subprocessError}")
    except Exception as ex:
        log.error(f'ERROR \n{ex}')


def load_json() -> dict[str, any]:
    json_data: dict[str, any] = {}
    log.info(f'Loading file {OUTPUT_JSON_FILE}')

    if os.path.isfile(OUTPUT_JSON_FILE) and os.stat(OUTPUT_JSON_FILE).st_size > 0:
        with open(OUTPUT_JSON_FILE, 'r') as file:
            json_str = file.read()
        json_str = json_str.splitlines()[0]
        json_data = json.loads(json_str)
        json_data['time'] = datetime.strptime(json_data['time'], '%Y-%m-%d %H:%M:%S')
    else:
        log.error(f'File {OUTPUT_JSON_FILE} not existing or empty.')

    return json_data


def call_all():
    log.info('\n\n--------------------------------------------------------------------------------')
    call_rtl_433()
    json_data: dict[str, any] = load_json()
    log.info(json_data)
    if bool(json_data):
        is_new_file = False if (os.path.isfile(OUTPUT_CSV_FILE) and os.stat(OUTPUT_CSV_FILE).st_size > 0) else True
        with open(OUTPUT_CSV_FILE, "a", newline='') as csvfile:
            writer = csv.writer(csvfile)
            if is_new_file:
                writer.writerow(["time", "temperature_C", "humidity"])
            writer.writerow([json_data["time"], json_data["temperature_C"], json_data["humidity"]])

        if not is_new_file:
            with open(OUTPUT_CSV_FILE, 'r') as r, open(OUTPUT_CSV_FILE + '.tmp', 'w') as o:
                for line in r:
                    line = line.strip()
                    if len(line) > 0:
                        o.write(line.strip() + '\n')
            os.remove(OUTPUT_CSV_FILE)
            os.rename(OUTPUT_CSV_FILE + '.tmp', OUTPUT_CSV_FILE)
            os.remove(OUTPUT_JSON_FILE)
    else:
        log.error('json_data empty')

    log.info(f"End task {datetime.now()}")


if __name__ == '__main__':
    log.info('ThermoPro started')
    schedule.every().hour.at(":00").do(call_all)
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt as ki:
        log.error(f'KeyboardInterrupt \n{ki}')
    except Exception as ex:
        log.error(f'ERROR \n{ex}')

    schedule.clear()
    log.info('ThermoPro stopped')
    sys.exit()
