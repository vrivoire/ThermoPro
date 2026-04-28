import os
import sys

HOME_PATH = f"{os.getenv('USERPROFILE')}".replace('\\', '/')
LOG_PATH = f"{HOME_PATH}/Documents/NetBeansProjects/PycharmProjects/logs/"
BKP_SCRIPTS = f'{HOME_PATH}/Documents/BkpScripts/ThermoPro'

POIDS_PRESSION_PATH = f"{HOME_PATH}/Documents/PoidsPression/"
BKP_PATH = f'{POIDS_PRESSION_PATH}bkp'
CLOUD_PATHS = ['OneDrive', 'Mega', 'Icedrive', 'GoogleDrive/Mon disque', 'TeraBox']
BKP_DAYS = 4

LOG_NAME: str = ''

sys.path.append(f'{BKP_SCRIPTS}/')
from Secrets import OPEN_WEATHER_API_KEY, NEVIWEB_EMAIL, NEVIWEB_PASSWORD, HYDRO_EMAIL, HYDRO_PASSWORD

COLUMNS: list[str] = (['time', 'open_feels_like', 'ext_temp', 'ext_humidity', 'int_temp', 'int_humidity', 'kwh_hydro_quebec', 'kwh_neviweb', 'ext_humidex', 'int_humidex'] +
                      sorted(
                          ['int_temp_bureau', 'int_temp_chambre', 'int_temp_salle-de-bain', 'int_temp_salon', 'kwh_bureau', 'kwh_chambre', 'kwh_salle-de-bain', 'kwh_salon', 'open_clouds', 'open_description', 'open_humidity', 'open_icon',
                           'open_pressure', 'open_rain', 'open_snow', 'open_sunrise', 'open_sunset', 'open_temp', 'open_uvi', 'open_visibility', 'open_wind_deg', 'open_wind_gust', 'open_wind_speed']
                      )
                      )

THERMO_PRO_SCAN_OUTPUT_JSON_FILE = f"{POIDS_PRESSION_PATH}ThermoProScan.json.zip"
SENSORS_OUTPUT_JSON_FILE = f"{POIDS_PRESSION_PATH}Sensors.json.zip"

LOCATION = f'{HOME_PATH}/Documents/NetBeansProjects/PycharmProjects/ThermoPro/'

OUTPUT_RTL_433_FILE: str = f"{POIDS_PRESSION_PATH}rtl_433.json"
# RTL_433_VERSION = '25.12'
RTL_433_VERSION = 'nightly'
TIMEOUT: int = 5 * 60
RTL_433_EXE_PATH: str = f"{HOME_PATH}/Documents/NetBeansProjects/rtl_433-win-x64-{RTL_433_VERSION}/rtl_433_64bit_static.exe"
RTL_433_EXE = RTL_433_EXE_PATH[RTL_433_EXE_PATH.rfind('/') + 1:]

DAYS_PER_MONTH = 30.437  # https://www.britannica.com/science/time/Standard-time

# OPEN_LAT = 45.509  # Montreal
# OPEN_LON = -73.588  # Montreal
OPEN_LAT = 45.55064  # Angus
OPEN_LON = -73.56062  # Angus
WEATHER_URL = f'https://api.openweathermap.org/data/3.0/onecall?lat={OPEN_LAT}&lon={OPEN_LON}&exclude=minutely,hourly,daily,alerts&appid={OPEN_WEATHER_API_KEY}&units=metric&lang=en'

MIN_HPA = 970
MAX_HPA = 1085

ROBOCOPY_RETURNCODES: dict[int, str] = {
    0: 'No files were copied. No failure was met. No files were mismatched. The files already exist in the destination directory; so the copy operation was skipped.',
    1: 'All files were copied successfully.',
    2: "There are some additional files in the destination directory that aren't present in the source directory. No files were copied.",
    3: 'Some files were copied. Additional files were present. No failure was met.',
    5: 'Some files were copied. Some files were mismatched. No failure was met.',
    6: 'Additional files and mismatched files exist. No files were copied and no failures were met. Which means that the files already exist in the destination directory.',
    7: 'Files were copied, a file mismatch was present, and additional files were present.',
    8: "Several files didn't copy."
}
