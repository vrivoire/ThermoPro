import json
import logging as log
import logging.handlers
import os.path
import subprocess
import traceback
import zipfile
from datetime import datetime

import pandas
import pandas as pd
import schedule
from pandas import DataFrame

import thermopro
from thermopro.constants import COLUMNS, THERMO_PRO_SCAN_OUTPUT_JSON_FILE, LOG_PATH, HOME_PATH, TIMEOUT, POIDS_PRESSION_PATH, SENSORS_OUTPUT_JSON_FILE, DAYS_PER_MONTH, RTL_433_EXE_PATH, OUTPUT_RTL_433_FILE, BKP_SCRIPTS, CLOUD_PATHS, ROBOCOPY_RETURNCODES

sensors: dict[str, dict[str, list[str]] | dict[str, str | None]]


def save_sensors(now: datetime, sensors: dict[str, int | float | datetime]) -> None:
    try:
        sensors['time'] = now
        df_sensors: DataFrame = pd.DataFrame([sensors])
        df_sensors = df_sensors.astype({'time': 'datetime64[ns]'})

        df_in: DataFrame = thermopro.load_sensors()
        df_in = pd.concat([df_in, df_sensors], ignore_index=True)

        df_in = df_in[['time'] + [c for c in sorted(df_in.columns) if c != 'time']]

        df_in.to_json(SENSORS_OUTPUT_JSON_FILE, orient='records', indent=4, date_format='iso',
                      compression={
                          'method': 'zip',
                          'compression': zipfile.ZIP_DEFLATED,
                          'compresslevel': 9
                      })

        show_df(df_in, title='save_sensors', max_rows=10)
        log.info(f'File of Sensors "{SENSORS_OUTPUT_JSON_FILE}" is saved.')
    except Exception as ex:
        log.error(ex)
        log.error(traceback.format_exc())


def get_sensors() -> dict[str, dict[str, list[str]] | dict[str, str | None]]:
    global sensors
    if sensors is None:
        log.info(f"Loading sensors from sensor_list.json...")
        try:
            with open(f'{BKP_SCRIPTS}/sensor_list.json', 'r') as file:
                sensors = json.load(file)

            for freq in sensors:
                for i, token in enumerate(sensors[freq]['args']):
                    try:
                        start: int = token.find('{') + 1
                        end: int = token.find('}')
                        if start != -1 and end != -1:
                            sensors[freq]['args'][i] = sensors[freq]['args'][i].replace(token[start - 1:end + 1], str(getattr(constants, token[start:end])))
                    except AttributeError as ae:
                        pass
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())
            raise ex

    return sensors


def load_sensors() -> DataFrame | None:
    df_in: DataFrame | None = None
    if os.path.exists(SENSORS_OUTPUT_JSON_FILE):
        df_in: DataFrame = pd.read_json(SENSORS_OUTPUT_JSON_FILE, compression='zip')

    sensor_list: list[str] = []
    for freq in get_sensors():
        for name in get_sensors()[freq]['sensors']:
            for loc in ['ext', 'int']:
                for tp in ['temp', 'humidity']:
                    sensor_list.append(f'{loc}_{tp}_{name}')
    sensor_list = ['time'] + sorted(sensor_list)

    if df_in is None:
        df_in = pd.DataFrame(columns=sensor_list)

    df_in = df_in[sensor_list]
    for sensor in sensor_list:
        if 'time' != sensor:
            if "_humidity_" in sensor:
                df_in = df_in.astype({sensor: 'Int64'})
            if "_temp_" in sensor:
                df_in = df_in.astype({sensor: 'float64'})
        else:
            df_in = df_in.astype({sensor: 'datetime64[ns]'})
    df_in = df_in[sensor_list]

    return df_in


def load_json(thermo_pro_scan_output_json_file=THERMO_PRO_SCAN_OUTPUT_JSON_FILE) -> DataFrame:
    try:
        df: DataFrame | None = None

        if os.path.exists(thermo_pro_scan_output_json_file):
            log.info(f'Loading file {thermo_pro_scan_output_json_file}')
            df: DataFrame = pandas.read_json(thermo_pro_scan_output_json_file, compression='zip', orient='split')

        if df is None:
            raise f"Unable to load file {thermo_pro_scan_output_json_file}"
        else:
            df = set_astype(df)
            for col in ['time', 'open_sunrise', 'open_sunset']:
                df = df.astype({col: 'datetime64[ns]'})

            # PURGE !???!!!!!????
            # timeout: int = int(TIMEOUT / 60)
            # df_conditional_drop = df.drop(df[
            #                                   (df['time'].dt.minute >= int32(3 * timeout)) &
            #                                   (df['time'].dt.minute <= int32(60 - timeout)) &
            #                                   (df['time'] <= (datetime.now() - relativedelta(weeks=1)))
            #                                   ].index)
            # log.info(f'Purged {len(df) - len(df_conditional_drop)} rows {len(df)}, {len(df_conditional_drop)}.')
            # df = df_conditional_drop.reset_index(drop=True)

            df = df[COLUMNS]

            return df
    except Exception as ex:
        log.error(ex)
        log.error(traceback.format_exc())
        raise ex


def save_json(df: DataFrame, thermo_pro_scan_output_json_file=THERMO_PRO_SCAN_OUTPUT_JSON_FILE) -> None:
    df = set_astype(df)
    df.to_json(thermo_pro_scan_output_json_file, orient='split', indent=4, date_format='iso',
               compression={
                   'method': 'zip',
                   'compression': zipfile.ZIP_LZMA,
                   'compresslevel': 9
               })
    log.info(f'{thermo_pro_scan_output_json_file}\t\t{os.path.getsize(thermo_pro_scan_output_json_file)} bytes')
    log.info('JSON saved')


def display_schedule() -> None:
    log.info('Schedule set:')
    for job in schedule.get_jobs():
        log.info(f'---> {job.__repr__()}')


def copy_to_cloud() -> None:
    try:
        for drive in CLOUD_PATHS:
            log.info(' Start send to clouds '.center(80, '*'))
            destination_folder = f"{HOME_PATH}/{drive}/PoidsPression"

            if not os.path.isdir(POIDS_PRESSION_PATH):
                raise Exception(f"Source folder '{POIDS_PRESSION_PATH}' does not exist.")
            if not os.path.isdir(destination_folder):
                os.makedirs(destination_folder, exist_ok=True)

            args: list[str] = ['robocopy', POIDS_PRESSION_PATH, destination_folder, '/MIR', '/NP', '/NDL', '/S', '/E', '/NJH', '/NJS', '/FFT', '/XF', '*.ffs_tmp', 'desktop.ini', 'rtl_433.json', 'Renpho Health-R_PmJP0']
            try:
                log.info(f'args: {' '.join(args)}')
                completed_process = subprocess.run(
                    args,
                    capture_output=True,
                    timeout=TIMEOUT,
                    encoding="cp437",
                    check=False,
                    shell=True,
                    text=True
                )
                log.info(f'robocopy returncode: {completed_process.returncode}: {ROBOCOPY_RETURNCODES.get(completed_process.returncode)}')
                if completed_process.returncode > 0:
                    log.info(f'robocopy stdout: {completed_process.stdout}')
                    log.error(f'robocopy stderr: {completed_process.stderr}')
            except subprocess.TimeoutExpired as timeoutExpired:
                log.error(f"TimeoutExpired, returned: {timeoutExpired}")
            except Exception as ex:
                log.error(ex)
                log.error(traceback.format_exc())
    except Exception as ex:
        log.error(ex)
        log.error(traceback.format_exc())
    log.info(' End send to clouds '.center(80, '*'))
    display_schedule()


def set_astype(df: DataFrame) -> DataFrame:
    columns = list(COLUMNS)
    for col in ['time', 'open_sunrise', 'open_sunset']:
        df = df.astype({col: 'datetime64[ns]'})
        columns.remove(col)
    for col in ['ext_humidex', 'ext_humidity', 'int_humidity', 'open_clouds', 'open_humidity', 'open_pressure', 'open_visibility', 'open_wind_deg']:
        try:
            df[col] = df[col].round().astype('Int64')
            df[col] = df[col].apply(lambda x: 0 if pd.isna(x) else x)
        except KeyError as ex:
            log.error(f'{col} -> {df.columns}')
            log.error(ex)
            log.error(traceback.format_exc())
        columns.remove(col)
    for col in ['open_description', 'open_icon']:
        df[col] = df[col].astype(str)
        columns.remove(col)
    for col in columns:
        try:
            df[col] = df[col].astype('Float64')
            df[col] = df[col].apply(lambda x: 0.0 if pd.isna(x) else x)
        except KeyError as ex:
            log.error(df[col].dtypes)
            log.error(ex)
            log.error(traceback.format_exc())

    df.set_index('time')
    all_columns2: list[str] = sorted(df.columns.tolist())
    all_columns2.remove('time')
    all_columns2 = ['time'] + all_columns2
    df = df[all_columns2]
    df = df.sort_values(by='time', ascending=True)
    df['kwh_hydro_quebec'] = df['kwh_hydro_quebec'].apply(lambda x: 0.0 if pd.isna(x) else x)
    df['kwh_neviweb'] = df['kwh_neviweb'].apply(lambda x: 0.0 if pd.isna(x) else x)

    return df


def show_df(df: DataFrame, title='', max_columns=None, width=1000, max_rows=50) -> None:
    pandas.set_option('display.max_columns', max_columns)
    pandas.set_option('display.width', width)
    pandas.set_option('display.max_rows', max_rows)
    log.info(f'>>>> {title} DataFrame len: {len(df)}\n{df[len(df) - max_rows:]}')


def ping(name: str) -> bool:
    try:
        command = ['ping', '-4', '-n', '1', f'{name}']
        completed_process = subprocess.run(command, text=True, capture_output=True)
        if "100%" in completed_process.stdout:
            log.info(f"{name} is unreachable.")
            return False
        else:
            log.info(f"{name} is reachable.")
            return True

    except subprocess.CalledProcessError as e:
        log.error(f"Error executing ping command: {e}")
    except FileNotFoundError:
        log.error("Ping command not found. Ensure it's in your system's PATH.")
    except Exception as ex:
        log.error(ex)
        log.error(traceback.format_exc())
    return False


def ppretty(value: object, tab_char: object = '\t', return_char: object = '\n', indent: object = 0) -> str | None:
    try:
        return json.dumps(value, indent=4, sort_keys=True, default=str, check_circular=False)
    except Exception as ex:
        log.error(ex)
        log.error(traceback.format_exc())
    return None


def set_up(log_name: str):
    global LOG_NAME
    LOG_NAME = f'{LOG_PATH}{log_name[log_name.rfind('\\') + 1:len(log_name) - 3]}.log'
    log_name_error = f'{LOG_PATH}{log_name[log_name.rfind('\\') + 1:len(log_name) - 3]}.error.log'

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    file_handler = logging.handlers.TimedRotatingFileHandler(LOG_NAME, when='midnight', interval=1, backupCount=7,
                                                             encoding="utf-8", delay=True, utc=False, atTime=None,
                                                             errors=None)
    file_handler_error = logging.handlers.TimedRotatingFileHandler(log_name_error, when='midnight', interval=1, backupCount=7,
                                                                   encoding="utf-8", delay=True, utc=False, atTime=None,
                                                                   errors=None)
    file_handler_error.setLevel(logging.WARNING)

    file_handler.namer = lambda name: name.replace(".log", "") + ".log"
    file_handler_error.namer = lambda name: name.replace(".log", "") + ".log"
    log.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-8s] [%(filename)s.%(funcName)s:%(lineno)d] %(message)s",
        handlers=[
            file_handler,
            file_handler_error,
            logging.StreamHandler()
        ]
    )
