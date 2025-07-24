import logging as log
import logging.handlers
import os.path

HOME_PATH = f"{os.getenv('USERPROFILE')}/"
LOG_PATH = f"{HOME_PATH}Documents/NetBeansProjects/PycharmProjects/logs/"

def ppretty(value, htchar='\t', lfchar='\n', indent=0):
    nlch: str = lfchar + htchar * (indent + 1)
    if type(value) is dict:
        items = [
            nlch + repr(key) + ': ' + ppretty(value[key], htchar, lfchar, indent + 1)
            for key in value
        ]
        return '{%s}' % (','.join(items) + lfchar + htchar * indent)
    elif type(value) is list:
        items = [
            nlch + ppretty(item, htchar, lfchar, indent + 1)
            for item in value
        ]
        return '[%s]' % (','.join(items) + lfchar + htchar * indent)
    elif type(value) is tuple:
        items = [
            nlch + ppretty(item, htchar, lfchar, indent + 1)
            for item in value
        ]
        return '(%s)' % (','.join(items) + lfchar + htchar * indent)
    else:
        return repr(value)

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
    # log.info(f'LOG_FILE={name}')
