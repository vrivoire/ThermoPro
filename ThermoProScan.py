# pyinstaller --onefile ThermoProScan.py --icon=ThermoPro.jpg --nowindowed --noconsole

# https://github.com/merbanan/rtl_433

import csv
import ctypes
import json
import logging as log
import logging.handlers
import os
import os.path
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import schedule


class ThermoProScan:
    HOME_PATH = "C:/Users/rivoi/"
    PATH = f"{HOME_PATH}GoogleDrive/PoidsPression/"
    OUTPUT_JSON_FILE = f"{PATH}ThermoProScan.json"
    OUTPUT_CSV_FILE = f"{PATH}ThermoProScan.csv"

    RTL_433_VERSION = '24.10'
    RTL_433_EXE = f'{HOME_PATH}Documents/NetBeansProjects/rtl_433-win-x64-{RTL_433_VERSION}/rtl_433_64bit_static.exe'
    SCHEDULE_DELAY = '60'
    ARGS = [RTL_433_EXE, '-T', SCHEDULE_DELAY, '-R', '162', '-F', f'json:{OUTPUT_JSON_FILE}']
    DAYS = 7

    LOG_PATH = f"{PATH}logs/"
    LOG_FILE = f'{LOG_PATH}ThermoProScan.log'

    def namer(name: str) -> str:
        return name.replace(".log", "") + ".log"

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)
    fileHandler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='midnight', interval=1, backupCount=7, encoding=None, delay=False, utc=False, atTime=None, errors=None)
    fileHandler.namer = namer
    log.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-8s] [%(filename)s.%(funcName)s:%(lineno)d] %(message)s",
        handlers=[
            fileHandler,
            logging.StreamHandler()
        ]
    )

    @staticmethod
    def load_csv() -> list[dict]:
        log.info('load_csv')
        if os.path.isfile(ThermoProScan.OUTPUT_CSV_FILE):
            result = pd.read_csv(ThermoProScan.OUTPUT_CSV_FILE)
            result = result.astype({'time': 'datetime64[ns]'})
            result = result.astype({'temperature': 'float'})
            return result.to_dict('records')
        return []

    @staticmethod
    def create_graph(popup: bool) -> None:
        log.info('create_graph')
        csv_data = ThermoProScan.load_csv()
        if bool(csv_data):
            sortedDatas = sorted(csv_data, key=lambda d: d["time"])
            df = pd.DataFrame(sortedDatas)
            df.set_index('time')
            log.info(f'\n{df}')

            fig, ax1 = plt.subplots()
            ax1.set_ylabel('Humidity %', color='xkcd:royal blue')  # we already handled the x-label with ax1
            ax1.plot(df["time"], df["humidity"], color='xkcd:royal blue')
            ax1.grid(axis='y', color='blue', linewidth=0.2)
            ax1.plot(df["time"], df.rolling(window=f'{ThermoProScan.DAYS}D', on='time')['humidity'].mean(), color='xkcd:deep blue', alpha=0.3)
            ax1.set_yticks(list(range(0, 101, 10)))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m'))
            ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%d'))
            ax1.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.SU.weekday, interval=1))
            ax1.grid(axis='x', color='black', which="major", linewidth=0.2)
            ax1.grid(axis='x', color='black', which="minor", linewidth=0.1)
            ax1.tick_params(axis='both', which='minor', labelsize=8)
            plt.xticks(rotation=45, ha='right', fontsize='9')
            plt.gcf().autofmt_xdate()

            ax2 = ax1.twinx()
            ax2.set_ylabel('Temperature °C', color='xkcd:scarlet')
            ax2.plot(df["time"], df["temperature"], color='xkcd:scarlet')
            ax2.grid(axis='y', linewidth=0.2, color='xkcd:scarlet')
            ax2.set_yticks(list(range(int(df['temperature'].min(numeric_only=True) - 0.5), int(df['temperature'].max(numeric_only=True) + 0.5), 1)))
            ax2.plot(df["time"], df.rolling(window=f'{ThermoProScan.DAYS}D', on='time')['temperature'].mean(), color='xkcd:deep red', alpha=0.3)
            plt.axhline(0, linewidth=1, color='black')

            plt.axis((
                df['time'][0] - timedelta(hours=1),
                df["time"][df["time"].size - 1] + timedelta(hours=1),
                df['temperature'].min(numeric_only=True) - 1,
                df['temperature'].max(numeric_only=True) + 1
            ))

            plt.title(f"Temperature & Humidity date: {df['time'][len(df['time']) - 1].strftime('%Y/%m/%d %H:%M')}, {df['temperature'][len(df['temperature']) - 1]}°C, {df['humidity'][len(df['humidity']) - 1]}%, rolling x̄: {ThermoProScan.DAYS} days")
            plt.tight_layout()
            fig.subplots_adjust(
                left=0.055,
                bottom=0.105,
                right=0.952,
                top=0.948,
                wspace=0.198,
                hspace=0.202
            )
            fig.canvas.manager.set_window_title('ThermoPro Graph')
            DPI = fig.get_dpi()
            fig.set_size_inches(1280.0 / float(DPI), 720.0 / float(DPI))
            plt.savefig(ThermoProScan.PATH + 'ThermoProScan.png')

        else:
            log.warning('csv_data is empty')
            if popup:
                ctypes.windll.user32.MessageBoxW(0, "csv_data is empty", 'Error', 16)

    @staticmethod
    def clear_json_file() -> None:
        if os.path.isfile(ThermoProScan.OUTPUT_JSON_FILE):
            os.remove(ThermoProScan.OUTPUT_JSON_FILE)

    @staticmethod
    def call_rtl_433() -> None:
        log.info("Start call_rtl_433")
        try:
            ThermoProScan.clear_json_file()

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
        log.info('load_json')

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
                    writer.writerow(["time", "temperature", "humidity"])
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
                ThermoProScan.create_graph(False)
        else:
            log.error('json_data empty')

        ThermoProScan.clear_json_file()
        log.info("End task")

    @staticmethod
    def start(self):
        log.info('ThermoProScan started')
        # self.call_all()
        schedule.every().hour.at(":00").do(self.call_all)
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt as ki:
            pass
            # log.error(f'{ki}')
            # log.error(traceback.format_exc())

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
