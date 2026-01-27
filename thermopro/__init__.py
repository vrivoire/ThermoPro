import copy
import json
import logging as log
import logging.handlers
import os.path
import shutil
import subprocess
import traceback
import zipfile
from datetime import datetime

import pandas
import pandas as pd
from pandas import DataFrame, Timestamp

import thermopro
from thermopro.constants import COLUMNS, THERMO_PRO_SCAN_OUTPUT_JSON_FILE, LOG_PATH, HOME_PATH, TIMEOUT, POIDS_PRESSION_PATH, SENSORS_OUTPUT_JSON_FILE, DAYS_PER_MONTH


# HOME_PATH = f"{os.getenv('USERPROFILE')}/".replace('\\', '/')
# LOG_PATH = f"{HOME_PATH}Documents/NetBeansProjects/PycharmProjects/logs/"
# POIDS_PRESSION_PATH = f"{HOME_PATH}GoogleDrive/PoidsPression/"
# LOG_NAME: str = ''

def save_sensors(json_data: dict, sensors: dict[str, int | float | str], kwh_dict: dict[str, float]) -> None:
    try:
        start: Timestamp = Timestamp.now()

        json_data2 = copy.deepcopy(json_data)
        sensors2 = copy.deepcopy(sensors)
        kwh_dict = copy.deepcopy(kwh_dict)

        data: dict[str, int | float | str] = {'time': datetime.now().isoformat()}
        sensors2.update(json_data2)
        for entry in [s for s in list(sensors2) if "ext_temp" in s]:
            data[entry] = sensors2[entry]
        for entry in [s for s in list(sensors2) if "int_temp" in s]:
            data[entry] = sensors2[entry]
        for entry in [s for s in list(sensors2) if "ext_humidity" in s]:
            data[entry] = sensors2[entry]
        for entry in [s for s in list(sensors2) if "int_humidity" in s]:
            data[entry] = sensors2[entry]
        for entry in [s for s in list(sensors2) if "kwh_" in s]:
            data[entry] = sensors2.get(entry)

        df: DataFrame = pd.DataFrame([data])

        df = df.astype({'time': 'datetime64[ns]'})
        df.set_index('time')
        df = df.sort_values(by='time', ascending=True)

        df_in = load_sensors()

        if len(kwh_dict) > 0:
            try:
                start: Timestamp = Timestamp.now()
                kwh_list: list[dict[str, float]] = [{'time': f'{k}:00', 'kwh_hydro_quebec': v} for k, v in kwh_dict.items()]
                df_kwh: DataFrame = pd.DataFrame(kwh_list, columns=['time', 'kwh_hydro_quebec'])
                df_kwh = df_kwh.astype({'time': 'datetime64[ns]'})
                df_kwh.set_index('time')
                kwh_first_timestamp: Timestamp = df_kwh['time'].head(1)[0]
                kwh_last_timestamp: Timestamp = df_kwh['time'].tail(1)[len(df_kwh) - 1]
                log.info(f'date range: {kwh_first_timestamp}...{kwh_last_timestamp}')

                df_in = thermopro.load_sensors()
                df_in['kwh_hydro_quebec'] = 0.0
                df_in.astype({'kwh_hydro_quebec': float})
                df_in['time'] = pd.to_datetime(df_in['time'])
                df_in.astype({'time': 'datetime64[ns]'})
                df_in.set_index('time')

                for index in df_kwh.index.tolist():
                    timestamp: Timestamp = df_kwh.iloc[index]['time']
                    filtered_df_in = df_in[
                        (df_in['time'].dt.year == timestamp.year) &
                        (df_in['time'].dt.month == timestamp.month) &
                        (df_in['time'].dt.day == timestamp.day) &
                        (df_in['time'].dt.hour == timestamp.hour)
                        ]
                    df_in_indexes: list[int] | None = filtered_df_in.index.tolist() if len(filtered_df_in.index.tolist()) > 0 else None
                    if df_in_indexes is not None:
                        for df_in_index in df_in_indexes:
                            df_in.loc[df_in_index, 'kwh_hydro_quebec'] = df_kwh.iloc[index]['kwh_hydro_quebec'] if df_kwh.iloc[index]['kwh_hydro_quebec'] else 0.0
            except Exception as ex:
                log.error(ex)
                log.error(traceback.format_exc())

        df_updated = pd.concat([df_in, df], ignore_index=True)
        for entry in [s for s in list(sensors2) if "kwh_" in s]:
            df_updated = df_updated.astype({entry: 'Float64'})

        columns = df_updated.columns.tolist()
        cols = ['time', 'ext_temp', 'ext_humidity', 'int_temp', 'int_humidity', 'kwh_hydro_quebec', 'kwh_neviweb']
        for col in cols:
            columns.remove(col)
        df_updated = df_updated[cols + sorted(columns)]

        df_updated['kwh_hydro_quebec'] = df_updated['kwh_hydro_quebec'].apply(lambda x: 0.0 if pd.isna(x) else x)
        df_updated['kwh_neviweb'] = df_updated['kwh_neviweb'].apply(lambda x: 0.0 if pd.isna(x) else x)

        df_updated.to_json(SENSORS_OUTPUT_JSON_FILE, orient='records', indent=4, date_format='iso',
                           compression={
                               'method': 'zip',
                               'compression': zipfile.ZIP_DEFLATED,
                               'compresslevel': 9
                           })
        show_df(df_updated, title='save_sensors', max_rows=10)
        log.info(f'Elapsed: {Timestamp.now() - start}, File of Sensors "{SENSORS_OUTPUT_JSON_FILE}" is saved.')
    except Exception as ex:
        log.error(ex)
        log.error(traceback.format_exc())


def load_sensors() -> DataFrame | None:
    df_in: DataFrame | None = None
    if os.path.exists(SENSORS_OUTPUT_JSON_FILE):
        df_in: DataFrame = pd.read_json(SENSORS_OUTPUT_JSON_FILE, compression='zip')
    if df_in is None:
        raise f"Unable to load file {SENSORS_OUTPUT_JSON_FILE}."
    return df_in


def save_json(df: DataFrame) -> None:
    df = set_astype(df)
    df.to_json(THERMO_PRO_SCAN_OUTPUT_JSON_FILE, orient='records', indent=4, date_format='iso',
               compression={
                   'method': 'zip',
                   'compression': zipfile.ZIP_DEFLATED,
                   'compresslevel': 9
               })

    # for orient in ['columns', 'index', 'split', 'table']:
    #     print(f'{OUTPUT_JSON_FILE[:OUTPUT_JSON_FILE.rfind('.')]}_{orient}.json')
    #     df.to_json(f'{OUTPUT_JSON_FILE[:OUTPUT_JSON_FILE.rfind('.')]}_{orient}.json', orient=orient, indent=4, date_format='iso')
    log.info('JSON saved')


def copy_to_cloud() -> None:
    for drive in ['OneDrive', 'Mega', 'Icedrive', 'Documents']:
        destination_folder = f"{HOME_PATH}{drive}/PoidsPression"
        try:
            if os.path.isdir(destination_folder):
                try:
                    shutil.rmtree(destination_folder)
                    log.info(f"Directory and all contents at '{destination_folder}' deleted successfully.")
                except OSError as e:
                    log.error(f"Error: {destination_folder} : {e.strerror}")
            shutil.copytree(POIDS_PRESSION_PATH, destination_folder, dirs_exist_ok=True)
            log.info(f"Folder and contents successfully copied from '{POIDS_PRESSION_PATH}' to '{destination_folder}'")
        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())


def load_json() -> DataFrame:
    try:
        df: DataFrame | None = None

        if os.path.exists(THERMO_PRO_SCAN_OUTPUT_JSON_FILE):
            log.info(f'Loading file {THERMO_PRO_SCAN_OUTPUT_JSON_FILE}')
            df: DataFrame = pandas.read_json(THERMO_PRO_SCAN_OUTPUT_JSON_FILE, compression='zip')

        # if os.path.exists(OUTPUT_JSON_FILE):
        #     log.info(f'Loading file {OUTPUT_JSON_FILE}')
        #     df: DataFrame = pandas.read_json(OUTPUT_JSON_FILE)
        # elif os.path.exists(OUTPUT_CSV_FILE):
        #     log.info(f'Loading file {OUTPUT_CSV_FILE}')
        #     df: DataFrame = pandas.read_csv(OUTPUT_CSV_FILE)
        # else:
        #     raise f"The files {OUTPUT_JSON_FILE} and {OUTPUT_CSV_FILE} do not exist."

        # df = df.drop('ext_humidity_Acurite-609TXC', axis=1)
        # df = df.drop('ext_temp_Acurite-609TXC', axis=1)

        if df is None:
            raise f"Unable to load file {THERMO_PRO_SCAN_OUTPUT_JSON_FILE}"
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
    # nlch: str = return_char + tab_char * (indent + 1)
    # if type(value) is dict:
    #     value = sorted(dict(value.items()), key=lambda item: item[0].lower())
    #     items = [
    #         nlch + repr(key) + ': ' + ppretty(value[key], tab_char, return_char, indent + 1)
    #         for key in value
    #     ]
    #     return '{%s}' % (','.join(items) + return_char + tab_char * indent)
    # elif type(value) is list:
    #     items = [
    #         nlch + ppretty(item, tab_char, return_char, indent + 1)
    #         for item in value
    #     ]
    #     return '[%s]' % (','.join(items) + return_char + tab_char * indent)
    # elif type(value) is tuple:
    #     items = [
    #         nlch + ppretty(item, tab_char, return_char, indent + 1)
    #         for item in value
    #     ]
    #     return '(%s)' % (','.join(items) + return_char + tab_char * indent)
    # else:
    #     return repr(value)


def set_up(log_name: str):
    global LOG_NAME
    LOG_NAME = f'{LOG_PATH}{log_name[log_name.rfind('\\') + 1:len(log_name) - 3]}.log'
    log_name_error = f'{LOG_PATH}{log_name[log_name.rfind('\\') + 1:len(log_name) - 3]}.error.log'

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    file_handler = logging.handlers.TimedRotatingFileHandler(LOG_NAME, when='midnight', interval=1, backupCount=7,
                                                             encoding=None, delay=True, utc=False, atTime=None,
                                                             errors=None)
    file_handler_error = logging.handlers.TimedRotatingFileHandler(log_name_error, when='midnight', interval=1, backupCount=7,
                                                                   encoding=None, delay=True, utc=False, atTime=None,
                                                                   errors=None)
    file_handler_error.level = logging.ERROR

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
