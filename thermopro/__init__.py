import logging as log
import logging.handlers
import os.path

HOME_PATH = f"{os.getenv('USERPROFILE')}/"
LOG_PATH = f"{HOME_PATH}Documents/NetBeansProjects/PycharmProjects/logs/"


def set_up(name: str):
    name = f'{LOG_PATH}{name[name.rfind('\\') + 1:len(name) - 3]}.log'

    def new_namer() -> str | None:
        return name.replace(".log", "") + ".log"

    # if not os.path.exists(name):
    #     os.mkdir(name)

    file_handler = logging.handlers.TimedRotatingFileHandler(name, when='midnight', interval=1, backupCount=7,
                                                             encoding=None, delay=True, utc=False, atTime=None,
                                                             errors=None)
    file_handler.namer = new_namer()
    log.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-8s] [%(filename)s.%(funcName)s:%(lineno)d] %(message)s",
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )
    log.info(f'LOG_FILE={name}')
