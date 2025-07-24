# start pyinstaller --onedir ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole

import sys

import thermopro
from thermopro import log, ppretty
from thermopro.ThermoProScan import ThermoProScan

if __name__ == '__main__':
    thermopro.set_up(__file__)

    log.info('ThermoProGraph')
    thermoProScan: ThermoProScan = ThermoProScan()
    thermoProScan.create_graph(True)
    log.info('exit')
    sys.exit()
