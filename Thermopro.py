# pyinstaller --onefile Thermopro.py --icon=Thermopro.jpg --nowindowed --noconsole

import subprocess
import os
import schedule
import time
from datetime import datetime
import json
import csv

RTL_433_VERSION = '23.11'
RTL_433_EXE = f'C:/Users/rivoi/Documents/NetBeansProjects/rtl_433-win-x64-{RTL_433_VERSION}/rtl_433_64bit_static.exe'
OUTPUT_JSON_FILE = "C:/Users/rivoi/GoogleDrive/PoidsPression/ThermoPro.json"
OUTPUT_CSV_FILE = "C:/Users/rivoi/GoogleDrive/PoidsPression/ThermoPro.csv"
ARGS = [RTL_433_EXE, '-T', '60', '-R', '162', '-F', f'json:{OUTPUT_JSON_FILE}']
SCHEDULE_DELAY = 60


def call_rtl_433():
    print(f"Executing call_rtl_433 at {datetime.now()}")
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
        print(f'ARGS: {completed_process.args}')
        print(f'Return code: {completed_process.returncode}')
        print(f'stdout: {completed_process.stdout}')
        print(f'stderr: {completed_process.stderr}')

    except subprocess.TimeoutExpired as timeoutExpired:
        print(f"TimeoutExpired, returned \n{timeoutExpired}")
    except subprocess.CalledProcessError as calledProcessError:
        print(f"CalledProcessError, returned {calledProcessError.returncode}\n{calledProcessError}")
    except subprocess.SubprocessError as subprocessError:
        print(f"SubprocessError, returned \n{subprocessError}")
    except Exception as ex:
        print(f'ERROR \n{ex}')


def load_json() -> dict[str, any]:
    json_data: dict[str, any]

    print(f'Loading file {OUTPUT_JSON_FILE}')

    if os.path.isfile(OUTPUT_JSON_FILE) and os.stat(OUTPUT_JSON_FILE).st_size > 0:
        with open(OUTPUT_JSON_FILE, 'r') as file:
            json_str = file.read()
        json_str = json_str.splitlines()[0]
        json_data = json.loads(json_str)
        print(json_data['time'])
        json_data['time'] = datetime.strptime(json_data['time'], '%Y-%m-%d %H:%M:%S')
    else:
        print(f'File {OUTPUT_JSON_FILE} not existing or empty.')
    return json_data


def call_all() -> object:
    call_rtl_433()
    json_data: dict[str, any] = load_json()
    print(json_data)

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


if __name__ == '__main__':
    schedule.every(SCHEDULE_DELAY).minutes.do(call_all)
    while True:
        schedule.run_pending()
        time.sleep(1)
