# start pyinstaller --onedir ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole

import sys

from ThermoProScan import ThermoProScan

if __name__ == '__main__':
    thermoProScan: ThermoProScan = ThermoProScan()
    thermoProScan.create_graph(True)

    sys.exit()
