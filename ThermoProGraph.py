# pyinstaller --onefile ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole


import sys

import matplotlib.pyplot as plt

from ThermoProScan import ThermoProScan

if __name__ == '__main__':
    thermoProScan: ThermoProScan = ThermoProScan()
    thermoProScan.create_graph(True)
    plt.show()
    sys.exit()
