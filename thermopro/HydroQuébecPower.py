# https://services-cl.solutions.hydroquebec.com/lsw/portail/fr/group/clientele/portrait-de-consommation/resourceObtenirDonneesConsommationHoraires?date=2025-09-24&_=1758820938310
import asyncio
import math
import traceback
from datetime import datetime
from io import StringIO
from queue import Queue

import pandas as pd
from dateutil.relativedelta import relativedelta
from hydroqc.contract.common import Contract
from hydroqc.types.consump import ConsumpHourlyResultTyping, ConsumpHourlyResultsTyping, ConsumpHourlyTyping
from hydroqc.webuser import WebUser

import thermopro
from constants import HYDRO_EMAIL, HYDRO_PASSWORD
from thermopro import log


class HydroQuébec:

    def __init__(self):
        log.info('              ----------------------- Starting HydroQuébec -----------------------')

    async def __get_kwh_list(self,
            result_queue: Queue,
            weeks=4
    ) -> None:
        web_user: WebUser | None = None
        kwh_dict: dict[str, float | None] = {}
        try:
            web_user = WebUser(HYDRO_EMAIL, HYDRO_PASSWORD, verify_ssl=False, log_level="ERROR", http_log_level="ERROR")
            await web_user.login()
            is_logged: bool = await web_user.login()
            log.info(f'Login: {is_logged}')
            log.info(f'check_hq_portal_status: {await web_user.check_hq_portal_status()}')

            if is_logged:
                await web_user.get_info()
                customer = web_user.customers[0]
                await customer.get_info()
                contract: Contract = web_user.customers[0].accounts[0].contracts[0]

                try:
                    log.info('---------------------------- get_hourly_energy ----------------------------')
                    start_date = datetime.now() - relativedelta(weeks=0)
                    end_date = datetime.now() - relativedelta(weeks=weeks)
                    log.info(f'Date range: from: {end_date.strftime('%Y-%m-%d %H:%M')}, to: {start_date.strftime('%Y-%m-%d %H:%M')}')
                    string: StringIO = await contract.get_hourly_energy(start_date, end_date, raw_output=True)
                    df = pd.read_csv(string, sep=';')
                    log.info(f'Data parsed, from: {df.iloc[-1]['Date et heure']}, to: {df.iloc[0]['Date et heure']}, rows: {len(df)}')
                    df['Date et heure'].astype('datetime64[ns]')
                    df.set_index('Date et heure')
                    df_reversed = df[::-1].reset_index(drop=True)
                    df_reversed['Date et heure'].astype('datetime64[ns]')
                    df_reversed.set_index('Date et heure')
                    df_reversed = df_reversed.sort_values(by='Date et heure', ascending=True)

                    log.info('Creating kwh_dict...')
                    for index, row in df_reversed.iterrows():
                        split = row['Date et heure'].split(' ')
                        kwh: float = 0.0
                        if type(row['kWh']) == str:
                            kwh = float(str(row['kWh']).replace(',', '.'))
                        elif type(row['kWh']) == float:
                            kwh = float(row['kWh'])
                        kwh_dict[f'{split[0]} {split[1][0:2]}'] = kwh if not math.isnan(kwh) else 0.0
                except Exception as ex:
                    log.error(ex)
                    log.error(traceback.format_exc())

                try:
                    log.info('---------------------------- get_today_hourly_consumption ----------------------------')
                    today_hourly_consumption: ConsumpHourlyTyping = await contract.get_today_hourly_consumption()
                    if today_hourly_consumption.get('success'):
                        crt: ConsumpHourlyResultsTyping = today_hourly_consumption.get('results')
                        date_jour: str = crt.get('dateJour')
                        liste_donnees_conso_energie_horaire: list[ConsumpHourlyResultTyping] = crt.get('listeDonneesConsoEnergieHoraire')
                        log.info(f'Got liste_donnees_conso_energie_horaire ({len(liste_donnees_conso_energie_horaire)} rows)')
                        for ldceh in liste_donnees_conso_energie_horaire:
                            kwh_dict[f'{date_jour} {ldceh.get('heure')[0:2]}'] = float(ldceh.get('consoTotal') if not math.isnan(ldceh.get('consoTotal')) else 0.0)
                    else:
                        log.error('ERROR today_hourly_consumption')
                        log.error(f'today_hourly_consumption: {thermopro.ppretty(today_hourly_consumption)}')
                except Exception as ex:
                    log.error(ex)
                    log.error(traceback.format_exc())

                kwh_dict = dict(sorted({key: value for key, value in kwh_dict.items() if value != 0.0}.items()))
                log.info(f'Created kwh_dict, size: {len(kwh_dict)} from: {next(iter(kwh_dict))}, to: {next(reversed(kwh_dict.keys()))}')
            else:
                log.error('Not logged in')
        except Exception as exp:
            log.error(exp)
            log.error(traceback.format_exc())
        finally:
            if web_user:
                await web_user.close_session()
                log.info('Session closed')
            result_queue.put({'kwh_dict': kwh_dict})

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
        kwh_list: dict[str, dict[str, float | None]] = result_queue.get()
        print(thermopro.ppretty(kwh_list))
