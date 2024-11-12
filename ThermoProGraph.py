# pyinstaller --onefile ThermoProGraph.py --icon=ThermoPro.jpg --nowindowed --noconsole


from ThermoProScan import ThermoProScan
import matplotlib.pyplot as plt
import sys

if __name__ == '__main__':
    thermoProScan: ThermoProScan = ThermoProScan()
    thermoProScan.create_graph(True)
    plt.show()

    sys.exit()
