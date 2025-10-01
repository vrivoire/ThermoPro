# https://services-cl.solutions.hydroquebec.com/lsw/portail/fr/group/clientele/portrait-de-consommation/resourceObtenirDonneesConsommationHoraires?date=2025-09-24&_=1758820938310
import asyncio
import traceback
from datetime import datetime
from io import StringIO
from queue import Queue

import pandas as pd
from dateutil.relativedelta import relativedelta

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
        webuser: WebUser | None = None
        kwh_dict: dict[str, float] = {}
        try:
            webuser = WebUser(HYDRO_EMAIL, HYDRO_PASSWORD, verify_ssl=False, log_level="ERROR", http_log_level="ERROR")
            await webuser.login()
            log.info(f'Login: {await webuser.login()}')
            await webuser.get_info()

            customer = webuser.customers[0]
            await customer.get_info()
            contract: Contract = webuser.customers[0].accounts[0].contracts[0]

            try:
                start_date = datetime.now() - relativedelta(months=1)
                end_date = datetime.now()
                log.info(f'start_date: {start_date.strftime('%Y-%m-%d %H:%M:%S')}, end_date: {end_date.strftime('%Y-%m-%d %H:%M:%S')}')
                string: StringIO = await contract.get_hourly_energy(start_date, end_date, raw_output=True)
                df = pd.read_csv(string, sep=';')
                log.info('Data parsed')
                df['Date et heure'].astype('datetime64[ns]')
                df.set_index('Date et heure')
                df_reversed = df[::-1].reset_index(drop=True)
                df_reversed['Date et heure'].astype('datetime64[ns]')
                df_reversed.set_index('Date et heure')
                df_reversed = df_reversed.sort_values(by='Date et heure', ascending=True)

                log.info('Creating kwh_dict...')
                for index, row in df_reversed.iterrows():
                    splited = row['Date et heure'].split(' ')
                    kwh: float = 0.0
                    if type(row['kWh']) == str:
                        kwh = float(str(row['kWh']).replace(',', '.'))
                    elif type(row['kWh']) == float:
                        kwh = float(row['kWh'])
                    kwh_dict[f'{splited[0]} {splited[1][0:2]}'] = kwh
            except Exception as ex:
                log.error(ex)
                log.error(traceback.format_exc())

            try:
                today_hourly_consumption: ConsumpHourlyTyping = await contract.get_today_hourly_consumption()
                if today_hourly_consumption.get('success'):
                    data: ConsumpHourlyResultsTyping = today_hourly_consumption.get('results')
                    date_jour: str = data.get('dateJour')
                    liste_donnees_conso_energie_horaire: list[ConsumpHourlyResultTyping] = data.get('listeDonneesConsoEnergieHoraire')
                    for data in liste_donnees_conso_energie_horaire:
                        kwh_dict[f'{date_jour} {data.get('heure')[0:2]}'] = data.get('consoTotal')
                else:
                    log.error('ERROR today_hourly_consumption')
                    log.error(f'today_hourly_consumption: {thermopro.ppretty(today_hourly_consumption)}')
            except Exception as ex:
                log.error(ex)
                log.error(traceback.format_exc())

            kwh_dict = sorted(kwh_dict.items())
            log.info(f'Created kwh_dict, size: {len(kwh_dict)} from: {kwh_dict[0]}, to: {kwh_dict[len(kwh_dict) - 1]}')

        except Exception as exp:
            log.error(exp)
            log.error(traceback.format_exc())
        finally:
            if webuser:
                await webuser.close_session()
                log.info('Session closed')
            data = dict(sorted(kwh_dict))
            result_queue.put({'kwh_dict': data})

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
        data = result_queue.get()
        print(thermopro.ppretty(data))
        print(len(data.get('kwh_dict')))
        # kwh_list: dict = result_queue.get()
        # print(f'size: {len(kwh_list['kwh_list'])}\n{thermopro.ppretty(kwh_list)}')
