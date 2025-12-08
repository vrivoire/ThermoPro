import json
import logging as log
import logging.handlers
import os.path
import subprocess
import traceback
import zipfile
from datetime import datetime

import pandas
from dateutil.relativedelta import relativedelta
from pandas import DataFrame

from thermopro.constants import COLUMNS, OUTPUT_JSON_FILE, OUTPUT_CSV_FILE, LOG_PATH


# HOME_PATH = f"{os.getenv('USERPROFILE')}/".replace('\\', '/')
# LOG_PATH = f"{HOME_PATH}Documents/NetBeansProjects/PycharmProjects/logs/"
# POIDS_PRESSION_PATH = f"{HOME_PATH}GoogleDrive/PoidsPression/"
# LOG_NAME: str = ''


@staticmethod
def save_json(df: DataFrame):
    df = set_astype(df)
    # df.to_json(OUTPUT_JSON_FILE, orient='records', indent=4, date_format='iso')
    df.to_json(OUTPUT_JSON_FILE + '.zip', orient='records', indent=4, date_format='iso',
               compression={
                   'method': 'zip',
                   'compression': zipfile.ZIP_DEFLATED,
                   'compresslevel': 9
               })

    # for orient in ['columns', 'index', 'split', 'table']:
    #     print(f'{OUTPUT_JSON_FILE[:OUTPUT_JSON_FILE.rfind('.')]}_{orient}.json')
    #     df.to_json(f'{OUTPUT_JSON_FILE[:OUTPUT_JSON_FILE.rfind('.')]}_{orient}.json', orient=orient, indent=4, date_format='iso')
    log.info('JSON saved')


@staticmethod
def load_json() -> DataFrame:
    try:
        df: DataFrame

        if os.path.exists(OUTPUT_JSON_FILE + '.zip'):
            log.info(f'Loading file {OUTPUT_JSON_FILE + '.zip'}')
            df: DataFrame = pandas.read_json(OUTPUT_JSON_FILE + '.zip', compression='zip')

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

        df = set_astype(df)

        df_conditional_drop = df.drop(df[
                                          (df['time'].dt.minute >= 12) &
                                          (df['time'].dt.minute <= 55) &
                                          (df['time'] <= (datetime.now() - relativedelta(weeks=1)))
                                          ].index)
        log.info(f'Purged {len(df) - len(df_conditional_drop)} rows {len(df)}, {len(df_conditional_drop)}.')
        df = df_conditional_drop.reset_index(drop=True)

        df = df[COLUMNS]

        for col in ['kwh_hydro_quebec', 'ext_temp', 'int_temp', 'open_temp', 'int_humidity', 'int_humidex', 'ext_humidity_Thermopro-TX2', 'ext_humidity_ThermoPro-TX7B',
                    'ext_temp_ThermoPro-TX7B', 'ext_temp_Thermopro-TX2', 'int_temp_Acurite-609TXC', 'int_temp_bureau', 'int_temp_chambre', 'int_temp_salle-de-bain', 'int_temp_salon',
                    'kwh_bureau', 'kwh_chambre', 'kwh_salle-de-bain', 'kwh_salon', 'open_feels_like']:
            df[col] = df[col].astype('Float64')
            df[col] = df[col].ffill().fillna(0.0)
        for col in ['ext_humidity', 'open_humidity', 'open_pressure', 'ext_humidex', 'kwh_neviweb', 'int_humidity', 'int_humidity_Acurite-609TXC']:
            df[col] = df[col].astype('Int64')
            df[col] = df[col].ffill().fillna(0)

        return df
    except Exception as ex:
        log.error(ex)
        log.error(traceback.format_exc())
        raise ex


@staticmethod
def set_astype(df: DataFrame) -> DataFrame:
    columns = list(COLUMNS)
    for col in ['time', 'open_sunrise', 'open_sunset']:
        df = df.astype({col: 'datetime64[ns]'})
        columns.remove(col)
    for col in ['ext_humidex', 'ext_humidity', 'int_humidity', 'ext_humidity_Thermopro-TX2',
                'int_humidity_Acurite-609TXC', 'open_clouds', 'open_humidity', 'open_pressure', 'open_visibility',
                'open_wind_deg']:
        try:
            df[col] = df[col].round().astype('Int64')
        except KeyError as ex:
            log.error(df[col].dtypes)
            log.error(ex)
            log.error(traceback.format_exc())
        columns.remove(col)
    for col in ['open_description', 'open_icon']:
        df[col] = df[col].astype(str)
        columns.remove(col)
    for col in columns:
        try:
            df[col] = df[col].astype('Float64')
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
    return df


def show_df(df: DataFrame):
    pandas.set_option('display.max_columns', None)
    pandas.set_option('display.width', 1000)
    pandas.set_option('display.max_rows', 50)
    log.info(f'DataFrame len: {len(df)}\n{df[len(df) - 50:]}')


def ping(name: str):
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


def ppretty(value, tab_char='\t', return_char='\n', indent=0):
    return json.dumps(value, indent=4, sort_keys=True, default=str)
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
