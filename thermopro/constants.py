import sys

from thermopro import HOME_PATH, PATH

sys.path.append(f'{HOME_PATH}/Documents//BkpScripts')
from Secrets import OPEN_WEATHER_API_KEY, NEVIWEB_EMAIL, NEVIWEB_PASSWORD

OUTPUT_CSV_FILE = f"{PATH}ThermoProScan.csv"
LOCATION = f'{HOME_PATH}\\Documents\\NetBeansProjects\\PycharmProjects\\ThermoPro\\'

OUTPUT_JSON_FILE = f"{PATH}ThermoProScan.json"
# RTL_433_VERSION = '25.02'
RTL_433_VERSION = 'nightly'
TIMEOUT = 300
SENSORS: dict[str, str] = {'Thermopro-TX2': '162', 'Rubicson-Temperature': '02'}
RTL_433_EXE = f"{HOME_PATH}Documents/NetBeansProjects/rtl_433-win-x64-{RTL_433_VERSION}/rtl_433_64bit_static.exe"

DAYS = 7 * 2

OPEN_LAT = 45.509  # Montreal
OPEN_LON = -73.588  # Montreal
# OPEN_LAT = 45.55064  # Angus
# OPEN_LON = -73.56062 # Angus
WEATHER_URL = f'https://api.openweathermap.org/data/3.0/onecall?lat={OPEN_LAT}&lon={OPEN_LON}&exclude=minutely,hourly,daily,alerts&appid={OPEN_WEATHER_API_KEY}&units=metric&lang=en'

MIN_HPA = 970
MAX_HPA = 1085
