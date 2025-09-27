import sys

from thermopro import HOME_PATH, PATH

sys.path.append(f'{HOME_PATH}/Documents//BkpScripts')
from Secrets import OPEN_WEATHER_API_KEY, NEVIWEB_EMAIL, NEVIWEB_PASSWORD, HYDRO_EMAIL, HYDRO_PASSWORD

COLUMNS: list[str] = (['time'] +
                      sorted(["ext_temp", "ext_humidity", 'int_temp', 'ext_humidex', 'open_temp', 'open_feels_like', 'open_humidity', 'open_pressure', 'open_clouds', 'open_visibility',
                              'open_wind_speed', 'open_wind_gust', 'open_wind_deg', 'open_rain', 'open_snow', 'open_description', 'open_icon', 'open_sunrise', 'open_sunset', 'open_uvi',
                              'ext_temp_Thermopro-TX2', 'ext_humidity_Thermopro-TX2', 'kwh_neviweb_load', 'int_temp_bureau', 'int_temp_chambre', 'int_temp_salle-de-bain', 'int_temp_salon',
                              'kwh_neviweb', 'kwh_bureau', 'kwh_chambre', 'kwh_salle-de-bain', 'kwh_salon',
                              'kwh_hydro_quebec']) +
                      ['ext_temp_Acurite-609TXC', 'ext_humidity_Acurite-609TXC'])

OUTPUT_CSV_FILE = f"{PATH}ThermoProScan.csv"
LOCATION = f'{HOME_PATH}\\Documents\\NetBeansProjects\\PycharmProjects\\ThermoPro\\'

OUTPUT_JSON_FILE = f"{PATH}ThermoProScan.json"
# RTL_433_VERSION = '25.02'
RTL_433_VERSION = 'nightly'
TIMEOUT = 300
RTL_433_EXE = f"{HOME_PATH}Documents/NetBeansProjects/rtl_433-win-x64-{RTL_433_VERSION}/rtl_433_64bit_static.exe"
SENSORS: list[dict[str, list[str] | dict[str, dict[str, str]]]] = [
    {
        'args': [RTL_433_EXE, '-F', f'json:{OUTPUT_JSON_FILE}', '-T', f'{TIMEOUT}'],
        'sensors': {
            'Thermopro-TX2': {
                'protocol': '162'
            },
            'Acurite-609TXC': {
                'protocol': '11'
            }
        }
    }
]

DAYS = 7 * 2

OPEN_LAT = 45.509  # Montreal
OPEN_LON = -73.588  # Montreal
# OPEN_LAT = 45.55064  # Angus
# OPEN_LON = -73.56062 # Angus
WEATHER_URL = f'https://api.openweathermap.org/data/3.0/onecall?lat={OPEN_LAT}&lon={OPEN_LON}&exclude=minutely,hourly,daily,alerts&appid={OPEN_WEATHER_API_KEY}&units=metric&lang=en'

MIN_HPA = 970
MAX_HPA = 1085
