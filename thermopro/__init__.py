import logging as log
import logging.handlers
import os.path
import subprocess
import traceback

HOME_PATH = f"{os.getenv('USERPROFILE')}/".replace('\\', '/')
LOG_PATH = f"{HOME_PATH}Documents/NetBeansProjects/PycharmProjects/logs/"
PATH = f"{HOME_PATH}GoogleDrive/PoidsPression/"
LOG_NAME: str = ''


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
    nlch: str = return_char + tab_char * (indent + 1)
    if type(value) is dict:
        items = [
            nlch + repr(key) + ': ' + ppretty(value[key], tab_char, return_char, indent + 1)
            for key in value
        ]
        return '{%s}' % (','.join(items) + return_char + tab_char * indent)
    elif type(value) is list:
        items = [
            nlch + ppretty(item, tab_char, return_char, indent + 1)
            for item in value
        ]
        return '[%s]' % (','.join(items) + return_char + tab_char * indent)
    elif type(value) is tuple:
        items = [
            nlch + ppretty(item, tab_char, return_char, indent + 1)
            for item in value
        ]
        return '(%s)' % (','.join(items) + return_char + tab_char * indent)
    else:
        return repr(value)


def set_up(log_name: str):
    global LOG_NAME
    LOG_NAME = f'{LOG_PATH}{log_name[log_name.rfind('\\') + 1:len(log_name) - 3]}.log'

    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    file_handler = logging.handlers.TimedRotatingFileHandler(LOG_NAME, when='midnight', interval=1, backupCount=7,
                                                             encoding=None, delay=True, utc=False, atTime=None,
                                                             errors=None)
    file_handler.namer = lambda name: name.replace(".log", "") + ".log"
    log.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-8s] [%(filename)s.%(funcName)s:%(lineno)d] %(message)s",
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )
