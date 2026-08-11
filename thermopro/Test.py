import thermopro
from thermopro.ThermoProScan import ThermoProScan

temp: float = 23.5
humidity: int = 84

if __name__ == "__main__":
    thermopro.set_up(__file__)
    thermoProScan: ThermoProScan = ThermoProScan()
    humidex = thermoProScan.get_humidex(temp, humidity)
    print(f"{temp}, {humidity}: {humidex}")
