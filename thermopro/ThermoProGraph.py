# start pyinstaller --onedir ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole

import sys

import thermopro
from thermopro import HOME_PATH, log

sys.path.append(f'{HOME_PATH}/Documents//BkpScripts')

if __name__ == '__main__':
    thermopro.set_up(__file__)

    log.info('ThermoProGraph')
    from thermopro.ThermoProScan import ThermoProScan

    thermoProScan: ThermoProScan = ThermoProScan()
    thermoProScan.create_graph(True)
    log.info('exit')
    sys.exit()
