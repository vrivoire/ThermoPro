import os
import sys

HOME_PATH = f"{os.getenv('USERPROFILE')}/".replace('\\', '/')
LOG_PATH = f"{HOME_PATH}Documents/NetBeansProjects/PycharmProjects/logs/"

POIDS_PRESSION_PATH = f"{HOME_PATH}GoogleDrive/PoidsPression/"
BKP_PATH = f'{HOME_PATH}Documents/PoidsPression/bkp/'
BKP_DAYS = 5

LOG_NAME: str = ''

sys.path.append(f'{HOME_PATH}/Documents/BkpScripts')
from Secrets import OPEN_WEATHER_API_KEY, NEVIWEB_EMAIL, NEVIWEB_PASSWORD, HYDRO_EMAIL, HYDRO_PASSWORD

COLUMNS: list[str] = (['time', 'open_feels_like', 'ext_temp', 'ext_humidity', 'int_temp', 'int_humidity', 'kwh_hydro_quebec', 'kwh_neviweb', 'ext_humidex', 'int_humidex'] +
                      sorted(
                          ['int_temp_bureau', 'int_temp_chambre', 'int_temp_salle-de-bain', 'int_temp_salon', 'kwh_bureau', 'kwh_chambre', 'kwh_salle-de-bain', 'kwh_salon', 'open_clouds', 'open_description', 'open_humidity', 'open_icon',
                           'open_pressure', 'open_rain', 'open_snow', 'open_sunrise', 'open_sunset', 'open_temp', 'open_uvi', 'open_visibility', 'open_wind_deg', 'open_wind_gust', 'open_wind_speed']
                      )
                      )

OUTPUT_CSV_FILE = f"{POIDS_PRESSION_PATH}ThermoProScan.csv"
OUTPUT_JSON_FILE = f"{POIDS_PRESSION_PATH}ThermoProScan.json"

LOCATION = f'{HOME_PATH}/Documents/NetBeansProjects/PycharmProjects/ThermoPro/'

OUTPUT_RTL_433_FILE: str = f"{POIDS_PRESSION_PATH}rtl_433.json"
RTL_433_VERSION = '25.12'
# RTL_433_VERSION = 'nightly'
TIMEOUT: int = 5 * 60
RTL_433_EXE_PATH: str = f"{HOME_PATH}Documents/NetBeansProjects/rtl_433-win-x64-{RTL_433_VERSION}/rtl_433_64bit_static.exe"
RTL_433_EXE = RTL_433_EXE_PATH[RTL_433_EXE_PATH.rfind('/') + 1:]

SENSORS2: dict[str, dict[str, list[str | int] | dict[str, str]] | dict[str, list[str] | dict[str, str]]] = {
    '915': {
        'args': [RTL_433_EXE_PATH, '-F', f'json:{OUTPUT_RTL_433_FILE}', '-T', f'{TIMEOUT}', '-R', '278', '-R', '113', '-f', '915M', '-Y', 'classic', '-s', '250k'],
        'sensors': {
            'ThermoPro-TX7B': 'int',
            'AmbientWeather-WH31B': 'ext'
        }
    },
    '433': {
        'args': [RTL_433_EXE_PATH, '-F', f'json:{OUTPUT_RTL_433_FILE}', '-T', f'{TIMEOUT}', '-R', '11', '-R', '162'],
        'sensors': {
            'Acurite-609TXC': 'int',
            'Thermopro-TX2': 'ext'
        }
    }
}

DAYS_PER_MONTH = 30.437  # https://www.britannica.com/science/time/Standard-time

OPEN_LAT = 45.509  # Montreal
OPEN_LON = -73.588  # Montreal
# OPEN_LAT = 45.55064  # Angus
# OPEN_LON = -73.56062 # Angus
WEATHER_URL = f'https://api.openweathermap.org/data/3.0/onecall?lat={OPEN_LAT}&lon={OPEN_LON}&exclude=minutely,hourly,daily,alerts&appid={OPEN_WEATHER_API_KEY}&units=metric&lang=en'

MIN_HPA = 970
MAX_HPA = 1085
