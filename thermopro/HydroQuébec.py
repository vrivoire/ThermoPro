# https://services-cl.solutions.hydroquebec.com/lsw/portail/fr/group/clientele/portrait-de-consommation/resourceObtenirDonneesConsommationHoraires?date=2025-09-24&_=1758820938310
import asyncio
import traceback
from datetime import datetime
from io import StringIO
from queue import Queue
from typing import Any

import pandas
import pandas as pd

import thermopro
from constants import HYDRO_EMAIL, HYDRO_PASSWORD
from hydroqc.contract.common import Contract
from hydroqc.types import ConsumpHourlyTyping
from hydroqc.types.consump import ConsumpHourlyResultTyping, ConsumpHourlyResultsTyping, ConsumpHourlyTyping
from hydroqc.webuser import WebUser
from thermopro import log


class HydroQuébec:

    def __init__(self):
        log.info('              ----------------------- Starting HydroQuébec -----------------------')

    async def __get_kwh_list(self, result_queue: Queue) -> None:
        kwh_list: list[dict[str, Any]] = []
        try:

            webuser = WebUser(HYDRO_EMAIL, HYDRO_PASSWORD, verify_ssl=False, log_level="ERROR", http_log_level="ERROR")
            await webuser.login()
            await webuser.get_info()

            customer = webuser.customers[0]
            await customer.get_info()
            contract: Contract = webuser.customers[0].accounts[0].contracts[0]

            start_date = datetime.now().replace(day=datetime.now().day - 1)
            end_date = datetime.now().replace(day=datetime.now().day + 1)
            log.info(f'start_date: {start_date.strftime('%Y-%m-%d %H:%M:%S')}, end_date: {end_date.strftime('%Y-%m-%d %H:%M:%S')}')
            string: StringIO = await contract.get_hourly_energy(start_date, end_date, raw_output=True)
            df = pd.read_csv(string, sep=';')
            df.set_index('Date et heure')
            df_reversed = df[::-1].reset_index(drop=True)

            pandas.set_option('display.max_columns', None)
            pandas.set_option('display.width', 1000)
            pandas.set_option('display.max_rows', 1000)

            for index, row in df_reversed.iterrows():
                splited = row['Date et heure'].split(' ')
                kwh_list.append({
                    'day': splited[0],
                    'hour': splited[1],
                    'consoTotal': float(row['kWh'].replace(',', '.'))
                })

            today_hourly_consumption: ConsumpHourlyTyping = await contract.get_today_hourly_consumption()
            if today_hourly_consumption.get('success'):
                data: ConsumpHourlyResultsTyping = today_hourly_consumption.get('results')
                date_jour: str = data.get('dateJour')
                liste_donnees_conso_energie_horaire: list[ConsumpHourlyResultTyping] = data.get('listeDonneesConsoEnergieHoraire')
                for data in liste_donnees_conso_energie_horaire:
                    kwh_list.append({
                        'day': date_jour,
                        'hour': data.get('heure'),
                        'consoTotal': data.get('consoTotal'),
                    })
            else:
                log.error('ERROR today_hourly_consumption')
                log.error(f'today_hourly_consumption: {thermopro.ppretty(today_hourly_consumption)}')

            await webuser.close_session()
            log.info(f'kwh_list: {kwh_list[:20]}')
            log.info(f'kwh_list: {kwh_list[len(kwh_list) - 20:]}')
        except Exception as exp:
            log.error(exp)
            log.error(traceback.format_exc())
        finally:
            result_queue.put({'kwh_list': kwh_list})

    def start(self, result_queue: Queue):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.__get_kwh_list(result_queue))
        except BaseException as exp:
            log.error(exp)
            log.error(traceback.format_exc())
        finally:
            loop.close()


if __name__ == "__main__":
    thermopro.set_up(__file__)
    result_queue: Queue = Queue()

    HydroQuébec().start(result_queue)

    while not result_queue.empty():
        print(result_queue.get())
