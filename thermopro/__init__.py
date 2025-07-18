import logging as log
import logging.handlers
import os.path

HOME_PATH = f"{os.getenv('USERPROFILE')}/"
LOG_PATH = f"{HOME_PATH}Documents/NetBeansProjects/PycharmProjects/logs/"
LOG_FILE = f'{LOG_PATH}ThermoProScan.log'


def namer(name: str) -> str:
    return name.replace(".log", "") + ".log"


if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)
fileHandler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='midnight', interval=1, backupCount=7,
                                                        encoding=None, delay=False, utc=False, atTime=None,
                                                        errors=None)
fileHandler.namer = namer
log.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] [%(filename)s.%(funcName)s:%(lineno)d] %(message)s",
    handlers=[
        fileHandler,
        logging.StreamHandler()
    ]
)
