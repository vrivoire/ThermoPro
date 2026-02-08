import traceback

import pandas as pd

import thermopro
from thermopro import log
from thermopro.constants import SENSORS


class SensorsGraph:
    df: pd.DataFrame

    def __init__(self):
        log.info('Starting ThermoProGraph')
        global df_sensors
        df_sensors = thermopro.load_sensors()
        # self.clean_data()
        thermopro.show_df(df_sensors, title='__init__')

    def create_graph_sensors(self):
        try:
            global df_sensors
            sensor_list: list[str] = []
            for freq in SENSORS:
                for name in SENSORS[freq]['sensors']:
                    for loc in ['ext', 'int']:
                        for tp in ['temp', 'humidity']:
                            sensor_list.append(f'{loc}_{tp}_{name}')
            sensor_list = ['time'] + sorted(sensor_list)

            log.info(thermopro.ppretty(sensor_list))

            for sensor in sensor_list:
                if sensor not in df_sensors.columns:
                    if "_humidity_" in sensor:
                        df_sensors[sensor] = 0
                        df_sensors = df_sensors.astype({sensor: 'int64'})
                    if "_temp_" in sensor:
                        df_sensors[sensor] = 0.0
                        df_sensors = df_sensors.astype({sensor: 'float64'})
                    df_sensors[sensor] = None
                    log.info(f"Column '{sensor}' added.")

            df_sensors = df_sensors[sensor_list]
            thermopro.show_df(df_sensors, title='create_graph_sensors')

        except Exception as ex:
            log.error(ex)
            log.error(traceback.format_exc())


if __name__ == '__main__':
    thermopro.set_up(__file__)
    thermoProGraph: SensorsGraph = SensorsGraph()
    thermoProGraph.create_graph_sensors()
