# start pyinstaller --onedir ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole

import sys

import thermopro
from thermopro import log
from thermopro.ThermoProScan import ThermoProScan

if __name__ == '__main__':
    thermopro.LOG_FILE = f'{thermopro.LOG_PATH}{__file__[__file__.rfind('\\') + 1:len(__file__) - 3]}.log'
    thermopro.set_up()

    log.info('ThermoProGraph')
    thermoProScan: ThermoProScan = ThermoProScan()
    thermoProScan.create_graph(True)
    log.info('exit')
    sys.exit()
